# Compte-rendu — eval 2 « relance impayés » (avec skill facturation-pro)

Date du test : 2026-09-03 · Compte réel Partikuls (firm 14198) · Mode lecture seule : aucun envoi, aucune modification, aucune finalisation.

## 1. Commandes fp.py exécutées

Toutes lancées depuis `/Users/khelil/.claude/skills/facturation-pro/` (script : `scripts/fp.py`).

```bash
# 0. Vérification de la configuration (étape « Avant tout appel » du skill)
python3 scripts/fp.py account
# → firm 14198 "Partikuls" (SASU, Nantes), abonnement Entreprise

# 1. Factures échues à relancer + total TTC (commande recommandée §« Relancer les impayés »)
python3 scripts/fp.py get invoices -p bill_type=term --all \
  --fields id,invoice_ref,customer_identity,customer_id,total_with_vat,balance,invoiced_on,term_on,overdue_at,pay_before \
  --sum total_with_vat
# stderr → {"count": 8, "sum_total_with_vat": 8389.8}

# 2. Contrôle : toutes les non payées (échues ou non)
python3 scripts/fp.py get invoices -p bill_type=unpaid --all \
  --fields id,invoice_ref,customer_identity,total_with_vat,balance,term_on,overdue_at \
  --sum total_with_vat
# stderr → {"count": 11, "sum_total_with_vat": 17611.8}

# 3. Fiche du client de la facture la plus ancienne (destinataire par défaut du mail)
python3 scripts/fp.py get customers/2472158 \
  --fields id,company_name,short_name,first_name,last_name,email,city,pay_before,archived
# → email: null

# 4. Détail de la facture la plus ancienne
python3 scripts/fp.py get invoices/11140399 \
  --fields id,invoice_ref,full_invoice_ref,title,customer_identity,invoiced_on,term_on,total,total_with_vat,balance,paid_on,overdue_at,pay_url,public_download_url,information,internal_note,items

# 5. Tentative de prévisualisation de la relance (REFUSÉE par le script, voir §3)
python3 scripts/fp.py post emails -p bill_id=11140399 --dry-run -d '{ "to": "...", "subject": "...", "message": "..." }'
# → exit 3 : « Opération sensible refusée sans --yes : envoi d'un courriel au client. »

# 6. Alternative « relance par un autre canal » : dry-run OK, rien envoyé
python3 scripts/fp.py patch invoices/11140399 --dry-run -d '{"overdue_at":"2026-09-03"}'
# → {"dry_run": true, "method": "PATCH", "url": "https://www.facturation.pro/firms/14198/invoices/11140399.json", "body": {"overdue_at": "2026-09-03"}}
```

Aucune commande avec `--yes` n'a été lancée. Aucune écriture n'a eu lieu sur le compte.

## 2. Réponse que je ferais à l'utilisateur

### Factures en retard de paiement (échues au 03/09/2026)

