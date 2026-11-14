---
description: Lit les conversations clients récentes dans Gmail et synchronise Twenty CRM (projets, tâches, notes) et GitHub (issues) avec l'état réel des échanges
argument-hint: "[nb_jours] (défaut: 1) [plan] — ajoute « plan » pour voir le plan de synchro sans rien écrire"
model: opus
allowed-tools: ToolSearch, mcp__claude_ai_Gmail__search_threads, mcp__claude_ai_Gmail__get_thread, mcp__claude_ai_Twenty, mcp__twenty-partikuls, Bash(python3:*), Bash(gh issue list:*), Bash(gh issue view:*), Bash(gh issue create:*), Bash(gh issue comment:*), Bash(gh issue close:*), Bash(gh issue reopen:*), Bash(gh label list:*), Bash(gh repo view:*), Bash(gh search issues:*), Bash(gh auth status:*), Bash(date:*)
---

# /partikuls-crm-sync — Synchroniser Twenty et GitHub avec l'état des conversations clients

**But.** Ma boîte mail est la source de vérité de ce qui se passe avec les clients. Cette commande lit les
conversations récentes et **met Twenty et GitHub au niveau de la réalité** : où en est chaque projet, qui
attend quoi de qui, quelles demandes client doivent devenir du travail. Le « plan du jour » (ce que je dois
faire aujourd'hui) est le *résultat* de cette synchro, pas son objet.

- **Gmail** = lecture des conversations (source). **Jamais le CRM pour chercher les mails.**
- **Twenty** (https://twenty.partikuls.com) = état commercial et relationnel du projet (fiche `project`,
  tâches, notes). C'est le CRM de Partikuls depuis novembre 2026 : **Attio n'est plus utilisé, n'y écris rien.**
- **GitHub** = travail à produire (issues du repo du projet).

**Arguments :** `$ARGUMENTS` → un nombre de jours (défaut **1** = dernières 24 h) et, en option, le mot
`plan` : dans ce cas tu fais toute l'analyse, tu présentes le plan de synchro (§5) et **tu n'écris rien**.

---

## 0. Préparation

- Charge en **un seul** `ToolSearch` les schémas Gmail et Twenty dont tu as besoin
  (requête `select:` avec les noms complets ; pour Twenty : `learn_tools` et `execute_tool`).
- **Comment parler à Twenty.** Le serveur MCP Twenty (connecteur « Twenty », ou `twenty-partikuls` en local)
  n'expose que des méta-outils. Toutes les opérations passent par
  `execute_tool({ toolName, arguments })`. **Avant le premier appel**, fais **un seul** `learn_tools` avec la
  liste complète des outils que tu vas utiliser, pour avoir leurs schémas exacts :
  `find_many_companies`, `find_many_people`, `find_many_projects`, `update_one_project`, `create_one_note`,
  `create_one_note_target`, `find_many_note_targets`, `find_many_notes`, `create_one_task`,
  `create_one_task_target`, `find_many_task_targets`, `find_many_tasks`, `update_one_task`,
  `find_many_workspace_members`. N'appelle **pas** `get_tool_catalog` (inutile : la liste est ici, et la
  réponse est énorme).
  Règles de syntaxe des `find_many_*` : `select` est **obligatoire** (`["*"]` ou une liste de champs) ; les
  filtres sont des clés de premier niveau (`{ "companyId": { "eq": "<id>" } }`,
  `{ "name": { "ilike": "%hanroad%" } }`), jamais dans un objet `filter` ; `limit` ≤ 100 ; si `hasNextPage`
  vaut `true`, pagine avant de conclure qu'un élément est absent.
- Mon identité Twenty : `find_many_workspace_members` → le membre **Khelil** (`id` = assigné des tâches).
  Mon adresse : celle du compte Gmail connecté.
