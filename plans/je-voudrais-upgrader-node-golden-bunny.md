# Upgrade Node — analyse d'impact

## Context
Le projet est pinné sur Node 20.11.1 (Volta). Node 20 sort de maintenance en avril 2026 : il est déjà EOL. État des releases (août 2026) : Node 22 = Maintenance LTS, **Node 24 = Active LTS** (cible « stable » recommandée), Node 26 = Current (LTS en oct. 2026).

## Constat clé : Strapi 4 bloque tout passage au-delà de Node 20
- `backend/package.json` : `@strapi/strapi` **4.24.0**, dont `engines.node = ">=18.0.0 <=20.x.x"` (propagé sur ~50 packages du lockfile backend et ~23 du lockfile frontend via la devDep `@strapi/strapi ^4.20.2` utilisée pour `generate-types`).
- Strapi v4 ne supporte pas Node 22/24. Strapi 5 supporte Node 22 dès 5.0 et Node 24 à partir de **5.31** (dernière : 5.42.0 d'après `backend/.strapi-updater.json`).
- ⇒ Passer à Node 22/24 impose d'abord une **migration Strapi 4 → 5** (majeure : Document Service API, `documentId`, réponses API aplaties, plugins à réévaluer — `strapi-plugin-config-sync`, `strapi-provider-email-brevo`, `plugin-sentry`, admin customisations, types OpenAPI regénérés côté front, etc.).

Le frontend (Next 14.1.4, react 18.2, sharp 0.33.5, jest 29, playwright 1.47) est compatible Node 22/24 sans changement de code.

## Autres points d'impact (Node 22/24)
- **Deps natives** : `sharp` 0.32.6 transitif via `@strapi/plugin-upload` (pas de prebuild Node 22+, disparaît avec Strapi 5) ; `canvas` 2.11.2 (optionnel, via pdfjs-dist/jsdom, nan-based → risque de build, mais `npm ci` skip si échec — à smoke-tester : rendu react-pdf et tests jsdom). `esbuild`/`@swc/core` OK.
- **npm 11** livré avec Node 24 : `backend/package.json` pinne `engines.npm: "10.2.4"` en exact → à assouplir. Lockfiles v3 OK.
- Code source : aucune API Node dépréciée utilisée (grep clean). Seulement un warning DEP0040 `punycode` transitif.
- **Hors repo** : runtime Node à changer manuellement sur Scaleway (backend) et Vercel (frontend) — aucune config de déploiement dans le repo.

## Fichiers touchés par un bump de version (quel que soit le chemin)
- `package.json` (root) `volta.node`
- `backend/package.json` `volta.node`, `engines.node`, `engines.npm`
- `frontend/package.json` `volta.node` (drifté à 20.11.0), `engines.node/npm`, `volta.yarn` vestigial
- `.github/workflows/release-backend.yml:19`, `release-frontend.yml:20` (`node-version: 20.x`)
- `.github/workflows/type-check-pull-request.yml` lit `node-version-file: package.json` à la **racine** (working-directory ne s'applique pas aux `uses:`) → root doit être à jour
- `frontend/.github/workflows/playwright.yml` : fichier mort (mauvais emplacement), `lts/*`
- `CLAUDE.md:127`
- Dépendabot groupe tous les `@strapi/*` : la migration arrivera en une PR groupée

## Options
**A. Bump immédiat sans risque : Node 20.19.x** (dernier 20). Config-only, ~30 min. Mais Node 20 est EOL → ne règle rien durablement.

**B. Chemin recommandé : migrer Strapi 5 (≥5.31) puis Node 24 LTS.** Deux PRs séparées :
1. Migration Strapi 4→5 (codemods `npx @strapi/upgrade major`, revue des routes custom `01-custom-*`, plugins, config-sync, types front regénérés) — plusieurs jours.
2. Bump Node 24 + npm 11 : fichiers ci-dessus + runtime Scaleway/Vercel.

## Vérification
- `npm ci` root/backend/frontend sans erreur engine ni build natif échoué
- backend : `npm run build`, `npm run dev`, upload S3 (sharp), génération rapport (hyperformula/exceljs)
- frontend : `npm run type:check`, `npm run test`, `npm run build`, `npm run generate-types`, rendu PDF
- CI verte sur les 3 workflows
