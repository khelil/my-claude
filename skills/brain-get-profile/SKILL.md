---
name: brain-get-profile
description: Crée ou rafraîchit, dans le vault Brain, la fiche suivie d'une personnalité publique (élu, dirigeant connu, figure médiatique) — essentiel, positionnement, évaluation business / politique / sociale sourcée et notée. Utiliser quand l'utilisateur demande le profil, la fiche ou le suivi d'une personnalité publique, ou tape /brain-get-profile. Pas pour un lead ou un particulier (→ /partikuls-get-profile).
argument-hint: "<Prénom Nom> [précisions — fonction, pays, parti…]"
allowed-tools: Read, Write, Edit, Glob, Grep, Agent, AskUserQuestion, Bash(firecrawl search:*), Bash(firecrawl scrape:*), Bash(python3:*), Bash(date:*), Bash(mkdir:*), Bash(ls:*)
---

Commande **globale** : elle opère toujours sur le vault Obsidian
`/Users/khelil/Library/Mobile Documents/iCloud~md~obsidian/Documents/Brain` (appelé VAULT ci-dessous),
quel que soit le dossier courant. Chemins vault toujours **absolus et entre guillemets** (espaces et `~` dans le chemin).

**Avant tout : lis `VAULT/CLAUDE.md`** (§0, §3, §4, §6quater, §8). Il fait foi.

Fichiers de la commande (dans `~/.claude/skills/brain-get-profile/`) :
- `researcher-brief.md` — gabarit du prompt des chercheurs ;
- `sources.md` — sources prioritaires par pays et par axe ;
- `scripts/profile_tools.py` — `slug` et `verify` (`python3 ~/.claude/skills/brain-get-profile/scripts/profile_tools.py …`).

