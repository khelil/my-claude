# Refonte de la section Admin — sociétés, utilisateurs, wallets

## Contexte

L'administrateur de l'application (rôle users-permissions `admin`) ne peut pas réellement gérer les sociétés et les utilisateurs. L'analyse a révélé trois familles de problèmes :

1. **Frontend cassé** : 7 des 13 pages admin sont inaccessibles (désynchronisation `dashboardItems.ts` / `navRolePermissions.ts`), la suppression de société existe en service mais n'est jamais affichée, la fiche société est en lecture seule sans action, l'admin voit des pages scopées partner qui ne fonctionnent pas pour lui.
2. **Backend incomplet** : `POST /users` assigne en dur la société et le wallet de l'appelant → un admin ne peut pas créer un utilisateur dans une autre société ; pas de crédit de wallet en delta (seulement un set absolu non validé) ; pas de wallet auto-créé avec une société ; pas de pagination sur `/wallets/admin`.
3. **Failles de sécurité restantes** (non couvertes par la PR #1373 mergée) : `PUT /users/:id` est la route stock Strapi, non scopée, mass-assignable, et accordée au rôle partner ; `company.create/find/findOne/update` accordés au partner sans ownership ; `role.createRole/updateRole/deleteRole` accordés au partner (escalade de privilèges) ; `GET /users/role` renvoie des lignes non sanitisées (`resetPasswordToken`).

**Décisions utilisateur** : les 3 volets sont dans le périmètre ; pas de nouveaux écrans pour invitations/rapports/commandes/abonnements ; about/faq deviennent accessibles à l'admin ; le code mort des suppressions de référentiels est retiré (pas de suppression protégée) ; catégorie de transaction admin = `gift` (déjà dans l'enum, pas de migration).

Branche : `feat/admin-overhaul` depuis `staging`.

---

## Phase 1 — Sécurité (fondation backend)

### C1. Policy `is-admin` réutilisable
**Créer** `backend/src/policies/is-admin.js` : `return policyContext.state.user?.role?.type === 'admin'` (booléen explicite, pas de fallthrough — même esprit que `callerOwnsReport` dans `backend/src/api/report-invitation/controllers/report-invitation.js:132-160`).

Appliquer `policies: ['global::is-admin']` aux routes admin existantes (défense en profondeur, garder les checks inline) :
- `backend/src/api/pool/routes/01-custom-pool-routes.js` (routes `/admin/*`)
- routes logo société (`/admin/companies/:id/upload-logo`, `/admin/companies/:id/logo`)
- routes wallet admin (`/wallets/admin`, `/wallets/:id/admin`)
- route impersonate dans `backend/src/extensions/users-permissions/strapi-server.js` (~:1001-1036)

