---
name: strudel-composer
description: Compositeur de musique électronique hypnotique et techno mentale avec Strudel (TidalCycles pour le web). Utiliser quand l'utilisateur veut créer de la musique électronique, des patterns rythmiques, de la techno, de l'ambient, ou du live coding musical. Ce skill fournit la théorie musicale, les techniques de composition hypnotique, et la documentation Strudel pour générer du code prêt à jouer sur strudel.cc
---

# Strudel Composer - Techno Mentale & Hypnotique

Ce skill permet de composer de la musique électronique hypnotique, de la techno mentale profonde et planante en utilisant Strudel, l'environnement de live coding musical basé sur TidalCycles.

## Workflow de composition

1. **Analyser la demande** : Identifier le mood, le tempo (BPM), et le style souhaité
2. **Concevoir la structure** : Définir les layers (kick, bass, hats, pads, leads, fx)
3. **Appliquer la théorie musicale** : Choisir gamme, accords, progressions adaptés au style hypnotique
4. **Coder en Strudel** : Générer le code prêt à copier-coller sur strudel.cc
5. **Proposer des variations** : Offrir des modifications pour évoluer le morceau

## Références essentielles

- **Syntaxe Strudel** : Voir `references/strudel-syntax.md` pour la mini-notation et les fonctions
- **Théorie musicale techno** : Voir `references/music-theory.md` pour gammes, accords et progressions hypnotiques
- **Patterns hypnotiques** : Voir `references/hypnotic-patterns.md` pour les techniques de composition

## Principes de la techno hypnotique

### Caractéristiques sonores
- **Tempo** : 120-135 BPM (sweet spot : 125-128 BPM)
- **Kick** : Lourd, long decay, souvent sidechainé
- **Bass** : Profonde, minimaliste, souvent une seule note répétée avec variations subtiles
- **Hi-hats** : Patterns polyrythmiques, évolution lente
- **Pads/Atmosphères** : Nappes évolutives, drones, textures granulaires
- **Leads** : Séquences répétitives avec micro-variations, arpèges hypnotiques

### Techniques de transe
- **Répétition avec micro-évolution** : Même pattern avec changements subtils sur 16-32 cycles
- **Polymetrie** : Superposition de patterns de longueurs différentes (3 sur 4, 5 sur 8)
- **Filtrage dynamique** : LPF qui évolue lentement (slow(8) à slow(32))
- **Delay/Reverb** : Espacialisation profonde, feedback contrôlé
- **Silence stratégique** : Drops, breaks, espaces respiratoires

## Structure de code Strudel typique

```javascript
// Configuration
setcps(128/60/4) // 128 BPM

// Drums
$: s("bd*4").gain(1)
$: s("~ sd ~ sd").gain(0.8)
$: s("hh*8").gain(0.4).pan(sine.slow(4))

// Bass
$: note("c1*4").s("sawtooth").lpf(200).gain(0.7)

// Atmosphère
$: note("<c3 eb3 g3>").s("pad").room(0.8).slow(4)
```

## Règles de génération

1. **Toujours inclure `setcps()`** pour définir le tempo
2. **Utiliser `$:`** pour chaque pattern parallèle
3. **Commenter** chaque section (// Kick, // Bass, etc.)
4. **Appliquer des effets** (lpf, delay, room) pour la profondeur
5. **Utiliser slow()** pour les évolutions lentes caractéristiques de l'hypnotique
6. **Privilégier les gammes mineures** : C minor, D minor, A minor pour l'atmosphère sombre

## Output attendu

Générer un fichier .md avec du code Strudel complet et fonctionnel, prêt à être copié sur https://strudel.cc, avec :
- Commentaires explicatifs en français
- Structure claire par sections
- Variations suggérées en commentaires
- Tempo et tonalité indiqués
