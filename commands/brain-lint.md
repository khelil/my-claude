---
description: Lint du savoir du vault Brain — contradictions, affirmations périmées, concepts sans page, santé du wiki et de l'index, liens cassés, orphelines ; produit un rapport dans _meta/
argument-hint: [tout (défaut) | structure | wiki]
allowed-tools: Read, Write, Edit, Glob, Grep, Agent, Bash(git:*), Bash(ls:*), Bash(find:*), Bash(grep:*), Bash(date:*), Bash(python3:*)
---

Commande **globale** : elle opère toujours sur le vault Obsidian
`/Users/khelil/Library/Mobile Documents/iCloud~md~obsidian/Documents/Brain`,
quel que soit le dossier courant. Tous les chemins ci-dessous sont relatifs à ce vault.

C'est l'opération **Lint** du pattern « LLM Wiki » (CLAUDE.md §7). Le lint **signale** :
c'est un rapport, pas une synthèse. Tu listes, tu ne conclus pas à ma place.

**Avant tout : lis `CLAUDE.md` à la racine du vault** (§0, §6bis, §6ter, §7, §8). Il fait foi.

## Portée — **$ARGUMENTS**

- `structure` : partie 1 seulement (rapide, mécanique).
- `wiki` : parties 2 et 3 seulement.
- vide ou `tout` : tout.

## 1. Lint mécanique

Lance `python3 ~/.claude/scripts/brain/lint_structure.py` et reprends sa sortie :
liens cassés, pièces jointes introuvables, orphelines (l'index et les rapports de `_meta/` ne
comptent pas comme liens entrants), tags hors taxonomie, frontmatter incomplet, `resources/`
sans champ `source`, dérive de l'index (notes absentes / entrées mortes), compteurs
(inbox, liens suggérés en attente, captures `#statut/a-traiter`).

Ajoute : notes `status: active` de `projects/` et `areas/` sans `updated` depuis > 14 jours.
Reprends aussi la section `PERSONNALITÉS NON RAFRAÎCHIES (> 90 j)` : fiches `personalities/` à relancer avec `/brain-get-profile` (les fiches ne comptent pas comme orphelines).

## 2. Santé du wiki

1. `python3 ~/.claude/scripts/brain/verify_wiki.py` : toute puce citée, sources existantes,
   cohérence avec `## Sources`. Liste les problèmes.
2. Pages wiki dont une source a été **supprimée, renommée ou déplacée hors de `resources/`**.
3. **Sondage de fidélité** : tire ~8 affirmations chiffrées ou datées réparties sur plusieurs
   pages, et vérifie chacune **dans le texte de la source citée**. Rapporte n/8 et détaille tout écart.
4. Sources de `resources/` plus récentes que le `updated` d'une page wiki qui devrait les citer
   (source rangée mais jamais propagée).

## 3. Lint du savoir

Appuie-toi sur `_meta/index.md` et les pages `wiki/`, et rouvre les sources quand il faut trancher un doute de lecture.

Les fiches `personalities/` sont l'**analyse de Claude** (CLAUDE.md §6quater) : **jamais** une source factuelle — ne les traite pas comme des sources, ne les compte pas dans les « ≥ 3 sources », ne propage rien d'elles vers le wiki.

- **Contradictions** entre sources, ou entre une source et une page wiki : relève celles des
  sections `## Contradictions et points ouverts`, et cherche celles qui n'y sont pas encore.
- **Affirmations périmées** par une source plus récente (versions de modèles, prix, statuts
  beta/preview, chiffres) — y compris dans mes fichiers de `_meta/` qui recopient des faits.
- **Affirmations à source unique** ou de fiabilité signalée (fuite, transcription automatique, chiffre incohérent dans la source).
- **Concepts/entités cités dans ≥ 3 sources sans page wiki** → candidats (proposition, pas création).
  Mentionne ceux à 2 sources.
- **Trous de connaissance** : sources non datées, débats où le vault n'a qu'un seul bord,
  questions laissées ouvertes par les sources, sources qu'il vaudrait la peine d'aller chercher.
  Tu peux suggérer des pistes ; tu ne vas pas les chercher sans que je le demande.

Pour plus de ~10 sources à rouvrir, délègue à des sous-agents **en lecture seule**.

## 4. Rapport

Écris `_meta/YYYY-Www-lint.md` (semaine ISO via `date +%G-W%V` ; si le fichier existe déjà cette
semaine, mets-le à jour) avec le frontmatter standard (`type: note`, `status: active`) et les
sections : Contradictions · Affirmations périmées · Source unique / fiabilité · Concepts sans
page · Santé du wiki et de l'index · Trous de connaissance · Structure.
Compare au lint précédent de `_meta/` s'il existe : orphelines, liens cassés, inbox — en hausse ou en baisse.

## 5. Corrections

**Autonome (§8)** — fais-le, puis liste-le dans le rapport :
- dans `wiki/` : marquer une affirmation `⚠️ périmé par [[source]] (date)`, ajouter une
  contradiction repérée, retargeter une source renommée, corriger un écart de fidélité
  en relisant la source ;
- dans `_meta/index.md` : ajouter les notes absentes, retirer les entrées mortes ;
- frontmatter incomplet, lien cassé vers une cible **évidente**.

**À me proposer, sans exécuter** : créer une page wiki, supprimer/fusionner quoi que ce soit,
retirer un lien cassé sans cible, toucher au fond d'une de mes notes, étendre la taxonomie.

**Jamais** : modifier le corps d'une source de `resources/`, trancher une contradiction, écrire un avis.

## 6. Commit et compte-rendu

`git status` d'abord : ne committe que tes fichiers, chemin par chemin, si l'arbre contient
des changements qui ne sont pas à toi. Commit : `meta: lint du savoir YYYY-Www` (rapport, index,
corrections wiki). Jamais de `git push`.

Compte-rendu en chat, court : les chiffres clés et leur évolution, les corrections faites,
et **la liste numérotée de ce qui attend ma décision**.
