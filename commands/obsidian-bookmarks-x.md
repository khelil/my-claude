---
description: Synchronise les derniers bookmarks X (Field Theory CLI) et les dépose dans 00_inbox/
argument-hint: [nombre de bookmarks récents, défaut 20]
allowed-tools: Bash(ft sync:*), Bash(ft list:*), Bash(ft show:*), Bash(ft status:*), Bash(ft path:*), Bash(head:*), Bash(tail:*), Bash(cat:*), Bash(wc:*), Bash(date:*), Bash(mkdir:*), Read, Write
---

Récupère mes bookmarks X récents via le CLI `ft` (Field Theory) et crée **une
note par bookmark** dans `00_inbox/`, conforme aux conventions du vault
(`CLAUDE.md`, `_meta/taxonomie.md`).

- Nombre de bookmarks récents à traiter : **$1** (si vide, prends **20**).

## 0. Pré-vol

Vérifie que l'outil et les données existent avant tout :

```bash
ft status
```

Si `ft` est introuvable, ou si aucun bookmark n'a jamais été synchronisé, ou si
le sync exige une session Chrome connectée à X qui manque → **arrête-toi** et
explique-moi quoi faire (ex. ouvrir Chrome connecté à X, ou lancer `ft auth`).
N'invente aucun bookmark, ne fabrique aucun contenu de substitution.

## 1. Sync (incrémental)

```bash
ft sync
```

Le sync par défaut est **incrémental** : il ne ramène que les nouveautés, c'est
exactement ce qu'on veut pour « les derniers ». **N'utilise pas `--full`**
(crawl complet de tout l'historique) sauf si je le demande explicitement.

## 2. Localiser les données et découvrir le schéma

Les bookmarks bruts sont en JSONL (un par ligne) dans le répertoire de données.
Récupère le chemin plutôt que de le coder en dur :

```bash
ft path
```

Le fichier est `<chemin>/bookmarks.jsonl`. **Avant de parser quoi que ce soit**,
inspecte UNE ligne pour découvrir les vrais noms de champs (id, texte, auteur,
url du tweet, date, média…) — ils ne sont pas garantis, ne les devine pas :

```bash
tail -n 1 "<chemin>/bookmarks.jsonl"
```

Observe les clés réellement présentes et adapte le mapping de l'étape 4. Si le
JSONL est introuvable, rabats-toi sur `ft list` (trié par date) puis
`ft show <id>` pour les détails, en t'adaptant de la même façon au format.

## 3. Sélectionner les N derniers

Le JSONL est cumulatif (tout l'historique). On ne veut que les **$1 plus
récents**. Selon l'ordre constaté du fichier (les nouveaux sont généralement en
fin) :

```bash
tail -n $1 "<chemin>/bookmarks.jsonl"
```

Si tu constates que l'ordre est inverse (récents en tête), utilise `head`.
Vérifie via le champ date découvert à l'étape 2 que tu prends bien les plus
récents, pas les plus anciens.

**Anti-doublon** : pour chaque bookmark, le nom de fichier dérive de son id X
(voir étape 4). Si la note existe déjà dans `00_inbox/`, `notes/`, `resources/`
ou `archive/`, **saute-la** — elle a déjà été capturée/traitée. Tu ne réécris
pas une note existante.

## 4. Écrire une note par bookmark

Pour chaque bookmark retenu, crée `00_inbox/x-<id>.md` où `<id>` est l'identifiant
X du post (garantit l'unicité et l'anti-doublon). `mkdir -p 00_inbox` au besoin.

Frontmatter (tags **sans `#`** dans le YAML ; date du jour via `date +%Y-%m-%d`) :

```markdown
---
type: resource
status: inbox
created: AAAA-MM-JJ
updated: AAAA-MM-JJ
tags: [type/ref, statut/a-traiter]
aliases: []
source: "<url du tweet>"
---

# Bookmark X — @<auteur>

**Auteur :** @<auteur>
**Date du post :** <date du tweet si dispo, sinon "inconnue">
**Lien :** <url du tweet>

## Contenu

<texte intégral du tweet, tel quel — pas de traduction, pas de reformulation>

## Ce que j'en retiens
<!-- VIDE. C'est moi qui écris ici. -->
```

Règles de contenu :
- **Recopie le texte du tweet tel quel.** Tu ne traduis pas, tu ne résumes pas,
  tu ne corriges pas. (Si je veux une traduction, j'enchaînerai avec `/obsidian-scrape-note`
  ou je te le demanderai.)
- **N'ajoute aucun tag de domaine.** Le classement par domaine se fait au
  traitement de l'inbox, pas ici — laisse `type/ref` + `statut/a-traiter`.
- Si un champ manque (auteur, date), écris « inconnu(e) » plutôt que d'inventer.
- Ne télécharge pas les médias (pas de `ft fetch-media` ici) sauf demande.

## 5. Git & compte-rendu

**Tu ne commit pas** (pas d'accès git dans cette commande, volontairement) :
laisse les fichiers non indexés pour que je les relise dans `git status` avant de
les intégrer. Per `CLAUDE.md` §9.

Rends compte brièvement : combien de notes créées, combien sautées (doublons),
le chemin de données utilisé, et tout champ manquant ou anomalie de format
rencontrée. Tu listes, tu n'interprètes pas le fond.