### C2. Corriger `is-owner.js`
**Modifier** `backend/src/policies/is-owner.js` :
- Branche anonyme `if (!user) return true` → `return false` (vérifié : le rôle Public n'atteint jamais report find/findOne, seuls les tokens de partage passent par `report-invitation.findOneReportInvitationByToken`).
- Garde sur `entry.company?.id` (TypeError actuel si entrée sans société).
- `return false` explicite en fin (le fallthrough `undefined` actuel).

### C3. Override `PUT /users/:id`
**Modifier** `backend/src/extensions/users-permissions/strapi-server.js` — ajouter un override `update` (à côté des overrides GET/POST /users existants), pattern allow-list `EDITABLE_SELF_FIELDS` (:511-536) :
- **Admin** : allow-list `firstName, lastName, email, phone, jobTitle, blocked, deleted, confirmed, role, company` (aligner sur les champs réels du schéma). Valider `role` et `company` contre la DB (réutiliser la validation de rôle du POST /users :379-395). Sur changement de société : re-lier le wallet (retirer du wallet de l'ancienne société, ajouter à celui de la nouvelle — voir la logique d'héritage :444-456).
- **Partner** : la cible doit appartenir à sa société (fetch avec `populate: ['company','role']`, comparaison d'ids, `ctx.forbidden()` sinon). Allow-list restreinte (`firstName, lastName, blocked, deleted` + les champs réellement envoyés par le formulaire collaborateurs — vérifier `frontend/app/(protected)/collaborators/_collaborator-actions.ts`) ; `role` seulement vers `partner`/`subpartner` ; jamais `company`, `confirmed`, `email`.
- Autres rôles : forbidden. Sortie via `sanitizeUser`.
- Les flux UI actuels (block/soft-delete/édition via `frontend/shared/services/user.ts:87,98,114`) restent inchangés.

### C4. Sanitiser `GET /users/role`
**Modifier** `strapi-server.js:697` — passer les lignes par le helper de sanitisation existant (:16) avant retour.

### C5. Retrait des grants partner (manuel + sync)
Révoquer côté rôle partner (via l'admin Strapi, puis re-export sync) :
- `api::company.company.create`, `.find`, `.findOne` (vérifier avant : l'UI partner passe par `/user/me` pour sa société ; garder `.update` — l'onglet société du compte en a besoin, désormais scopé par C6).
- `plugin::users-permissions.role.createRole/updateRole/deleteRole` (garder `role.find/findOne` — utilisés par les selects de rôle).
- `plugin::users-permissions.user.find` (le partner utilise `GET /users/collaborators`) ; ajouter un check admin explicite dans le handler `GET /users` (:838).

### C6. Scoper `company.update` (et sécuriser le reste)
**Modifier** `backend/src/api/company/controllers/company.js` — overrides :
- `update` : admin → toute société, allow-list `name, vatCode, address, phone` ; partner → uniquement sa propre société (via `company.findByUser`), même allow-list.
- `find/findOne/create/delete` : check admin inline (ceinture + bretelles vu le risque de sync stale).
- `delete` : garde-fou — refuser (409) si la société a des users non supprimés, des pools ou des reports (`strapi.db.query(...).count`), message listant les blocages ; si vide, supprimer le wallet orphelin puis la société (Strapi v4 ne cascade pas).

### C7. Re-export config-sync (manuel)
Après tous les changements de grants : `cd backend && npx strapi config-sync export -y`, relire le diff, committer `config/sync/user-role.*.json`. Cela corrige aussi les fichiers stale (actions manquantes : `wallet.findAllWalletsAdmin`, `company.uploadLogo`, `auth.impersonateUser`, etc.). La DB fait foi.

---

## Phase 2 — Endpoints de gestion admin (backend)

Toutes les nouvelles routes : namespace `/admin/*`, `policies: ['global::is-admin']`, grant admin en DB + re-export sync. Précédent : `01-custom-pool-routes.js`.

### B1. Création d'utilisateur dans n'importe quelle société
**Modifier** l'override `POST /users` (`strapi-server.js:364`) : si l'appelant est admin ET que `body.company` est fourni, utiliser cette société (valider l'id) au lieu de celle de l'appelant (:400-407), et attacher le wallet de la société cible (:444-456). Chemin non-admin inchangé. L'email d'invitation Brevo est conservé sans duplication. Pas de nouvelle route.

### B2. Déplacement / changement de rôle
Couvert par l'override C3 (branche admin : changement de société + re-liaison wallet + rôle).

### B3. Wallet auto-provisionné à la création de société
**Créer** `backend/src/api/company/content-types/company/lifecycles.js` avec `afterCreate` : créer un wallet (`balanceCredits: 0`, lien `company`). Lifecycle plutôt qu'override contrôleur pour couvrir aussi les créations via le panel Strapi.

### B4. Crédit en delta
**Ajouter** dans `backend/src/api/wallet/routes/01-custom-wallet-routes.js` : `POST /admin/wallets/:id/credit`.
**Modifier** `backend/src/api/wallet/controllers/wallet.js` — nouveau `creditWalletAdmin` :
- Body allow-list `{ amount, reason }` ; `Number.isInteger(amount)`, `amount !== 0` ; refuser si `balanceCredits + amount < 0`.
- Passer par le service canonique `transfer()` (`backend/src/api/wallet/services/wallet.js:13`), `type` selon le signe, `category: 'gift'`, `userId: ctx.state.user.id`.
- `updateWalletAdmin` (:54) devient validityDate-only (retire le `parseInt` de balance non validé :77).

### B5. Pagination `GET /wallets/admin`
**Modifier** `findAllWalletsAdmin` (:38) : `page`, `pageSize`, `q` (recherche nom de société), retour `{ results, pagination }` au format consommé par `frontend/components/common/List.tsx` (miroir de la liste admin pools).

### B6. Fiche société enrichie
Préférer la réutilisation : `GET /companies/:id?populate[users][populate]=role&populate=wallet` (grants désormais admin-only). Si la sanitisation users-permissions bloque le populate des users, ajouter `GET /admin/companies/:id` retournant `{ company, users (sanitisés), wallet }`.

### B7. Tests backend (Jest)
- `PUT /users/:id` : partner cross-société → 403 ; partner escalade vers admin → 403 ; `company` en mass-assign ignoré pour partner ; admin déplace un user → wallet re-lié.
- `POST /admin/wallets/:id/credit` : non-entier, zéro, sur-débit → 400 ; cas nominal → transaction + balance recalculée.
- Garde-fou delete société : bloqué avec users ; OK si vide.
- `is-owner` : anonyme → 403.

---

## Phase 3 — Frontend

### A1. Réconciliation navigation
**Modifier** `frontend/components/sidebar/dashboardItems.ts` + `navRolePermissions.ts` (filtre : `app/(protected)/layout.tsx:48-66`) :
- Ajouter les items sidebar manquants : countries, states, sectors, subsectors ; réactiver trainings (`dashboardItems.ts:61-66`) dans le bon bucket (corrige le `administration-trainings-page` mort en resourcesSection :180-185).
- Ajouter les grants admin pour about et faq (`superadministration-about-page` :70, `superadministration-faq-page` :75).
- Retirer le grant fantôme `administration-booklets-page` (`navRolePermissions.ts:29`) et `administration-collaborators-page` de l'admin (:28) — l'admin gère les users via /administration/users.
- Renommer les deux sections « Administration » dupliquées (`dashboardItems.ts:197` et `:212`) — ex. « Gestion » (sociétés/users/wallets/pools/packs) vs « Référentiels » + « Mon compte ».
- `/account` : masquer l'onglet société quand `me.company` est absent (`EditCompany.tsx`).

### A2. Fiche société = hub de gestion
**Réécrire** `frontend/app/(protected)/administration/companies/details/CompanyDetails.tsx` :
- Édition : lien/dialog vers `CompanyCreationForm` (déjà dual create/edit).
- Carte wallet : balance + validityDate + bouton crédit/débit ouvrant le modal A5.
- Table des users de la société (via B6) avec block/delete (réutiliser `useChangeStatus`/`useDeleteUser` de `frontend/shared/hooks/mutations/users.ts`) et « Ajouter un utilisateur » ouvrant `UserCreationModal` avec la société présélectionnée et verrouillée.
- Suppression société : `components/common/ConfirmationDialog` + mutation, afficher le message du 409.

### A3. Réparer `useDeleteCompany` + câbler la suppression
**Modifier** `frontend/shared/hooks/queries/companies.ts` : convertir la fausse « hook » (fonction async plate) en vraie `useMutation` invalidant la query key sociétés. Câbler l'action delete déjà importée mais morte dans `CompanyList.tsx` (import `DeleteSharp` inutilisé) avec ConfirmationDialog.

### A4. Écran utilisateurs
- `administration/users/NewUserForm.tsx` / `UserCreationModal` : le select société existe — s'assurer que `_user-actions.ts` envoie `company` (B1 l'honore désormais).
- Édition user : ajouter le select société (admin) → `PUT /users/:id` avec `company` (C3).
- Consolidation : supprimer `collaborators/_collaborator-actions.ts` (copie byte-à-byte de `_user-actions.ts`) et importer le partagé.

### A5. Écran wallets
- **Réécrire** `administration/wallets/WalletList.tsx` sur `components/common/List.tsx` (pagination serveur, ajouter le mapping entity → query key ; dépend de B5).
- Modal crédit : montant signé + motif → nouvelle mutation `useCreditWallet` (service `Wallet.creditWalletAdmin` à ajouter dans `frontend/shared/services/wallet.ts`), invalidation des keys wallet.
- `WalletEditForm.tsx` : retirer le champ balance (delta-only via modal), garder validityDate via `PUT /wallets/:id/admin`, passer par une mutation TanStack au lieu de l'appel direct (:74).

### A6. Édition de pool côté admin
Ajouter l'édition sur `/administration/pools` : réutiliser le formulaire partner `/pools/edit/[id]` — vérifier son scoping société ; si réutilisable, route `administration/pools/edit/[id]` qui l'enveloppe ; vérifier que l'endpoint de mise à jour de pool autorise l'admin cross-société.

### A7. Nettoyage du code mort
Supprimer les blocs de delete commentés : `sectors/SectorsList.tsx:60-85`, `states/StateList.tsx:69-84`, `countries/CountryList.tsx:68-83`, `packs/PackList.tsx:92-107` (décision : pas de suppression protégée des référentiels pour l'instant). Retirer aussi les imports morts de `CompanyList.tsx` rendus vivants par A3.

### A8. Optionnel (en dernier)
Toolbar générique `AdminListToolbar` remplaçant les cinq toolbars quasi identiques (Companies/Users/Wallet/AdminPools/Grid).

### A9. Types
`cd frontend && npm run generate-types` après régénération OpenAPI backend. Les routes custom `/admin/*` n'apparaîtront probablement pas dans l'OpenAPI — garder le pattern `as any` existant pour celles-ci.

---

## Étapes manuelles (utilisateur)

1. Panel Strapi : accorder les nouvelles actions admin (`creditWalletAdmin`, etc.) et révoquer les grants partner (C5).
2. `cd backend && npx strapi config-sync export -y` ; relire + committer `config/sync/user-role.*.json`.
3. Au déploiement staging/prod : vérifier le diff du config-sync import avant application.

## Vérification

- Backend : `cd backend && npm test` (nouvelles suites B7 + existant vert).
- Frontend : `cd frontend && npm run lint && npm run type:check`.
- Script manuel **admin** : login → les 13 entrées de nav visibles et fonctionnelles → créer une société (wallet auto-créé) → ouvrir la fiche → créditer +10 / débiter −5 (transactions visibles, balance via transfer) → sur-débit refusé → créer un user dans cette société (email d'invitation, wallet lié) → déplacer le user vers une autre société (wallet re-lié) → block/unblock, soft-delete → supprimer une société vide OK, société peuplée bloquée (409) → grille wallets paginée → édition de pool OK → page compte sans onglet société.
- Script manuel **partner** : login → collaborateurs list/create/edit/block OK → onglet société du compte édite sa propre société → `PUT /companies/{autreId}` → 403 → `GET /companies` → 403 → `PUT /users/{userAutreSociété}` → 403 → `PUT /users/{sonCollaborateur}` avec `role: <admin>` → 403 → lien de partage de rapport (token report-invitation) fonctionne toujours.

## Décisions actées

- Catégorie de transaction admin : `gift` (déjà dans l'enum `transaction.schema.json`, pas de migration).
- Le partner ne peut pas changer l'email d'un collaborateur (nécessiterait une re-vérification).
- Le partner garde `company.update` scopé à sa propre société (C6).
- About/FAQ : rendus accessibles à l'admin. Référentiels : code mort supprimé, pas de delete protégé.
