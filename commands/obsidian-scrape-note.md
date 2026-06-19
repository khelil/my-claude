---
description: Scrape une URL, traduit en français et dépose une note resource prête à traiter dans le vault
argument-hint: <url> [consignes de traduction optionnelles]
allowed-tools: Bash(firecrawl scrape:*), Bash(mkdir:*), Bash(date:*), Bash(yt-dlp:*), Bash(python3:*), Bash(source:*), Bash(pip:*), Bash(mlx_whisper:*), Bash(rm:*), Read, Write, AskUserQuestion
---

Cette commande prolonge `/scrape-translate` : même récupération et même traduction, mais
la sortie est une **note `resource`** conforme aux conventions du vault
(`CLAUDE.md`, `_meta/taxonomie.md`, `_meta/templates/resource.md`), déposée dans
`resources/` et prête à être traitée plus tard comme n'importe quelle capture.

## Entrée

- URL : **$1**
- Consignes additionnelles : $ARGUMENTS (ignore le premier token = l'URL).

## Procédure

### 1. Récupérer

```bash
mkdir -p .firecrawl
firecrawl scrape "$1" -o .firecrawl/source.md
```

Guillemets obligatoires autour de l'URL. Un seul format (markdown) → pas de JSON.
Si le scrape échoue ou renvoie un contenu vide/tronqué, **arrête-toi** et
signale-le avec l'erreur. N'invente jamais le contenu manquant, ne bascule pas
vers `interact` sans mon accord.

Lis `.firecrawl/source.md`.

### 1bis. Cas particulier : vidéo sans transcript

Pour une vidéo (YouTube…), le scrape Firecrawl renvoie en général une section
`## Transcript`. Si elle est **absente** (seuls le titre, les métadonnées et la
description sont là), le contenu est incomplet : **ne crée pas la note avec la
seule description**. Tente de récupérer le texte parlé dans cet ordre.

**a. Sous-titres existants (yt-dlp).** Vérifie d'abord ce qui est disponible :

```bash
yt-dlp --list-subs "$1"
```

S'il existe des sous-titres (manuels ou auto), télécharge-les et utilise-les
comme transcript :

```bash
yt-dlp --skip-download --write-subs --write-auto-subs \
  --sub-langs "en.*,fr.*" --sub-format vtt -o "/tmp/veille-sub.%(ext)s" "$1"
```

Nettoie le `.vtt` (retire timestamps et balises) pour ne garder que le texte
courant.

**b. Transcription locale (whisper) — uniquement avec mon accord.** Si la sortie
indique `has no subtitles` / `has no automatic captions`, la seule voie est de
transcrire l'audio. Comme ça installe des outils et prend du temps,
**demande-moi d'abord** (via `AskUserQuestion` : transcrire / note description
seule / abandonner). Ne lance rien sans mon accord.

Si j'accepte :

```bash
# 1. extraire l'audio
yt-dlp -x --audio-format mp3 -o "/tmp/veille-audio.%(ext)s" "$1"

# 2. whisper isolé dans un venv (pip est bloqué hors venv par PEP 668)
#    macOS / Apple Silicon : mlx-whisper est rapide
python3 -m venv /tmp/veille-venv
source /tmp/veille-venv/bin/activate && pip install -q mlx-whisper

# 3. transcrire (--language à adapter à la langue de la vidéo)
source /tmp/veille-venv/bin/activate && mlx_whisper /tmp/veille-audio.mp3 \
  --model mlx-community/whisper-large-v3-turbo \
  --language en --output-dir /tmp/veille-out --output-format txt
```

Lis `/tmp/veille-out/veille-audio.txt`. **Ignore les artefacts de fin** (boucles
sur du silence, ex. « Thank you » répété des dizaines de fois). Une fois la note
écrite, nettoie le temporaire :
`rm -rf /tmp/veille-audio.mp3 /tmp/veille-venv /tmp/veille-out`.

**Provenance obligatoire.** Quand le transcript ne provient PAS de Firecrawl,
ajoute en tête de `## Contenu traduit` un encadré `>` précisant la méthode
(sous-titres yt-dlp, ou whisper local + nom du modèle). Pour une transcription
whisper, signale-le aussi dans le compte-rendu final (§4).

### 2. Traduire

Mêmes règles que `/scrape-translate` : traduction **fidèle et idiomatique**, structure
Markdown préservée. **Ne traduis pas** : blocs de code et code inline, URLs,
chemins, noms de commandes/variables/fonctions, noms propres et marques, termes
techniques sans équivalent français usuel. **Traduis** : texte courant, texte
visible des liens (jamais l'URL), légendes, alt-text. Premier terme ambigu :
garde l'anglais entre parenthèses — « inférence (*inference*) ».

### 3. Construire la note resource

**Nom de fichier** : `kebab-case`, descriptif, déduit du titre — **sans accents,
sans espaces, sans majuscules, sans préfixe de date**. Ex :
`extraction-cognitive-ia.md`.

**Anti-écrasement** : si `resources/<slug>.md` existe déjà, n'écrase rien.
Signale le doublon probable et propose soit un suffixe, soit l'abandon. Tu ne
fusionnes pas.

**Tags** : dans le frontmatter, tags **sans `#`** (convention Obsidian — le `#`
ne sert qu'en ligne dans le corps). Mets toujours `type/ref` et
`statut/a-traiter`. Ajoute **un seul** `domaine/*` choisi dans la liste fermée de
`_meta/taxonomie.md` si le sujet est clair ; si tu hésites, n'en mets pas et
signale-le. Tu n'inventes aucun tag.

Écris `resources/<slug>.md` avec cette structure (date via `date +%Y-%m-%d`) :

```markdown
---
type: resource
status: inbox
created: AAAA-MM-JJ
updated: AAAA-MM-JJ
tags: [type/ref, statut/a-traiter]
aliases: []
source: "$1"
---

# <Titre en français>

**Source :** $1
**Récupéré le :** AAAA-MM-JJ

## En une phrase
<une phrase neutre et descriptive : de quoi parle le document. Factuel, pas d'interprétation.>

## Ce que j'en retiens
<!-- VIDE. C'est moi qui écris ici, jamais toi. -->

## Contenu traduit

<la traduction complète, structure Markdown d'origine préservée>
```

### 4. Git & compte-rendu

**Tu ne commit pas** (tu n'as pas accès à git ici, c'est volontaire) : tu laisses
le fichier non indexé pour que je le voie dans `git status`/`git diff` et que je
garde le geste du commit. Per `CLAUDE.md` §9.

Rends compte en deux lignes : chemin du fichier créé, titre, tag `domaine/*`
retenu (ou « aucun, à confirmer »), et tout passage laissé en VO ou doublon
détecté. **Tu ne remplis pas « Ce que j'en retiens » et tu ne résumes pas le
fond** — la synthèse reste mon travail.