- `gh auth status` : si `gh` n'est pas authentifié, fais la partie Twenty et signale que GitHub est sauté.
- Si Gmail ou Twenty est indisponible : dis-le et arrête-toi (pas de synchro à moitié aveugle). **Ne te
  rabats jamais sur Attio.**

## 1. Lire les conversations (Gmail)

- `search_threads` avec `newer_than:<nb_jours>d -in:draft -category:promotions -category:social`, `pageSize: 50`,
  pagine si besoin. **Inclure les envoyés** : l'état d'une conversation dépend autant de ce que j'ai écrit que de
  ce que j'ai reçu.
- Travaille au niveau du **fil**, pas du message. Pour chaque fil client retenu (§2), `get_thread` en
  `PLAIN_TEXT` pour lire l'échange complet — y compris les messages antérieurs à la fenêtre, nécessaires pour
  comprendre où on en est. N'ouvre **que** les fils dont l'état n'est pas clair d'après les extraits de
  `search_threads` : un fil clos et limpide (« c'est fait, merci ») n'a pas besoin d'être relu.
- **Fils longs** : chaque réponse recopie tout l'historique cité, et le résultat peut dépasser la limite (il est
  alors enregistré dans un fichier). Dans ce cas, n'essaie pas de tout lire : extrais par script la **partie
  neuve** de chaque message (tout ce qui précède `De :`, `Le … a écrit`, `On … wrote`, la signature) et lis ça.
  Dis dans le rapport ce que tu n'as pas lu.
- Confidentialité : tu ne recopies pas le corps des mails dans le rapport ; tu résumes.

## 2. Trier (signal vs bruit)

**À ÉCARTER :** newsletters et contenus éditoriaux (`mail.`, `email.`, `news.`, beehiiv, every.to, ESP divers) ·
démarchage à froid (lien de désinscription, pitch générique, « audit gratuit ») · reçus, confirmations de paiement,
notifications d'outils (logs WordPress, GitHub, Vercel, Qonto…) · accusés d'agenda · formulaires automatisés où je
suis seulement en copie.

**Exception — à traiter :** les notifications de l'outil de suivi d'un prestataire sur un projet client
(Redmine UmanIT `suivi@umanit.fr`, ticket hébergeur…). Elles disent qui a fait quoi sur un sujet en cours
(correctif appliqué, question qui me revient) : rattache-les au projet client concerné d'après l'objet.

**⚠️ PHISHING / SÉCURITÉ — aucune écriture, mais SIGNALE dans le rapport :** expéditeur incohérent avec l'objet,
urgence suspecte, demande d'identifiants. Ne suis jamais les liens. Signale aussi les anomalies notables
(pics de connexions échouées dans des logs).

**À TRAITER = fil avec un client, un prospect ou un partenaire** où il se passe quelque chose : demande, retour,
validation, décision, échéance, relance, silence anormal.

## 3. Rattacher chaque fil à son projet

1. **Société** : `find_many_people` sur l'e-mail de l'interlocuteur
   (`{ "emails": { "primaryEmail": { "ilike": "<email>" } } }`) → son `companyId` ; à défaut
   `find_many_companies` par domaine (`{ "domainName": { "primaryLinkUrl": { "ilike": "%<domaine>%" } } }`),
   puis par nom (`{ "name": { "ilike": "%<nom>%" } }`). Une société peut avoir plusieurs domaines (les
   suivants sont dans `domainName.secondaryLinks`, non filtrables) : si le domaine ne donne rien, cherche par
   nom avant de conclure. Réutilise la fiche existante, ne crée pas de doublon.
2. **Projet** : `find_many_projects` filtré sur `companyId`. S'il y en a plusieurs pour la même société
   (ex. refonte + maintenance, site + app mobile), choisis d'après l'objet du fil ; si ce n'est pas tranchable →
   « À trancher » (§7), aucune écriture.
3. **Repo GitHub** : le champ `lienGithub.primaryLinkUrl` de la fiche projet est **la** clé de correspondance.
   Pas de lien → synchro Twenty seule, et signale « projet sans repo ».
