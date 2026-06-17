---
description: Scrape une URL avec Firecrawl et traduit le contenu en français
argument-hint: <url> [consignes de traduction optionnelles]
allowed-tools: Bash(firecrawl scrape:*), Bash(mkdir:*), Bash(date:*), Read, Write
---

## Entrée

- URL à traiter : **$1**
- Consignes additionnelles (ton, glossaire, ce qu'il faut garder en VO…) : $ARGUMENTS
  (ignore le premier token, c'est l'URL ; le reste, s'il existe, est une consigne).

## Procédure

### 1. Récupérer le contenu

Crée le dossier de travail si besoin, puis scrape l'URL en Markdown vers un
fichier (jamais directement dans le contexte, pour ne pas le saturer) :

```bash
mkdir -p .firecrawl
firecrawl scrape "$1" -o .firecrawl/source.md
```

- **Toujours** entourer l'URL de guillemets (le shell interprète `?` et `&`).
- Un seul format (`markdown` par défaut) → le fichier contient du Markdown brut.
  Ne passe pas plusieurs formats ici : on ne veut pas de JSON.
- Si le scrape échoue ou renvoie un contenu vide/tronqué (page très dynamique,
  paywall, infinite scroll), **arrête-toi** et signale-le-moi avec le message
  d'erreur. Ne bascule pas vers `interact` sans mon accord, et n'invente jamais
  le contenu manquant.

Lis ensuite `.firecrawl/source.md`.

### 2. Traduire en français

Produis une traduction **fidèle et idiomatique**, pas du mot-à-mot. Règles :

**À préserver tel quel (ne PAS traduire) :**
- La structure Markdown exacte : titres (niveaux), listes, tableaux, citations,
  séparateurs.
- Les blocs de code et le code inline (`` ` ``) — y compris commentaires, sauf si
  une consigne explicite demande de traduire les commentaires.
- Les URLs, chemins de fichiers, noms de commandes, de variables, de fonctions.
- Les noms propres, marques, et termes techniques qui n'ont pas d'équivalent
  français usuel (garde l'anglicisme quand c'est l'usage réel du métier).

**À traduire :**
- Tout le texte courant, en français naturel et fluide.
- Le **texte visible** des liens `[texte](url)` — mais jamais l'URL.
- Les légendes, alt-text d'images, titres de sections.

**Esprit :** vise ce qu'écrirait un rédacteur francophone du domaine, pas une
traduction littérale. En cas de terme ambigu, garde le terme anglais entre
parenthèses à la première occurrence : « inférence (*inference*) ».

### 3. Écrire le résultat

Écris la traduction dans `.firecrawl/traduction.fr.md`, précédée de ce
frontmatter (remplis la date avec la sortie de `date +%Y-%m-%d`) :

```yaml
---
source: "$1"
traduit_le: AAAA-MM-JJ
statut: brouillon-traduction
---
```

### 4. Rendre compte

En une ligne : titre du document, longueur approx., et signale tout passage que
tu as laissé en VO ou sur lequel tu as hésité. **Tu ne réécris pas, tu ne
résumes pas, tu ne « corriges » pas le fond** — tu traduis. Toute synthèse reste
mon travail.
