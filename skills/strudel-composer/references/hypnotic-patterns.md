# Patterns Hypnotiques - Templates et Techniques

## Templates complets prêts à l'emploi

### Template 1: Deep Hypnotic Minimal (125 BPM)

```javascript
// Deep Hypnotic Minimal - 125 BPM
// Tonalité: C mineur
setcps(125/60/4)

// === DRUMS ===
// Kick profond 4/4
$: s("bd*4")
  .bank("RolandTR909")
  .gain(0.9)

// Rimshot/Clap décalé
$: s("~ rim ~ rim")
  .bank("RolandTR909")
  .gain(0.6)
  .room(0.3)

// Hi-hats évolutifs
$: s("hh*8")
  .bank("RolandTR909")
  .gain(perlin.range(0.3, 0.5))
  .pan(sine.slow(4))
  .hpf(6000)

// === BASS ===
// Sub bass hypnotique
$: note("c1*4")
  .s("sine")
  .gain(0.7)
  .lpf(100)

// Bass line avec mouvement
$: note("c2 ~ c2 <c2 eb2>")
  .s("sawtooth")
  .lpf(sine.range(200, 800).slow(8))
  .lpq(5)
  .gain(0.5)

// === ATMOSPHÈRE ===
// Pad évolutif
$: note("<[c3,eb3,g3]!3 [bb2,d3,f3]>")
  .s("sawtooth")
  .lpf(sine.range(400, 1200).slow(16))
  .room(0.6)
  .size(4)
  .gain(0.25)
  .slow(4)
```

### Template 2: Mental Techno Polymetric (128 BPM)

```javascript
// Mental Techno Polymetric - 128 BPM
// Tonalité: D mineur
setcps(128/60/4)

// === DRUMS ===
// Kick avec variation
$: s("<bd*4 bd(3,8)>")
  .bank("RolandTR909")
  .gain(0.95)

// Snare minimal
$: s("~ sd ~ ~")
  .bank("RolandTR909")
  .gain(0.7)
  .room(0.2)

// Hi-hats polyrythmiques (5 sur 8)
$: s("hh(5,8)")
  .bank("RolandTR909")
  .gain(0.4)
  .pan(rand)
  .hpf(8000)

// Percussion additionnelle (3 sur 8)
$: s("cp(3,8)")
  .bank("RolandTR808")
  .gain(0.35)
  .delay("0.3:0.25:0.5")

// === BASS ===
// Bass hypnotique avec mouvement minimal
$: note("d1 d1 d1 <d1 a0>")
  .s("square")
  .lpf(150)
  .gain(0.6)

// Ligne de basse mélodique
$: note("d2 ~ f2 ~ d2 ~ <a2 g2> ~")
  .s("sawtooth")
  .lpf(sine.range(300, 1000).slow(16))
  .lpq(8)
  .gain(0.45)
  .delay("0.2:0.125:0.4")

// === LEAD ===
// Arpège hypnotique
$: note("d3 f3 a3 <f3 g3>")
  .s("triangle")
  .lpf(sine.range(500, 2000).slow(8))
  .delay("0.4:0.25:0.6")
  .room(0.5)
  .gain(0.3)

// === TEXTURE ===
// Noise sweep (tension)
$: s("white")
  .lpf(sine.range(100, 4000).slow(32))
  .hpf(100)
  .gain(perlin.range(0, 0.15).slow(8))
```

### Template 3: Ambient Techno Drone (118 BPM)

```javascript
// Ambient Techno Drone - 118 BPM
// Tonalité: A mineur
setcps(118/60/4)

// === DRUMS (minimal) ===
// Kick espacé
$: s("bd ~ ~ bd ~ ~ bd ~")
  .bank("RolandTR808")
  .gain(0.85)
  .room(0.2)

// Hi-hat subtil
$: s("hh*4")
  .bank("RolandTR808")
  .gain(perlin.range(0.1, 0.3))
  .pan(sine.slow(8))
  .hpf(10000)
  .room(0.4)

// === BASS ===
// Drone de basse
$: note("a1")
  .s("sine")
  .gain(0.5)
  .lpf(80)

// === ATMOSPHÈRES ===
// Pad principal (évolution très lente)
$: note("[a2,c3,e3]")
  .s("sawtooth")
  .lpf(sine.range(200, 600).slow(32))
  .room(0.8)
  .size(8)
  .gain(0.2)
  .attack(2)
  .release(4)

// Texture granulaire
$: s("white")
  .lpf(perlin.range(200, 800).slow(16))
  .hpf(100)
  .gain(perlin.range(0, 0.1))
  .room(0.9)

// Mélodie flottante
$: note("<a4 e4 c4 e4>")
  .s("triangle")
  .lpf(1000)
  .delay("0.6:0.333:0.7")
  .room(0.7)
  .gain(0.15)
  .slow(2)
```