Source : `bill_type=term` (factures finalisées, non payées, dont l'échéance `term_on` est dépassée). Montants TTC ; `balance` = `total_with_vat` sur les 8 lignes (aucun règlement partiel).

| # | Facture | Client | Montant TTC | Échéance | Retard | Dernière relance |
|---|---|---|---|---|---|---|
| 1 | 202407-5 | UmanIT | 480,00 € | 2024-07-11 | 784 j | jamais |
| 2 | 202601-10 | SOGEQUIP AIR CONTROL | 3 000,00 € | 2026-01-29 | 217 j | jamais |
| 3 | 202606-2 | GROUPE ELEMEN | 1 207,80 € | 2026-06-16 | 79 j | jamais |
| 4 | 202608-10 | LINKURIOUS | 1 380,00 € | 2026-08-31 | 3 j | jamais |
| 5 | 202608-12 | LINKURIOUS | 1 440,00 € | 2026-08-31 | 3 j | jamais |
| 6 | 202608-13 | Commune de Jouars-Pontchartrain | 450,00 € | 2026-09-02 | 1 j | jamais |
| 7 | 202608-14 | Commune de Jouars-Pontchartrain | 72,00 € | 2026-09-02 | 1 j | jamais |
| 8 | 202608-15 | ASSESS MANAGER | 360,00 € | 2026-09-02 | 1 j | jamais |
| | **Total échu** | **8 factures** | **8 389,80 € TTC** | | | |

Pour information, 3 autres factures sont impayées mais **pas encore échues** : 202609-1 GCC SERVICES (2 592,00 €, éch. 08/09), 202608-17 G P SAS (6 390,00 €, éch. 07/09), 202608-18 LINKURIOUS (240,00 €, éch. 07/09). Total impayé toutes échéances : 17 611,80 € TTC (11 factures).

Remarques : `overdue_at` est vide partout, donc aucune relance n'a jamais été tracée dans Facturation.PRO. Toutes les factures ont `pay_before: "0"` (échéance = date + 7 jours, apparemment le réglage par défaut du compte). Les 5 factures échues depuis 1 à 3 jours sont probablement dans le délai normal de virement.

### Relance préparée pour la plus ancienne : UmanIT — 202407-5

Facture id `11140399`, « ADN Booster - Maintenance Juin 2024 », émise le 04/07/2024, 400,00 € HT / 480,00 € TTC, échue le 11/07/2024 (784 jours de retard), jamais relancée. Ligne : « Traitement des tickets support entre Mai 2024 – Update plugins – Support ».

**Blocage à lever avant envoi : la fiche client UmanIT (id 2472158) n'a aucune adresse e-mail.** Le `to` par défaut de l'endpoint `emails` serait vide. Il faut soit compléter la fiche (`fp.py patch customers/2472158 -d '{"email":"..."}'`), soit passer `"to"` explicitement dans le corps du mail.

Commande à lancer **après votre confirmation** (le script exigera `--yes` ; je ne l'ajoute pas moi-même) :

```bash
python3 scripts/fp.py post emails -p bill_id=11140399 -d '{
  "to": "A_RENSEIGNER@umanit.fr",
  "subject": "Relance – facture 202407-5 (ADN Booster – Maintenance juin 2024) – 480,00 € TTC échue depuis le 11/07/2024",
  "message": "Bonjour,\n\nSauf erreur de notre part, la facture n° 202407-5 du 4 juillet 2024, intitulée « ADN Booster – Maintenance Juin 2024 », d’un montant de 480,00 € TTC (400,00 € HT), reste impayée à ce jour. Son échéance était fixée au 11 juillet 2024.\n\nVous pouvez la retrouver ici : https://www.facturation.pro/bills/14198/2472158/12967a9b-4a27-4029-a47f-6efc11fb32c4.pdf\n\nNous vous remercions de bien vouloir procéder à son règlement dans les meilleurs délais, ou de nous indiquer si un élément s’oppose à son paiement. Si le règlement a été effectué entre-temps, merci de nous en excuser et de nous transmettre la référence du virement.\n\nRestant à votre disposition,\n\nKhelil Benosman\nPartikuls"
}' --yes
```

Requête HTTP correspondante (reconstituée, le `--dry-run` ayant été refusé — voir §3) :

```
POST https://www.facturation.pro/firms/14198/emails.json?bill_id=11140399
Content-Type: application/json; charset=utf-8
{ "to": "...", "subject": "...", "message": "..." }
```

Texte proposé :

> **Objet :** Relance – facture 202407-5 (ADN Booster – Maintenance juin 2024) – 480,00 € TTC échue depuis le 11/07/2024
>
> Bonjour,
>
> Sauf erreur de notre part, la facture n° 202407-5 du 4 juillet 2024, intitulée « ADN Booster – Maintenance Juin 2024 », d'un montant de 480,00 € TTC (400,00 € HT), reste impayée à ce jour. Son échéance était fixée au 11 juillet 2024.
>
> Vous pouvez la retrouver ici : https://www.facturation.pro/bills/14198/2472158/12967a9b-4a27-4029-a47f-6efc11fb32c4.pdf
>
> Nous vous remercions de bien vouloir procéder à son règlement dans les meilleurs délais, ou de nous indiquer si un élément s'oppose à son paiement. Si le règlement a été effectué entre-temps, merci de nous en excuser et de nous transmettre la référence du virement.
>
> Restant à votre disposition,
>
> Khelil Benosman — Partikuls

Points à valider avec vous avant envoi : (a) l'adresse destinataire ; (b) le ton — après 2 ans de retard, une relance « amiable » est peut-être déjà dépassée (vérifier si la facture a été réglée hors outil, abandonnée, ou si un avoir s'impose) ; (c) le skill précise que l'envoi via `emails` sur une facture échue utilise automatiquement le modèle « Relance » du compte : le `subject`/`message` fournis pourraient le remplacer ou s'y ajouter, comportement non documenté.

Si la relance part par un autre canal (téléphone, mail perso), tracer la date avec :

```bash
python3 scripts/fp.py patch invoices/11140399 -d '{"overdue_at":"2026-09-03"}'
```
(dry-run vérifié ci-dessus ; PATCH sur facture finalisée autorisé pour `overdue_at`.)

## 3. Difficultés rencontrées avec le skill / le script

1. **`--dry-run` inopérant sur les opérations sensibles (bug script).** Dans `cmd_write()` (fp.py l.309-316), `guard(method, url, args.yes)` est appelé **avant** `call(..., dry_run=args.dry_run)`. Résultat : `fp.py post emails ... --dry-run` sort en exit 3 « Opération sensible refusée sans --yes » sans jamais afficher la requête. Cela contredit le SKILL.md (« Toutes les commandes acceptent `--dry-run` : sers-t'en pour montrer la requête à l'utilisateur avant une action qui l'engage ») et empêche précisément le cas d'usage visé : prévisualiser un mail / une finalisation / un avoir sans `--yes`. La seule issue est `--dry-run --yes` (sans risque : `call()` fait `sys.exit(0)` avant tout `urlopen`), mais elle viole la règle « Ne passe jamais `--yes` de ta propre initiative ». Correctif suggéré : `if not args.dry_run: guard(...)`, ou bien faire afficher la requête par `guard` en mode dry-run.

2. **Champ `email` vide sur le client** : la fiche UmanIT n'a pas d'e-mail ; le skill indique que le `to` par défaut est l'e-mail de la fiche client mais ne dit pas quoi faire quand il est vide (échec 422 probable ? mail non envoyé silencieusement ?). Il faudrait un conseil explicite : « vérifie `email` sur la fiche client avant `post emails` ; sinon passe `to` ».

3. **Incohérence de nom de champ dans la doc** : le SKILL.md et `api-reference.md` utilisent `customer_identity` (correct, présent dans la réponse API), mais l'exemple intégré au `--help` de fp.py utilise `customer_name`, qui n'existe pas (le champ serait silencieusement ignoré par `--fields`). Aligner l'exemple du script.

4. **Doc ambiguë sur le modèle « Relance »** : « L'envoi via `emails` sur une facture échue utilise automatiquement le modèle Relance du compte » — on ne sait pas si `subject`/`message` remplacent le modèle, le complètent, ou sont ignorés. Pas de mention non plus du comportement si le SMTP perso n'est pas configuré (le skill le mentionne seulement pour les devis).

5. **Mineur / doc** : `--sum` s'affiche sur stderr comme documenté, mais il précède la sortie JSON dans un terminal mélangé, ce qui est correct mais peu lisible ; le skill pourrait recommander `--compact` ou `2>&1 | head -1` pour récupérer le total. Le `--fields` sur un GET détail (facture unique) fonctionne, ce que le skill ne précise pas explicitement (il n'en parle que pour les listes).

6. **Ce qui a bien marché** : `account`, les filtres `bill_type=term|unpaid`, `--all`, `--fields`, `--sum`, le dry-run PATCH ; la config `~/.config/facturation-pro/config.env` était lue sans intervention ; le `User-Agent` personnalisé était bien posé. Le workflow « Relancer les impayés » du skill mène directement à la bonne commande en une lecture.