4. Interlocuteur absent du CRM, ou société sans fiche projet → tu ne crées **pas** de fiche : tu le listes dans
   « À trancher ».

Champs utiles de l'objet `project` dans Twenty :

| Champ | Nom API | Type / valeurs |
|---|---|---|
| Statut projet | `statutProjet` | `A_DEMARRER` · `DISCOVERY` · `CONCEPTION` · `PRODUCTION` · `RECETTE` · `MISE_EN_LIGNE` · `MAINTENANCE` · `EN_PAUSE` |
| Santé projet | `santeProjet` | `VERT` · `ORANGE` · `ROUGE` |
| Priorité | `priorite` | `HAUTE` · `MOYENNE` · `BASSE` |
| Facturation | `facturation` | `NON_COMMENCEE` · `ACOMPTE_FACTURE` · `EN_COURS` · `SOLDEE` · `RECURRENT` |
| Prochaine action | `prochaineAction` | texte |
| Date de prochaine échéance | `prochaineEcheance` | date `AAAA-MM-JJ` |
| Date de fin | `dateDeFin` | date |
| Dernier point client | `dernierPointClient` | date |
| Prochain point client | `prochainPointClient` | date |
| Lien GitHub | `lienGithub` | lien `{ primaryLinkUrl }` |
| Société / Deal / Contact principal | `companyId` · `opportunityId` · `contactPrincipalId` | relations |

L'ancien champ texte `statut` est désactivé : utilise **uniquement** `statutProjet`.

## 4. Établir l'état de chaque conversation

Pour chaque fil rattaché, détermine :

- **À qui est la balle ?**
  - **Chez moi** : le dernier message vient du client et attend quelque chose (réponse, devis, correction, livraison, RDV).
  - **Chez le client** : j'ai répondu ou demandé quelque chose ; note depuis combien de jours. Silence **> 7 jours**
    sur une question ouverte → une relance est due.
  - **Close** : échange terminé, rien n'est attendu.
- **Ce qui a changé pour le projet** : décision prise (on continue / on arrête / on met en pause), validation ou
  refus d'un livrable, nouvelle échéance, RDV calé, blocage côté client, facture annoncée ou réglée, tension.
- **Les demandes de travail** : chaque demande concrète du client (bug, modification, contenu à intégrer,
  nouvelle fonctionnalité) = une unité de travail candidate pour GitHub.
- **Les demandes closes** : ce que le client valide ou dont il confirme que c'est réglé.

N'invente rien : une date ou une décision qui n'est pas dans le fil n'existe pas. En cas de doute → « À trancher ».

## 5. Plan de synchro

Avant d'écrire, construis le plan — **une ligne par fil** :

| Client / projet | État de la conversation | Twenty : ce qui change | GitHub : ce qui change | Niveau |
|---|---|---|---|---|

`Niveau` = **auto** ou **à valider** (voir §6). En mode `plan`, présente ce tableau et arrête-toi.
Sinon : exécute les lignes **auto**, puis présente les lignes **à valider** et attends ma réponse.

## 6. Écrire

### 6.1 Twenty — fiche projet (`update_one_project`)

