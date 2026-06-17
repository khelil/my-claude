# Syntaxe Strudel - Référence Complète

## Mini-Notation

La mini-notation permet d'écrire des patterns rythmiques de manière concise.

### Séquences de base
```javascript
"a b c d"        // 4 événements égaux dans un cycle
"a b [c d]"      // c et d partagent le temps d'un événement
"a b [c d e]"    // c, d, e subdivisés
"a ~ b ~"        // ~ = silence/rest
```

### Multiplicateurs et diviseurs
```javascript
"bd*4"           // Répète bd 4 fois dans le cycle
"bd/2"           // bd joue une fois tous les 2 cycles
"hh*8"           // Hi-hat 8 fois par cycle (croches)
"hh*16"          // Hi-hat 16 fois par cycle (doubles croches)
```

### Alternance avec < >
```javascript
"<a b c>"        // Alterne entre a, b, c à chaque cycle
"<bd sd> hh"     // Cycle 1: "bd hh", Cycle 2: "sd hh"
"<c3 eb3 g3>"    // Arpège qui change chaque cycle
```

### Accords avec ,
```javascript
"[c3,e3,g3]"     // Accord de Do majeur (notes simultanées)
"[c3,eb3,g3]"    // Accord de Do mineur
```

### Euclidean rhythms (x,y)
```javascript
"bd(3,8)"        // 3 kicks distribués sur 8 steps
"hh(5,8)"        // Pattern euclidien classique
"sd(2,8,1)"      // Avec offset de 1
```

### Poids avec @
```javascript
"a@3 b"          // a dure 3x plus que b
"bd@2 ~ sd ~"    // Kick plus long
```

### Probabilité avec ?
```javascript
"hh*8?"          // Chaque hh a 50% de chance de jouer
"sd?0.3"         // 30% de chance de jouer
```

## Fonctions principales

### Sources sonores

```javascript
s("bd sd hh cp")           // Samples (sound)
sound("bd sd")             // Alias de s()
note("c3 e3 g3")           // Notes MIDI
n("0 2 4 7").scale("C:minor") // Notes par index dans une gamme
```

### Synthétiseurs intégrés

```javascript
.s("sawtooth")    // Onde en dent de scie (basses, leads)
.s("square")      // Onde carrée (basses punchy)
.s("triangle")    // Onde triangulaire (doux)
.s("sine")        // Onde sinusoïdale (sub bass)
.s("white")       // Bruit blanc
.s("pink")        // Bruit rose
.s("brown")       // Bruit brun
```

### Banques de samples

```javascript
.bank("RolandTR808")     // Samples 808
.bank("RolandTR909")     // Samples 909
.bank("RolandTR707")     // Samples 707
s("bd").bank("RolandTR909")
```

## Modificateurs de temps

```javascript
.slow(2)          // 2x plus lent (pattern sur 2 cycles)
.fast(2)          // 2x plus rapide
.early(0.25)      // Décale en avant de 1/4 cycle
.late(0.125)      // Décale en arrière
.rev()            // Inverse le pattern
.palindrome()     // Joue puis inverse
```

## Effets audio

### Filtre passe-bas (essentiel pour techno)
```javascript
.lpf(500)                        // Cutoff à 500Hz
.lpf(sine.range(200, 2000).slow(8))  // Modulation lente
.lpq(5)                          // Résonance (0-50)
.cutoff(800)                     // Alias de lpf
```

### Filtre passe-haut
```javascript
.hpf(100)         // Coupe les basses en dessous de 100Hz
.hpq(5)           // Résonance high-pass
```

### Delay
```javascript
.delay(0.5)                    // 50% wet
.delay("0.5:0.25:0.8")         // wet:time:feedback
.delaytime(0.25)               // Temps en cycles (1/4 = croche)
.delayfeedback(0.7)            // Répétitions
```

### Reverb
```javascript
.room(0.5)        // Niveau de reverb (0-1)
.size(4)          // Taille de la pièce
.room("0.5:4")    // Shorthand room:size
```

### Distorsion et saturation
```javascript
.distort(0.5)     // Distorsion douce
.crush(8)         // Bit crusher (1-16)
.shape(0.5)       // Saturation douce
```

