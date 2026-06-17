# Théorie Musicale pour Techno Hypnotique

## Gammes recommandées

### Gammes mineures (essentielles)
Les gammes mineures créent l'atmosphère sombre et introspective de la techno mentale.

| Gamme | Notes | Caractère |
|-------|-------|-----------|
| **C minor** | C Eb F G Ab Bb | Standard, polyvalent |
| **D minor** | D F G A Bb C | Très utilisé, mélancolique |
| **A minor** | A C D E F G | Naturel, accessible |
| **E minor** | E G A B C D | Profond, mystique |
| **F minor** | F Ab Bb C Db Eb | Sombre, dramatique |

### Gammes modales (atmosphères spécifiques)

| Mode | Caractère | Utilisation |
|------|-----------|-------------|
| **Dorien** | Mineur mais lumineux | Grooves hypnotiques optimistes |
| **Phrygien** | Très sombre, oriental | Techno dark, tribal |
| **Locrien** | Tendu, instable | Montées, tension extrême |
| **Éolien** | Mineur naturel | Base de la techno classique |

### Notes de basse recommandées par tonalité

```
C minor : C, G, F, Eb (fondamentale, quinte, quarte, tierce mineure)
D minor : D, A, G, F
A minor : A, E, D, C
```

## Progressions d'accords hypnotiques

### Progression minimaliste (1 accord)
La techno hypnotique utilise souvent un seul accord ou drone :
```javascript
// Drone en C mineur
note("[c2,eb2,g2]").s("pad").slow(8)
```

### Progression à 2 accords
```javascript
// i - VII (mineur classique)
"<[c3,eb3,g3] [bb2,d3,f3]>"  // Cm - Bb

// i - iv
"<[c3,eb3,g3] [f3,ab3,c4]>"  // Cm - Fm
```

### Progression à 4 accords
```javascript
// i - VI - III - VII (progression épique)
"<[c3,eb3,g3] [ab2,c3,eb3] [eb3,g3,bb3] [bb2,d3,f3]>"
// Cm - Ab - Eb - Bb
```

## Intervalles pour mélodies hypnotiques

### Intervalles recommandés
- **Seconde mineure (1 demi-ton)** : Tension, dissonance contrôlée
- **Tierce mineure (3 demi-tons)** : Mélancolie, profondeur
- **Quarte juste (5 demi-tons)** : Stabilité, ouverture
- **Quinte juste (7 demi-tons)** : Puissance, ancrage
- **Octave (12 demi-tons)** : Expansion, clarté

### Mélodies hypnotiques typiques
```javascript
// Arpège mineur simple (très efficace)
note("c3 eb3 g3 eb3")

// Pattern hypnotique avec quarte
note("c3 f3 eb3 c3")

// Montée chromatique subtile
note("c3 c#3 d3 c3")
```

## Rythmes et time signatures

### BPM par sous-genre

| Style | BPM | Caractéristiques |
|-------|-----|------------------|
| Deep Techno | 118-124 | Lent, hypnotique, groovy |
| Hypnotic Techno | 124-130 | Transe, répétitif, évolutif |
| Mental Techno | 128-134 | Complexe, polyrythmique |
| Hard Techno | 140-150 | Rapide, percussif |
| Ambient Techno | 90-120 | Atmosphérique, flottant |

### Signatures rythmiques

**4/4 standard** (la base)
```javascript
$: s("bd*4")           // Kick on the beat
$: s("~ sd ~ sd")      // Snare sur 2 et 4
$: s("hh*8")           // Hi-hat en croches
```

**Patterns euclidiens classiques**
```javascript
"bd(3,8)"    // Tresillo (Afro-Cuban)
"bd(5,8)"    // Cinquillo
"hh(7,16)"   // Pattern complexe
"sd(2,8,1)"  // Backbeat décalé
```

## Techniques de composition hypnotique

### 1. Répétition avec micro-variations
```javascript
// Pattern de base
$: note("c2 c2 c2 <c2 eb2>").s("sawtooth").lpf(400)
// Le 4ème temps varie entre c2 et eb2
```

### 2. Filtrage évolutif
```javascript
// Sweep de filtre sur 16 cycles
.lpf(sine.range(200, 4000).slow(16))
```

### 3. Polymetrie
```javascript
$: s("bd*4")           // 4 events
$: s("hh*3")           // 3 events (crée décalage)
$: note("c2*5")        // 5 events (complexité)
```

### 4. Évolution sur 32 cycles
```javascript
$: note("c2*4")
  .s("sawtooth")
  .lpf(sine.range(100, 2000).slow(32))
  .room(sine.range(0.1, 0.5).slow(16))
```

### 5. Silence stratégique
```javascript
// Break tous les 8 cycles
$: s("bd*4").mask("<1!7 0>")
```

## Fréquences clés

### Notes de basse fondamentales
| Note | Hz | Utilisation |
|------|-----|-------------|
| C1 | 32.7 Hz | Sub bass profonde |
| C2 | 65.4 Hz | Bass standard |
| C3 | 130.8 Hz | Bass haute / low mid |

### Zones de fréquence
- **Sub Bass** : 20-60 Hz (C1-B1)
- **Bass** : 60-250 Hz (C2-B2)
- **Low Mids** : 250-500 Hz
- **Mids** : 500-2000 Hz
- **High Mids** : 2000-4000 Hz
- **Highs** : 4000-20000 Hz

## Tension et release

### Créer la tension
- Monter le cutoff du filtre progressivement
- Ajouter des layers de percussions
- Augmenter la densité des notes
- Réduire la reverb (son plus "sec")

### Release / Drop
- Couper soudainement des éléments
- Ouvrir le filtre d'un coup
- Ajouter la reverb massivement
- Retirer le kick puis le ramener

```javascript
// Exemple de build-up
$: s("hh*16")
  .gain(sine.range(0.2, 1).slow(8))
  .lpf(sine.range(500, 8000).slow(8))
```
