---
description: Traite en lot tous les liens de 00_inbox/links_to_parse.md via la procédure /obsidian-scrape-note, puis retire du fichier ceux traités
argument-hint: [chemin de fichier alternatif, défaut 00_inbox/links_to_parse.md]
allowed-tools: Bash(firecrawl scrape:*), Bash(mkdir:*), Bash(date:*), Bash(yt-dlp:*), Bash(python3:*), Bash(source:*), Bash(pip:*), Bash(mlx_whisper:*), Bash(rm:*), Bash(wc:*), Read, Write, AskUserQuestion
---

Traite **en lot** une liste de liens déposés dans un fichier « boîte de dépôt »,
en appliquant à chacun la procédure de `/obsidian-scrape-note` (scrape/transcript → traduction →
note `resource` dans `resources/`), puis **nettoie le fichier** pour ne pas
retraiter les mêmes liens au prochain lancement.

- Fichier à traiter : **$1** si fourni, sinon **`00_inbox/links_to_parse.md`**.

`/obsidian-scrape-note` (`.claude/commands/obsidian-scrape-note.md`) reste la **source de vérité** pour le
traitement d'un lien individuel (récupération, cas vidéo sans transcript,
traduction fidèle, structure exacte de la note, anti-écrasement). Cette commande
ne fait qu'**orchestrer le lot** et **entretenir le fichier**. En cas de doute
sur le traitement d'un lien, relis `obsidian-scrape-note.md`.

## 0. Pré-vol

Lis le fichier cible. S'il n'existe pas ou est vide (hors lignes blanches /
commentaires), **arrête-toi** et dis-le simplement — il n'y a rien à traiter.

Extrais la liste des **URLs** : une URL par ligne. **Ignore** les lignes
blanches, les lignes de commentaire (`#…`, `<!--…-->`, `//…`) et tout texte après
l'URL sur une même ligne (ex. un `<!-- échec: … -->` laissé par un run
précédent — l'URL reste à retraiter, le commentaire non). **Dédoublonne** la
liste. Présente-moi le nombre de liens trouvés et la liste avant de lancer.

**Anti-doublon vault** : pour chaque URL, si une note `resource` portant ce même
`source:` existe déjà dans `resources/` (ou `archive/`), considère le lien comme
**déjà traité** → tu le marqueras « sauté (doublon) » et tu le retireras du
fichier sans le retraiter. Tu ne réécris jamais une note existante.

## 1. Politique whisper (une seule fois pour tout le lot)

Pour les vidéos sans sous-titres, `/obsidian-scrape-note` impose mon accord avant une
transcription whisper locale (installe des outils, lent). En lot, ne me le
demande pas vidéo par vidéo : **vérifie d'abord** quels liens en auraient besoin
(rappel `/obsidian-scrape-note §1bis` : Firecrawl sans `## Transcript`, puis `yt-dlp
--list-subs` → `has no subtitles` / `has no automatic captions`).

- Si **aucun** lien ne nécessite whisper (sous-titres dispos partout, ou pages
  web classiques) → n'ouvre aucune question, enchaîne.
- Si **au moins un** lien le nécessiterait → pose **une seule** `AskUserQuestion`
  pour tout le lot : *Transcrire tous ceux qui en ont besoin* / *Les sauter
  (garder le lien pour plus tard)* / *Abandonner le lot*. Applique ma réponse à
  tous les liens concernés. Un lien « sauté » faute de whisper reste dans le
  fichier (cf. §3), il n'est pas perdu.

## 2. Traiter chaque lien (procédure /obsidian-scrape-note)

Pour chaque URL retenue, applique **intégralement** la procédure de `/obsidian-scrape-note` :

1. **Récupérer** : `firecrawl scrape "<url>" -o .firecrawl/source.md` (guillemets
   obligatoires). Cas vidéo sans transcript → sous-titres `yt-dlp` (en/fr), ou
   whisper **selon la politique décidée en §1**. Provenance obligatoire dans la
   note quand le transcript ne vient pas de Firecrawl (encadré `>` en tête de
   `## Contenu traduit`).
2. **Traduire** fidèlement et idiomatiquement en français (mêmes règles que
   `/scrape-translate` : on ne traduit pas code, URLs, chemins, noms propres, marques,
   termes techniques sans équivalent ; on traduit le texte courant).
3. **Écrire** `resources/<slug>.md` — slug `kebab-case` sans accents/espaces/
   majuscules/date, déduit du titre. Frontmatter et structure **exactement** comme
   dans `/obsidian-scrape-note §3` (`type: resource`, `status: inbox`, `tags: [type/ref,
   statut/a-traiter]` + **un seul** `domaine/*` de `_meta/taxonomie.md` si le sujet
   est clair, sinon aucun ; `source: "<url>"` ; sections `## En une phrase`,
   `## Ce que j'en retiens` **VIDE**, `## Contenu traduit`).
   **Anti-écrasement** : si `resources/<slug>.md` existe déjà, n'écrase pas —
   marque le lien « sauté (doublon) » et passe au suivant.

Le contenu des liens étant indépendant, tu **peux** déléguer la traduction de
plusieurs liens à des sous-agents en parallèle (un par lien) pour aller plus
vite ; chaque sous-agent écrit sa propre note selon la structure ci-dessus. À
défaut, traite-les en séquence (le scratch `.firecrawl/source.md` est partagé,
donc en séquentiel un lien à la fois).

**Frontière sacrée (`CLAUDE.md §0`)** : tu remplis « En une phrase » (factuel),
tu laisses « Ce que j'en retiens » **vide**. Tu ne résumes pas le fond.

## 3. Nettoyer le fichier de liens

Une fois le lot traité, **réécris** le fichier cible pour ne pas refaire le
travail :

- **Retire** toute URL **traitée avec succès** (note créée) **ou sautée comme
  doublon** (déjà dans le vault) — ce sont des liens « faits ».
- **Conserve** toute URL **en échec** (scrape vide/tronqué, erreur) ou **sautée
  faute de whisper**, chacune sur sa ligne, suivie d'un bref commentaire
  `<!-- échec: <raison courte> -->` (ou `<!-- sauté: whisper refusé -->`). Ainsi
  elles seront représentées au prochain lancement, et tu gardes la trace du
  pourquoi. Le parseur de §0 réignore ces commentaires.
- Si **tous** les liens sont faits, laisse le fichier avec une seule ligne :
  `<!-- Boîte de dépôt : colle ici une URL par ligne, puis lance /parse-links. -->`
  (ne supprime pas le fichier — c'est une boîte de dépôt réutilisable).

Écris le fichier via l'outil Write. **Tu ne commit pas** (per `CLAUDE.md §9`) :
laisse les notes créées et le fichier modifié non indexés pour que je les relise
dans `git status` / `git diff` avant de committer.

## 4. Compte-rendu

Rends compte en un tableau : pour chaque lien → **statut** (créé / sauté doublon
/ échec / sauté whisper), **note** (chemin `resources/<slug>.md` ou —), `domaine/*`
retenu (ou « aucun »). Termine par : combien de liens restent dans le fichier et
pourquoi, et tout passage notable laissé en VO. **Tu ne remplis pas « Ce que j'en
retiens » et tu ne résumes pas le fond** — la synthèse reste mon travail.
