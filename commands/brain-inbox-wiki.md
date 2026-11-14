---
description: Traite l'inbox du vault Brain et propage les nouvelles sources dans le wiki (ingest « LLM Wiki ») — plan groupé, validation, exécution, index, commit
argument-hint: [fichier ou slug de 00_inbox/ | vide = toute l'inbox]
allowed-tools: Read, Write, Edit, Glob, Grep, Agent, Bash(git:*), Bash(ls:*), Bash(find:*), Bash(grep:*), Bash(date:*), Bash(python3:*), Bash(mkdir:*)
---

Commande **globale** : elle opère toujours sur le vault Obsidian
`/Users/khelil/Library/Mobile Documents/iCloud~md~obsidian/Documents/Brain`,
quel que soit le dossier courant. Tous les chemins ci-dessous sont relatifs à ce vault
(utilise des chemins absolus ou `git -C "<vault>"`).

C'est l'opération **Ingest** du pattern « LLM Wiki » : une capture ne devient pas seulement
une note rangée, elle **met à jour les pages wiki** qu'elle concerne.

**Avant tout : lis `CLAUDE.md` à la racine du vault** (§0, §2, §4, §5, §6, §6bis, §6ter, §8, §9).
Il fait foi ; en cas de divergence avec cette commande, c'est lui qui gagne — et signale-moi l'écart.

## Entrée

- Cible : **$ARGUMENTS** — un fichier ou un slug de `00_inbox/`, ou vide pour toute l'inbox.
- Si l'inbox est vide ou la cible introuvable : dis-le et arrête-toi.

## Phase A — État des lieux (lecture seule)

1. `git status` du vault. **S'il n'est pas propre, montre-moi ce qui traîne et demande** avant
   d'aller plus loin (je range souvent en direct dans Obsidian : ne restaure rien, ne committe
   rien qui ne soit pas à toi).
2. Lis `_meta/index.md` (ton point d'entrée), `_meta/taxonomie.md`, et la liste des pages de `wiki/`.

## Phase B — Plan groupé (lecture seule, rien n'est modifié)

Pour chaque fichier ciblé de `00_inbox/` :

1. Lis-le, déduis `type`.
2. Prépare le frontmatter (§2) : `created` déduit de la date du fichier s'il manque, jamais réécrit.
3. Tags : uniquement ceux de la taxonomie. S'il en manque un, **signale-le, n'invente pas**.
4. Nom cible en `kebab-case` sans accents (§3) et destination (`notes/`, `projects/…`, `areas/…`, `resources/`).
5. 1 à 3 liens suggérés vers des notes existantes (repérées via l'index).
6. Doublon probable ? Signale, **ne fusionne pas**.
7. **Secret** (clé, token, mot de passe, seed phrase) repéré ? Prévois l'extraction vers `_secrets/` (§8).
8. **Si c'est une source (`type: resource`)** — impact wiki :
   - pages `wiki/` existantes que la source alimente (elle en parle *substantiellement*, pas en passant) ;
   - affirmations d'une page wiki que cette source **contredit** ou **périme** (versions, prix, statuts) ;
   - entités/concepts qui atteignent le seuil de **≥ 3 sources** dans le vault et n'ont pas encore de page → page **à créer** (proposition) ;
   - ceux qui passent à 2 sources → simple mention « sous le seuil ».

Présente **un seul tableau** :

| Fichier | Type | Destination / nouveau nom | Tags | Doublon ? | Wiki : pages à mettre à jour | Wiki : pages à créer |

puis, sous le tableau : tags manquants, secrets repérés, contradictions/péremptions détectées.

**Arrête-toi ici et attends ma validation** (« vas-y », « tout », ou ligne par ligne).
Tu ne déplaces rien et tu n'écris rien avant.

## Phase C — Exécution (après validation)

1. **Classement** : frontmatter, mise en forme du corps (titres, listes, retrait du boilerplate —
   c'est maintenant ou jamais, cf. « sources immuables »), section `## Liens suggérés` taguée
   `#statut/a-relier`, extraction des secrets, puis `git mv` vers la destination.
   Commit : `inbox: classement de N captures + frontmatter`.
2. **Propagation wiki** (§6bis) — pour chaque page impactée :
   - **relis la source elle-même** avant d'écrire : aucune affirmation que tu n'as pas vue dans son texte ;
   - ajoute les affirmations dans `## Ce que disent les sources`, chacune terminée par `([[source]])`,
     datée si elle peut vieillir ; factuel uniquement, positions attribuées (« Selon X, … ») ;
   - contradiction → `## Contradictions et points ouverts`, les deux positions, sans trancher ;
     affirmation périmée → marque `⚠️ périmé par [[source]] (date)`, ne l'efface pas ;
   - complète `## Sources` et `## Voir aussi`, rafraîchis `updated` ;
   - mes `notes/` ne sont **jamais** une source : elles ne vont que dans `## Voir aussi`.
   Pages **à créer** : seulement celles que j'ai validées, avec le gabarit `_meta/templates/wiki.md`.
   Pour plus de ~5 sources à relire, délègue la lecture à des sous-agents (une page ou un groupe
   de pages par agent, périmètre d'écriture strict : `wiki/<page>.md` uniquement).
3. **Contrôle** : `python3 ~/.claude/scripts/brain/verify_wiki.py` doit rendre 0 problème
   (toute puce citée, sources existantes dans `resources/`, cohérence avec `## Sources`).
   Corrige jusqu'à ce que ce soit le cas.
4. **Index** (§6ter) : ajoute/actualise dans `_meta/index.md` une ligne par note créée, déplacée
   ou renommée (`- [[note]] — objet factuel de la note, ≤ 140 caractères · updated`), dans la
   bonne section ; actualise le compteur et la date. Pas de montant ni de détail sensible pour `areas/perso/`.
5. Commit : `wiki: ingest de N sources — pages mises à jour : …` (wiki + index ensemble).

## Compte-rendu

Par source : destination, pages wiki touchées (nb d'affirmations ajoutées), contradictions ou
péremptions posées, pages créées. Puis : taille restante de l'inbox, tags manquants à arbitrer.
**Tu ne résumes pas le fond des sources et tu ne conclus pas à ma place.** Jamais de `git push`.

## Interdits (rappel §8)

Écrire dans `wiki/` une affirmation sans source, un avis ou une thèse · toucher au corps d'une
source déjà rangée dans `resources/` · remplir mes sections « Ce que j'en retiens » · inventer un
tag · créer une page wiki non validée · committer un secret.