### Panoramique et gain
```javascript
.pan(0.5)                      // Centre (0=gauche, 1=droite)
.pan(sine.slow(4))             // Auto-pan
.gain(0.8)                     // Volume (0-1)
.velocity(0.7)                 // Alias de gain pour les notes
```

## Enveloppes ADSR

```javascript
.attack(0.01)     // Temps d'attaque
.decay(0.1)       // Temps de decay
.sustain(0.5)     // Niveau de sustain
.release(0.3)     // Temps de release
.adsr(".01:.1:.5:.3")  // Shorthand
```

## Signaux de modulation (LFOs)

```javascript
sine              // Onde sinusoïdale (0-1)
cosine            // Cosinus
saw               // Dent de scie
tri               // Triangle
square            // Carré
rand              // Aléatoire
perlin            // Bruit de Perlin (smooth random)

// Utilisation
.lpf(sine.range(200, 2000).slow(8))
.gain(perlin.range(0.6, 0.9))
.pan(sine.slow(4))
```

### Méthodes des signaux
```javascript
sine.range(100, 1000)    // Remapper de 100 à 1000
sine.slow(8)             // 8 cycles pour un cycle complet
sine.segment(16)         // Discrétiser en 16 steps
```

## Combinaison de patterns

### stack() - Jouer simultanément
```javascript
stack(
  s("bd*4"),
  s("~ sd"),
  s("hh*8")
)
```

### cat() - Jouer séquentiellement
```javascript
cat(
  s("bd*4"),
  s("sd*2")
)  // Chaque pattern dure 1 cycle
```

### Notation $: pour patterns parallèles
```javascript
$: s("bd*4")
$: s("~ sd")
$: note("c2*2").s("sawtooth")
```

## Gammes et accords

### Gammes disponibles
```javascript
.scale("C:minor")         // Do mineur
.scale("C:major")         // Do majeur
.scale("C:dorian")        // Dorien
.scale("C:phrygian")      // Phrygien (très dark)
.scale("C:aeolian")       // Éolien (= mineur naturel)
.scale("C:locrian")       // Locrien (très tendu)
.scale("C:minorPentatonic")  // Pentatonique mineur
```

### Notation des notes
```javascript
"c3"              // Do octave 3
"c#3"             // Do dièse
"db3"             // Ré bémol (= c#3)
"eb3"             // Mi bémol
"c2 e2 g2 b2"     // Arpège Cmaj7
```

## Modificateurs conditionnels

```javascript
.every(4, fast(2))        // Tous les 4 cycles, double la vitesse
.sometimes(rev)           // 50% du temps, inverse
.rarely(x => x.crush(4))  // Rarement, applique bitcrush
.often(fast(2))           // Souvent, double la vitesse
.someCycles(fast(2))      // Certains cycles
```

## Tempo

```javascript
setcps(0.5)               // 0.5 cycles par seconde = 120 BPM
setcps(128/60/4)          // Formule pour BPM: BPM/60/4
setcps(125/60/4)          // 125 BPM

// Formule: setcps(BPM / 60 / 4)
// 120 BPM = setcps(0.5)
// 125 BPM = setcps(0.521)
// 128 BPM = setcps(0.533)
// 130 BPM = setcps(0.542)
```

## Samples externes

```javascript
// Charger depuis GitHub
samples('github:tidalcycles/dirt-samples')
samples('github:yaxu/clean-breaks')

// Utiliser
s("bd sd hh cp").bank('RolandTR909')
```

## Techniques avancées

### Probabilités et variations
```javascript
.degradeBy(0.3)           // 30% des événements supprimés
.mask("<1 1 0 1>")        // Masque booléen
.struct("<t f t f>")      // Structure booléenne
```

### Polymetrie
```javascript
$: s("bd*4")              // 4/4
$: s("hh*3")              // 3/4 contre 4/4
$: note("c2*5")           // 5/4 contre 4/4
```

### FM Synthesis
```javascript
.fm(4)                    // Index de modulation
.fmh(2)                   // Ratio d'harmonique
```

### Jux (stereo split)
```javascript
.jux(rev)                 // Gauche: normal, Droite: inversé
.jux(fast(2))             // Gauche: normal, Droite: 2x rapide
```
