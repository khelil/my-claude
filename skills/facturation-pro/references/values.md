# Valeurs codées de l'API Facturation.PRO

Source : https://facturation.dev/llms.txt (section « Valeurs spécifiques »).

## payment_mode — factures (ventes)

| Code | Libellé |
|---|---|
| 0 | Non payé |
| 1 | PayPal |
| 2 | Carte bancaire |
| 3 | Virement |
| 4 | Chèque |
| 5 | Espèces |
| 6 | CESU préfinancé |
| 8 | Prélèvement |
| 9 | TIP |
| 30 | Ticket restaurant |
| 31 | Chèque cadeau |
| 32 | Chèque vacances |
| 50 | LCR |
| 51 | BOR |
| 90 | Avoir |
| 99 | Autre |
| 999 | Créance irrécouvrable |

## payment_mode — achats

Identique aux ventes pour 0–5, 8, 9, 30–32, 50, 51, 90, 99, plus :

| Code | Libellé |
|---|---|
| 7 | Compte courant d'associé |
| 20 | Crédit fournisseur |

(pas de 6 ni de 999 pour les achats)

## pay_before — délai de paiement (chaîne)

| Code | Libellé |
|---|---|
| 0 | À réception |
| cash | Comptant |
| 15 / 30 / 45 / 60 | N jours nets à compter de la livraison |
| 07fm / 30fm / 45fm | N jours fin de mois, à compter de la livraison |
| 00fm10 / 00fm20 | fin de mois le 10 / le 20 |
| 30fm10 / 30fm20 | 30 jours fin de mois le 10 / le 20 |
| 15-inv / 30-inv / 45-inv / 60-inv | N jours nets à compter de la facturation |
| 07fm-inv / 30fm-inv / 45fm-inv | N jours fin de mois à compter de la facturation |
| 00fm10-inv / 00fm20-inv / 30fm10-inv / 30fm20-inv | variantes fin de mois à compter de la facturation |

Des délais personnalisés peuvent exister : Paramètres / Facturation dans l'interface web.

## nature — lignes de facturation (auto/micro-entrepreneurs uniquement)

| Code | Libellé |
|---|---|
| 1 | Vente |
| 2 | BIC - prestations de service commerciales ou artisanales |
| 3 | BNC - prestation non commerciale |
| 8 | Débours |
| 9 | Non applicable |

## nature — achats

| Code | Libellé |
|---|---|
| 1 | Achat de biens |
| 2 | Prestation de service |
| 5 | Mixte |
| 9 | Autre |

## quote_status — état d'un devis

| Code | Libellé |
|---|---|
| 0 | En attente |
| 1 | Accepté |
| 9 | Refusé |

Filtres de liste `status` sur `quotes` : `pending` (non soldés, en attente ou acceptés),
`to_invoice` (acceptés non soldés), `invoiced` (soldés), ou `0` / `1` / `9`.

## bill_type — filtre de liste sur invoices

| Valeur | Sens |
|---|---|
| paid | Payées |
| unpaid | Non payées |
| term | Échues, à relancer |
| invoice | Factures (hors avoirs, acomptes…) |
| external | Factures externes importées |
| refund | Avoirs |
| down_payment | Acomptes |
| draft | Brouillons |
| notes | Notes internes |
| nova | Nova (service à la personne) |

## purchase_type — filtre de liste sur purchases

`pending`, `draft`, `unpaid`, `paid`, `prepaid`, `excluded` (exclus des exports), `forecast` (prévisionnel).

## mode — filtre de liste sur customers

`all`, `company`, `individual`, `missing_siret`, `archived` (défaut : clients actifs seulement).

## status — catégories

| Code | Affectation |
|---|---|
| 0 | Achats et ventes |
| 1 | Ventes uniquement |
| 2 | Achats uniquement |

## status — suivis commerciaux (followups)

| Code | Affectation |
|---|---|
| 0 | Devis et factures |
| 1 | Devis uniquement |
| 2 | Factures uniquement |

Deux suivis système utilisables dans `followup_id` : `0` En cours, `-1` Terminé.

## style — lignes de facturation

`""` ligne standard · `comment` · `title` (gras) · `subtotal` · `new_page` · `subsidy` (déduction sur le TTC, ex. prime CEE).

## language — langue du PDF

`fr`, `en`, `es`, `nl`.

## currency

Code ISO 4217 à trois lettres (`EUR` par défaut). Liste complète dans la doc brute.