## Patterns de drums par style

### Kick patterns

```javascript
// Standard 4/4
s("bd*4")

// Offbeat kick (deep house influence)
s("bd ~ bd ~")

// Tribal/Hypnotic
s("bd(3,8)")

// Driving techno
s("bd bd ~ bd")

// Broken beat
s("bd ~ [~ bd] ~")

// Double kick (hard techno)
s("[bd bd] ~ bd ~")
```

### Hi-hat patterns

```javascript
// Croches standard
s("hh*8")

// Doubles croches
s("hh*16")

// Off-beat
s("~ hh ~ hh ~ hh ~ hh")

// Shuffle
s("hh [~ hh] hh [~ hh]")

// Polyrythmique
s("hh(5,8)")
s("hh(7,16)")

// Avec variations de vélocité
s("hh*8").gain("[1 0.5 0.7 0.5]*2")
```

### Clap/Snare patterns

```javascript
// Backbeat classique
s("~ sd ~ sd")

// Minimal
s("~ sd ~ ~")

// Offbeat
s("~ ~ sd ~")

// Ghost notes
s("~ [~ sd] ~ sd")
```

## Patterns de basse hypnotiques

### Une note (ultra minimal)
```javascript
note("c2*4").s("sawtooth").lpf(400)
```

### Deux notes (tension)
```javascript
note("c2 c2 c2 <c2 eb2>").s("sawtooth")
```

### Octave jump
```javascript
note("c1 c2 c1 c2").s("square").lpf(300)
```

### Arpège simple
```javascript
note("c2 eb2 g2 eb2").s("sawtooth").lpf(500)
```

### Avec silences
```javascript
note("c2 ~ c2 ~ eb2 ~ c2 ~").s("sawtooth")
```

## Techniques de modulation

### Filter sweep classique
```javascript
.lpf(sine.range(200, 4000).slow(16))
```

### Ouverture progressive
```javascript
.lpf(saw.range(200, 2000).slow(32))
```

### Modulation aléatoire contrôlée
```javascript
.lpf(perlin.range(400, 1500).slow(8))
```

### Résonance modulée
```javascript
.lpf(800).lpq(sine.range(1, 15).slow(8))
```

### Delay modulé
```javascript
.delay("0.5:0.25:0.6")
.delaytime(sine.range(0.1, 0.3).slow(4))
```

## Structures d'arrangement

### Build-up (8-16 cycles)
```javascript
// Augmenter progressivement
$: s("hh*16")
  .gain(saw.range(0.1, 0.8).slow(8))
  .lpf(saw.range(500, 10000).slow(8))
```

### Drop
```javascript
// Retirer le kick puis le ramener
$: s("bd*4").mask("<1!7 0 1!8>")
```

### Breakdown
```javascript
// Garder seulement pads et effets
$: note("[c3,eb3,g3]")
  .s("sawtooth")
  .lpf(sine.range(200, 800).slow(8))
  .room(0.8)
  .gain(0.3)
```

## Effets signature

### Reverb massive (pour drops)
```javascript
.room(0.9).size(8)
```

### Delay dub
```javascript
.delay("0.6:0.333:0.8")
```

### Sidechain simulé
```javascript
.gain("[1 0.3 0.5 0.3]*4")
```

### Espace stéréo
```javascript
.pan(sine.slow(4))
.jux(rev)
```

### Distorsion subtile
```javascript
.shape(0.3)
// ou
.distort(0.2)
```

## Formule de tempo

```javascript
// Convertir BPM en CPS (cycles par seconde)
// Formule: setcps(BPM / 60 / 4)

setcps(120/60/4)  // 120 BPM = 0.5 cps
setcps(125/60/4)  // 125 BPM ≈ 0.521 cps
setcps(128/60/4)  // 128 BPM ≈ 0.533 cps
setcps(130/60/4)  // 130 BPM ≈ 0.542 cps
setcps(135/60/4)  // 135 BPM = 0.5625 cps
```
