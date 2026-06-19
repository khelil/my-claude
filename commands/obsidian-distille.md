---
description: Prépare la distillation d'une capture (affirmations clés + pistes de liens), sans écrire la synthèse à ma place
argument-hint: <chemin-ou-slug de la capture | "inbox" pour toutes>
allowed-tools: Read, Write, Edit, Bash(grep:*), Bash(ls:*), Bash(date:*)
---

Cette commande prépare l'**échafaudage de distillation** d'une capture brute
(typiquement une note `resource`/`inbox` issue de `/obsidian-scrape-note` ou des bookmarks).
Elle prolonge la philosophie du vault (`CLAUDE.md` §0) : **je prépare la matière,
tu écris la pensée.** Je ne remplis JAMAIS « Ce que j'en retiens ».

## Entrée

- Cible : **$1** — un chemin (`00_inbox/x.md`), un slug (`x`), ou le mot `inbox`
  pour traiter toutes les captures `#statut/a-traiter` de `00_inbox/`.

## Procédure

Pour chaque capture visée :

### 1. Lire et localiser
Lis la capture. Si `$1` est un slug, retrouve le fichier dans `00_inbox/` puis
`resources/`. Si la cible n'existe pas, **arrête-toi** et signale-le ; n'invente
rien.

### 2. Extraire les affirmations clés (factuel, pas d'interprétation)
Ajoute (ou complète) une section `## Affirmations clés` : **2 à 4 puces**
strictement **descriptives**, reformulant ce que dit la source — pas ce que j'en
pense. Pas d'adjectif d'opinion, pas de conclusion. Si la source est en langue
étrangère, les puces sont en français (mêmes règles de non-traduction que
`/obsidian-scrape-note` : code, noms propres, marques, URLs restent en VO).

### 3. Proposer des pistes de liens
Cherche dans le vault (`grep`/`ls` sur `notes`, `projects`, `areas`, `resources`)
1 à 3 notes existantes réellement reliées au sujet. Ajoute-les dans une section
`## Liens suggérés` taguée `#statut/a-relier`. **Tu ne fabriques pas de lien dans
le corps** : ils restent en suggestion tant que je n'ai pas dit « relie » (§5,
§7bis). N'invente pas de cible : si aucune note pertinente n'existe, écris
« aucune piste évidente ».

### 4. Réserver la place de ma synthèse
Garantis la présence d'une section `## Ce que j'en retiens` **laissée vide**, avec
le commentaire `<!-- VIDE. C'est moi qui écris ici, jamais toi. -->`. Si elle
existe déjà et contient du texte, **n'y touche pas**.

### 5. Frontmatter
Rafraîchis `updated` (via `date +%Y-%m-%d`). Ne touche jamais à `created`.
Laisse `status: inbox` et le tag `#statut/a-traiter` : la capture n'est
« traitée » que lorsque MOI j'ai écrit la synthèse et retiré le drapeau.

### 6. Compte-rendu
En deux lignes par capture : chemin, nb d'affirmations extraites, pistes de liens
retenues (ou « aucune »). **Tu ne résumes pas le fond, tu ne conclus pas.** Tu ne
commits pas — tu me laisses voir le diff.