**Auto** (factuel, tiré du fil, réversible) :
- `dernierPointClient` = date du dernier échange réel avec le client (mail ou appel mentionné).
- `prochainPointClient` = date d'un RDV/call **explicitement calé** dans le fil.
- `prochaineAction` = une phrase à l'infinitif, qui dit qui doit faire quoi
  (« Envoyer la facture du palier 80 % », « Attendre les contenus d'Amélie (relance le 05/10) »).
- `prochaineEcheance` = une échéance **écrite** dans le fil.

**À valider** (changent la lecture du projet, je tranche) :
- `statutProjet` (ex. client qui relance un projet arrêté : `EN_PAUSE` → `PRODUCTION` ; recette validée → `MISE_EN_LIGNE`).
- `santeProjet` (silence prolongé, retard côté client, tension, impayé → `ORANGE`/`ROUGE` ; retour à la normale → `VERT`).
- `facturation`, `priorite`, `dateDeFin`.
Pour chacun, donne la valeur actuelle, la valeur proposée et la phrase du fil qui le justifie.

Ne touche **jamais** aux budgets (`budgetVendu`, `budgetConsomme`, `resteAProduire`, `margeEstimee`), aux
liens, ni aux champs que le fil ne documente pas.

**Économie d'appels :** regroupe **tous** les champs d'un même projet dans **un seul** `update_one_project`
(`{ "id": "<projet>", ...champs }`), et ne relis pas la fiche ensuite pour vérifier. Avant d'écrire, dresse
la table `projet → id` à partir du `find_many_projects` et **copie les identifiants depuis cette table** : un
UUID retapé de mémoire finit en « record not found ».

### 6.2 Twenty — journal du projet (note, auto)

Pour chaque fil où **quelque chose a changé**, une note rattachée à la fiche projet :
1. `create_one_note` : `title` = `[sync] AAAA-MM-JJ — <objet du fil>`, `bodyV2` = `{ "markdown": "…" }`,
   3 à 6 lignes — état de la conversation, décisions, échéances, qui a la balle. Résumé, pas de copie du mail.
2. `create_one_note_target` : `{ "noteId": "<id de la note>", "targetProjectId": "<id du projet>" }`.
   **Sans cette étape la note est orpheline** et n'apparaît sur aucune fiche.

Anti-doublon : `find_many_note_targets` filtré sur `targetProjectId` (champ `noteId`), puis
`find_many_notes` sur ces ids, triées par `createdAt` décroissant ; si une note `[sync]` couvre déjà ce fil
**et** que rien de nouveau n'est arrivé depuis, n'en recrée pas.

### 6.3 Twenty — tâches (auto)

- **Balle chez moi** → une tâche : `create_one_task` avec `title` préfixé par le client
  (« SYD — répondre à … », 120 caractères max ; détail éventuel dans `bodyV2.markdown`), `status: "TODO"`,
  `assigneeId` = mon id de membre, `dueAt` seulement si le fil donne une échéance
  (« lundi », « avant le 15 », « à la rentrée » = début septembre ; format ISO, ex. `2026-11-20T09:00:00Z`).
  Pas d'indice → pas de date. Puis `create_one_task_target` pour la lier à la fiche **projet**
  (`targetProjectId`), à défaut au deal (`targetOpportunityId`), puis à la société (`targetCompanyId`).
- **Balle chez le client depuis > 7 jours** → une tâche de relance, échéance = aujourd'hui.
- **Action faite** : si une tâche ouverte correspond à une action que le fil montre accomplie (j'ai envoyé la
  réponse, le devis, la facture ; le client ou le prestataire confirme que c'est réglé), **clôture-la** :
  `update_one_task` avec `status: "DONE"`, plus la ligne de suivi qui dit pourquoi (format ci-dessous).
- **Fait nouveau sur une tâche ouverte → mets-la à jour (auto).** Une tâche n'est pas figée à sa création :
  elle doit dire où en est le sujet **aujourd'hui**. Dès qu'un fil apporte du nouveau sur le sujet d'une tâche
  ouverte (`TODO` / `IN_PROGRESS`) : cause identifiée, action transmise à un tiers (hébergeur, prestataire),
  correctif livré par ce tiers, question qui me revient, nouvelle échéance, précision du client. Dans ce cas,
  fais **un seul** `update_one_task` qui regroupe :
  - `bodyV2` = `{ "markdown": "<corps actuel recopié tel quel>\n\n**JJ/MM** — <ce qui s'est passé> → <ce qui
    reste à faire, et par qui>" }`. C'est un journal **en ajout seul** : ne réécris ni ne supprime jamais les
    lignes existantes (je les modifie parfois à la main). Avant la première ligne de suivi d'une tâche,
    insère un intertitre `**Suivi**`.
  - `title` : à réécrire **seulement** si la prochaine action a changé (« Corriger l'erreur 429 » →
    « Valider le correctif 429 et confirmer à Manon »). Garde le préfixe client et 120 caractères max ;
    recopie l'ancien titre dans la ligne de suivi (`titre initial : …`).
  - `status` : `IN_PROGRESS` dès que le travail a commencé ou qu'il est entre les mains d'un tiers ;
    `DONE` quand le fil montre que c'est fait.
  - `dueAt` : nouvelle échéance **écrite** dans le fil ; sinon n'y touche pas.

  **Pas de redite :** si le corps contient déjà ce fait (runs qui se chevauchent), n'écris rien. Pour
  comparer, prends `title`, `bodyV2`, `status`, `dueAt` dans le `find_many_tasks` de l'anti-doublon
  ci-dessous, sans appel de plus.
  **Miroir GitHub :** toute information qui donne lieu à un commentaire sur une issue (§6.4) met **aussi**
  à jour, dans le même run, la tâche ouverte qui porte sur le même sujet (son corps cite souvent `repo#n`).
  L'issue et la tâche doivent raconter la même histoire.
  *Exemple :* tâche « SOULARD — Corriger l'erreur 429… ». Le 09/11, je trouve la cause (rate limiting nginx)
  et la transmets à UmanIT, qui applique le correctif et me demande de valider. → Titre « SOULARD — Valider
  le correctif 429 d'UmanIT (#74959) et confirmer à Manon », statut `IN_PROGRESS`, une ligne de suivi datée
  du 09/11.

**Anti-doublon obligatoire avant toute création :**
1. Intra-run : plusieurs messages d'un même fil ou d'un même couple (projet + action) = **une** tâche.
2. **Filtre par fiche d'abord — règle dure.** Ne balaie **jamais** toutes mes tâches en premier. Pour chaque
   client concerné, récupère les tâches liées via `find_many_task_targets` (champ `taskId`), dans cet ordre :
   a. la fiche **société** du client (`targetCompanyId` — c'est là que vivent la plupart des tâches historiques) ;
   b. la ou les fiches **projet** de cette société (`targetProjectId`) ;
   c. le **deal** s'il y en a un (`targetOpportunityId`).
   Puis `find_many_tasks` sur ces ids (`{ "id": { "in": [...] } }`, `select` :
   `["id","title","bodyV2","status","dueAt","updatedAt"]`) : tâches **ouvertes** (`TODO`,
   `IN_PROGRESS`) et tâches **terminées** (`DONE`) modifiées sur la fenêtre (une tâche faite ne doit pas
   réapparaître). Un client peut avoir **plusieurs fiches société** (une par marque — ex. NFG Groupe =
   Invisible Estate + Prestige Atlantique) : les personnes et les mails sont souvent rattachés à l'une, le
   projet à l'autre. Interroge les deux.
   Le balayage global de mes tâches ouvertes n'est qu'un **dernier recours**, pour une candidate sans aucune fiche.
3. Comparaison **sémantique** : même action sur le même sujet = doublon, même formulé autrement. Dans le doute, ne recrée pas.
4. Une tâche existante qui couvre le sujet : ne la recrée pas, **mets-la à jour** si le fil apporte du nouveau
   (voir plus haut). Si son échéance est dépassée et que le fil n'en donne pas de nouvelle, signale-la en
   « Déjà suivi » et propose d'actualiser son échéance.

### 6.4 GitHub — issues du repo du projet (`gh`, via `lienGithub`)

**Périmètre :** uniquement les repos de l'organisation **`Partikuls`**. Si `lienGithub` pointe vers le repo d'un
tiers (ex. l'organisation du client), **n'écris rien** : propose l'action dans « À valider ».

Avant toute écriture : `gh issue list --repo <repo> --state all --search "<mots-clés>"` pour retrouver l'issue
existante (ouverte **ou** fermée). Même logique sémantique que pour les tâches.

**Auto :**
- **Nouvelle demande de travail explicite** et sans issue équivalente → `gh issue create` :
  titre à l'impératif/infinitif et autoportant ; corps = le besoin reformulé, les critères de « c'est fait »
  s'ils sont donnés, l'origine (`Demande client — mail du JJ/MM, <prénom>`). Labels **seulement** parmi ceux qui
  existent dans le repo (`gh label list`) : `bug`, `enhancement`, `Change Request`… N'en crée pas.
- **Information nouvelle sur une issue existante** (précision, fichier annoncé, contenu reçu, changement de
  priorité ou de date) → `gh issue comment`, daté, en deux ou trois lignes.

**À valider :**
- **Fermer** une issue parce que le client valide ou confirme que c'est réglé (`gh issue close` avec un commentaire
  qui cite la validation) — et **rouvrir** une issue fermée que le client conteste.
- Demande floue, hors périmètre contractuel ou qui ressemble à un nouveau devis → pas d'issue : « À trancher ».

**Ne va JAMAIS dans GitHub :** montants, factures, impayés, litiges, négociation, contenu contractuel,
coordonnées, reproches. Un repo est un outil de production, lu par des développeurs et parfois par le client :
tout cela reste dans Twenty. Pas de copier-coller de mail dans une issue.

### 6.5 Garde-fous

- Rien de destructif : pas de `delete_*` (tâche, note, cible, fiche), pas d'`update_many_*` ni
  d'`upsert_many_*` ; pas de suppression d'issue.
- Tu ne crées ni `company`, ni `person`, ni repo : tu proposes. Une fiche `project` manquante (repo actif
  sans projet Twenty) se crée **uniquement après mon accord** (`create_one_project`), rattachée à la société
  existante, avec `lienGithub`, `typeDeProjet`, `statutProjet` et `responsable` ; tu ne fusionnes jamais deux
  fiches société.
- **Ce que je te dis prime sur la boîte mail.** Un appel passé, une décision prise à l'oral, un devis envoyé par un
  autre canal : le mode `plan` sert aussi à ça. Intègre mes corrections telles quelles dans Twenty (note `[sync]`
  avec la mention « confirmé par Khelil le JJ/MM ») plutôt que de rester sur ce que montrent les mails.
- Tu n'envoies **aucun mail** et tu ne crées aucun brouillon : cette commande lit Gmail, elle n'y écrit pas.
  (Le MCP Twenty expose aussi `send_email` / `draft_email` : **interdits** ici.)
- Une erreur d'écriture sur un projet n'arrête pas les autres : note-la et continue.

## 7. Rapport (en français, concis)

1. **Plan du jour** — ce que je dois faire aujourd'hui, par priorité : balles chez moi, relances dues, échéances
   proches. Une ligne par action, préfixée par le client.
2. **Synchro effectuée** — tableau : projet | Twenty (champs mis à jour, note, tâches créées / mises à jour / clôturées) |
   GitHub (issues créées `repo#n`, commentées).
3. **À valider** — changements de statut / santé / facturation, fermetures et réouvertures d'issues, écritures
   sur un repo tiers : valeur actuelle → proposée, et la justification tirée du fil. J'exécute après ton accord.
4. **En attente côté client** — projet | ce qu'on attend | depuis combien de jours.
5. **À trancher** — fils non rattachables, projets multiples, demandes floues ou hors périmètre, contacts absents du CRM, projets sans repo.
6. **Déjà suivi** — candidates écartées car une tâche ou une issue équivalente existe (son nom / `repo#n`).
7. **⚠️ Alertes** — phishing probable (expéditeur + objet), anomalies de sécurité.
8. **Bruit écarté** — une ligne par catégorie, avec le nombre.