Format de fiche : `VAULT/_meta/templates/personality.md` (**source unique** — lis-le, ne l'invente pas).

## Entrée

- Personne : premiers mots de **$ARGUMENTS** (le nom).
- Précisions éventuelles (fonction, pays, parti…) : le reste de $ARGUMENTS ; elles servent à lever une ambiguïté.
- `TODAY` = `date +%Y-%m-%d`. `SCRATCH` = le dossier scratchpad de la session ; `PAGES` = `SCRATCH/profile-<slug>-pages/` (crée-le avec `mkdir -p`). **Jamais** `VAULT/.firecrawl/`.

## 0. Garde-fous d'entrée

1. **Désambiguïsation.** `firecrawl search "<nom> <précisions>" --limit 10`. Identifie les personnes réelles derrière les résultats.
   - Plusieurs personnalités publiques plausibles et rien dans les précisions pour trancher → **`AskUserQuestion`** (une option par candidat : nom · fonction · pays). Ne choisis jamais seul.
   - Arrête-toi là si l'utilisateur annule.
2. **Personne publique ?** Il faut au moins une fonction publique, élective ou dirigeante notable, ou une couverture de presse nationale récurrente. Sinon : **stop**, aucune fiche, réponds :
   « Je ne trouve pas de présence publique notable pour <nom> : cette commande est réservée aux personnalités publiques (CLAUDE.md §6quater). Pour un lead ou un contact pro, utilise `/partikuls-get-profile`. »
3. Fixe : `IDENTITE` (une ligne : nom complet · fonction actuelle · pays · un élément distinctif), `PAYS` (ISO-2 : `FR`, `US`, `GB`, `DE`… ou `EU` pour un responsable européen), `COUVERTURE` = `dédiée` si `PAYS` ∈ {FR, US, GB, DE, EU}, sinon `générique` (section `GENERIQUE` de `sources.md`).
4. `SLUG` = `profile_tools.py slug "<nom complet>"`. Fiche = `VAULT/personalities/<SLUG>.md`.

## 1. Mode

- La fiche n'existe pas → **création** (§2 à §4).
- Elle existe → **rafraîchissement** (§5). Lis-la entièrement d'abord.

## 2. Création — trois chercheurs en parallèle

Lis `researcher-brief.md` et `sources.md`. Pour chaque axe `business`, `politique`, `social`, remplis le gabarit :

| Placeholder | Valeur |
|---|---|
| `{{NOM}}` | nom complet |
| `{{IDENTITE}}` | ligne de désambiguïsation |
| `{{PAYS}}` | code pays |
| `{{AXE}}` | l'axe |
| `{{SOURCES}}` | la sous-section `### <axe>` de la section du pays dans `sources.md` |
| `{{PERIODE}}` | `toute` |
| `{{SORTIE}}` | `SCRATCH/profile-<SLUG>-<axe>.md` |
| `{{PAGES}}` | `PAGES` |
| `{{SLUG}}` | `SLUG` |

Lance les **trois `Agent` (`general-purpose`) dans un seul message** pour qu'ils tournent en parallèle. Le prompt de chacun = le gabarit rempli (à partir de « Tu es »).

## 3. Vérification des preuves

```bash
python3 ~/.claude/skills/brain-get-profile/scripts/profile_tools.py verify --pages "PAGES" SCRATCH/profile-<SLUG>-*.md
```

- **Seules les preuves `verified` peuvent entrer dans la fiche.** Les `rejected` (avec leur raison) et les sections `# ÉCHECS` des fichiers ne servent qu'au compte-rendu.
- Si un axe a 0 preuve vérifiée alors que la personne a manifestement une activité sur cet axe, relance **une fois** le chercheur de cet axe avec la liste de ses rejets. Sinon l'axe sera « Non applicable ».
- Les preuves dont l'affirmation commence par `CONTRE: ` alimentent le **contre-argument** de l'axe.

## 4. Rédaction de la fiche

Lis `VAULT/_meta/templates/personality.md` et produis la fiche en **suivant ses sections dans l'ordre, sans en ajouter ni en retirer**.

**Frontmatter :**
- `created` = `updated` = TODAY ;
- `tags` : 1 ou 2 parmi la taxonomie de `VAULT/_meta/taxonomie.md`, en général `domaine/politique` et/ou `domaine/business`. N'en invente aucun ;
- `aliases: ["<Nom avec accents>"]` ;
- `role` = la fonction actuelle courte ;
- `country` = PAYS.

**H1 et bandeau :**
- H1 = nom avec accents.
- Si `COUVERTURE` = `générique`, ajoute sous le bandeau du template : `> ⚠️ Couverture générique : pas de sources dédiées pour ce pays, la fiche s'appuie sur la presse internationale et les registres mondiaux.`

**Preuves :**
- Chaque affirmation de la fiche est appuyée par ≥ 1 preuve vérifiée, affichée ainsi : `affirmation — « citation » [B2](url) *(consulté TODAY)*`.
- Pas de preuve → pas d'affirmation.

**Positionnement :**
- Axes économique et GAL-TAN décrits en mots, sans échelle chiffrée.
- 4 à 6 sujets clés.
- Sans prise de position publique : `Non applicable — aucune prise de position publique repérée (recherche du TODAY)`.

**Évaluation** (Business / Politique / Social) — pour chaque axe :
- **Position** : 1 à 3 phrases descriptives, sans adjectif de jugement moral ;
- **Preuves** : les 2 ou 3 plus fortes ;
- **Contre-argument le plus solide** : tiré des preuves `CONTRE:` ;
- **Confiance** : `élevée` (plusieurs preuves A/B concordantes), `moyenne` (preuves B/C ou partielles), `faible` (preuves C/D isolées ou contradictoires), avec une demi-phrase de justification.

**Autres sections :**
- **Contradictions et revirements** : datés, preuves des deux côtés.
- **Points ouverts** : ce qui manque, échéances connues.
- **`## Ce que j'en retiens`** : laisse le commentaire du template, **n'écris rien**.
- **Voir aussi** : cherche le nom (et ses alias) avec Grep dans `VAULT/wiki/` et `VAULT/notes/`, puis liste les pages pertinentes en `[[liens]]`. Si rien ne sort, laisse la section vide.
- **Journal de suivi** : `- TODAY — création (N sources, M preuves vérifiées, K écartées ; couverture dédiée|générique)`.
- **Sources** : liste dédupliquée des URL utilisées, au format `[éditeur — titre](url) · publié AAAA-MM-JJ · note`.

Écris la fiche avec Write (`mkdir -p "VAULT/personalities"` si besoin).

**Index** (`VAULT/_meta/index.md`) :
- Ajoute la ligne `- [[<SLUG>]] — <role>, fiche suivie (M preuves). · TODAY` dans la section `## Personnalités (\`personalities/\`) — N`. Si la section est absente, crée-la juste avant `## Notes (`.
- Mets à jour son compteur et le total `**N notes**` de l'en-tête.
- Ne touche à rien d'autre dans l'index.

## 5. Rafraîchissement

1. `PIVOT` = le `updated` de la fiche.
   - Si PIVOT = TODAY, demande d'abord avec `AskUserQuestion` s'il faut relancer quand même.
2. **Un seul** chercheur, en remplissant le gabarit ainsi :
   - `{{AXE}}` = `transverse` ;
   - `{{SOURCES}}` = les trois sous-sections du pays ;
   - `{{PERIODE}}` = `depuis PIVOT` ;
   - `{{SORTIE}}` = `SCRATCH/profile-<SLUG>-transverse.md`.
   Ajoute au prompt la liste des URL déjà présentes dans `## Sources`, à ne pas re-rapporter.
3. Vérifie les preuves comme au §3.
4. Édite la fiche avec **Edit uniquement** (jamais Write sur une fiche existante) :
   - **Nouveau fait ou position** → ajout dans la section concernée, avec sa preuve.
   - **Fait ou position de la personne contredit par du neuf** → l'ancien est conservé mais barré : `~~…~~ *(périmé le TODAY — [source](url))*`, le nouveau est ajouté à côté. Le revirement va aussi dans `## Contradictions et revirements`. On **n'efface jamais**.
   - **Évaluation** → tu peux réécrire en place Position, Preuves, Contre-argument et Confiance si les nouvelles preuves l'imposent. Chaque changement d'appréciation est noté au journal : `axe · ancienne → nouvelle — raison [note](url)`.
   - **Interdits** : ne touche jamais à `created`, ni à `## Ce que j'en retiens`, ni aux anciennes lignes du journal.
5. Journal : `- TODAY — rafraîchissement depuis PIVOT (N nouvelles preuves vérifiées, K écartées) : <résumé factuel en une ligne>`.
   - Si rien n'est nouveau : `- TODAY — rafraîchissement depuis PIVOT : aucune nouveauté`, et rien d'autre ne change.
6. `updated` = TODAY. Index : mets à jour la date et le nombre de preuves de la ligne de la fiche.

## 6. Git & compte-rendu

**Pas de commit** : laisse la fiche et l'index modifiés pour que l'utilisateur les voie dans `git status` et garde le geste (CLAUDE.md §6quater).

Compte-rendu court en chat :
- le chemin de la fiche et le mode (création ou rafraîchissement) ;
- les sources consultées, les preuves vérifiées et les preuves écartées, avec les raisons principales ;
- les axes « Non applicable » ;
- la couverture (dédiée ou générique) ;
- les points d'attention : homonymie résolue, sources faibles, échecs de scraping notables.

**Ne résume pas l'évaluation et ne donne pas d'avis** : la lecture et « Ce que j'en retiens » appartiennent à l'utilisateur.
