# API Facturation.PRO — référence condensée

Base : `https://www.facturation.pro/` · Auth : Basic `IdentifiantApi:CleApi` · JSON snake_case
sans élément racine · toutes les URL en `.json` · tout est préfixé `/firms/FIRM_ID/` sauf
`/account.json`. Création → `201 Created` + en-tête `Location`. Listes : 50 par page,
paramètre `page=N`, en-tête `x-pagination` (minuscules) `{"current_page","total_pages","per_page","total_entries"}`.
Quota : 600 req / 5 min, 10 000 / jour, `429` + `Retry-After`. Champs `api_id` (bigint) et
`api_custom` (string 255) libres sur presque toutes les ressources.

Tri commun : `sort=asc|desc`, `order=<clé>` (clés listées par ressource).
Périodes : `period_start`, `period_end` en `AAAA-MM` ou `AAAA-MM-JJ`.

Avec `fp.py`, écrire `get customers` pour `GET /firms/FIRM_ID/customers.json`.

## Compte

| Méthode | Chemin | Note |
|---|---|---|
| GET | `/account.json` | email + liste `firms[{id,name}]` |
| GET | `orders` | factures d'abonnement Facturation.PRO |

## Clients — `customers`

| Méthode | Chemin | Note |
|---|---|---|
| GET | `customers` | filtres : `company`, `last_name`, `email`, `category_id` (0 = sans), `api_id`, `api_custom`, `mode=all|company|individual|missing_siret|archived`, `with_sepa=1` (admin), `account_code`, `accounting_entry` · order : `last_invoice`, `last_paid`, `created`, `updated` |
| POST | `customers` | pro par défaut ; `individual: true` pour un particulier |
| GET | `customers/ID` | `with_sepa=1` (admin sinon 403) |
| PATCH | `customers/ID` | partiel |
| DELETE | `customers/ID` | seulement si jamais facturé ; supprime aussi ses devis |
| POST | `customers/ID/archive` · `customers/ID/unarchive` | |
| POST | `customers/ID/upload` | multipart `upload_file`, `?filename=` |
| GET | `customers/ID/quotes` · `customers/ID/invoices` | redirige (302) vers `quotes?customer_id=ID` : utilise directement cette forme |

Champs modifiables : `company_name`, `civility`, `first_name`, `last_name`, `short_name`,
`street`, `city`, `zip_code`, `country` (ISO-2 maj.), `phone`, `fax`, `email`, `mobile`,
`website`, `notes`, `vat_number`, `siret`, `category_id`, `account_code`, `accounting_entry`,
`sepa_iban`, `sepa_bic`, `sepa_rum`, `sepa_signature_on`, `individual`, `reference`, `penalty`,
`discount`, `pay_before`, `validity` (jours de validité devis), `currency`, `language`,
`default_vat`, `vat_country`, `vat_exemption`, `invoice_email`, `electronic_address`,
`field1..field5`. Lecture : `id`, `last_invoiced_on`, `last_paid_on`, `created_at`, `updated_at`.

## Devis — `quotes`

| Méthode | Chemin | Note |
|---|---|---|
| GET | `quotes` | `with_details=1` (items + fichiers) · filtres : `quote_ref`, `full_quote_ref`, `customer_id`, `title`, `company`, `last_name`, `status=pending|to_invoice|invoiced|0|1|9`, `category_id`, `followup_id`, `user_id`, périodes · order : `customer`, `total`, `billed`, `created`, `updated` |
| POST | `quotes` | ≥ 1 `items` ; pas de totaux |
| GET | `quotes/ID` | inclut `items`, `files`, `invoice_ids` |
| PATCH | `quotes/ID` | items : liste complète ; `_destroy: "1"` pour supprimer |
| DELETE | `quotes/ID` | |
| GET | `quotes/ID.pdf` | `?proforma=1` pour une pro-forma |
| POST | `quotes/ID/invoice` | convertit en facture finalisée (201 + facture) |
| POST | `emails?bill_id=ID` | `{to,cc,bcc,subject,message}` ; SMTP perso requis |
| POST | `quotes/ID/upload` | `?filename=&visible=1` |

Champs document (devis et factures) : `customer_id`, `title`, `language`, `category_id`,
`followup_id`, `invoiced_on`, `term_on`, `currency`, `rebate_percentage`, `vat_exemption`,
`vat_country`, `tax_title`, `tax_percent`, `penalty`, `pay_before`, `discount`, `precompte`,
`activity_title`, `service_personne`, `accounting_entry`, `information` (visible sur le PDF),
`internal_note`, `purchase_number`, `user_id`, `delivery_on`, `items`, `api_id`, `api_custom`.
Lecture : `total` (HT), `total_with_vat`, `draft`, `public_download_url`, `files`,
`created_at`, `updated_at`. Devis seulement : `quote_status` (modifiable), `quote_ref`,
`ignore_quote`, `fully_invoiced`, `amount_invoiced`, `invoice_ids`.

Ligne (`items[]`) : `id`, `position`, `title`, `quantity`, `measure`, `unit_price` (HT),
`vat` (fraction), `product_id`, `optional` (devis), `style`, `nature`, `sap_nature`.
Lecture : `total`.

## Factures — `invoices`

| Méthode | Chemin | Note |
|---|---|---|
| GET | `invoices` | `with_details=1`, `with_settlements=1` · filtres : `invoice_ref`, `full_invoice_ref`, `payment_ref`, `title`, `customer_id`, `company`, `last_name`, `bill_type=paid|unpaid|term|invoice|external|refund|down_payment|draft|notes|nova`, `category_id`, `followup_id`, `user_id`, périodes (`period_type=billed` pour la date de facture, sinon date d'encaissement) · order : `customer`, `paid`, `total`, `billed`, `term`, `created`, `updated` |
| POST | `invoices` | `?type_doc=draft` brouillon ; `?external=1` + `external_ref` pour importer une facture externe ; sinon **finalisée immédiatement** |
| GET | `invoices/ID` | inclut `items`, `settlements`, `balance` |
| PATCH | `invoices/ID` | `?type_doc=final` finalise un brouillon ; finalisée : seuls règlement/infos modifiables |
| DELETE | `invoices/ID` | brouillons uniquement |
| GET | `invoices/ID.pdf` | acquittée si payée ; `?original=1` pour l'originale |
| POST | `invoices/ID/refund` | avoir total ; `?api_id=&api_custom=` |
| POST | `emails?bill_id=ID` | finalisées uniquement ; modèle auto Facture / Relance / Confirmation |
| POST | `invoices/ID/upload` | |
| GET | `recurring_invoices` · `recurring_invoices/ID` | lecture seule |

Champs propres aux factures : `payment_mode`, `paid_on`, `payment_ref`, `paid_in_main_currency`,
`external_ref`, `overdue_at` (dernière relance), `balance_year`. Lecture : `invoice_ref`,
`full_invoice_ref`, `quote_id`, `refund_id`, `pay_url`, `balance` (restant dû), `external`,
`settlements`, `recurring_invoice_id`.

## Règlements — `invoices/INVOICE_ID/settlements`

| Méthode | Chemin | Note |
|---|---|---|
| GET | `invoices/ID/settlements` | |
| POST | `invoices/ID/settlements` | `{total, payment_mode, paid_on, payment_ref}` ; solde atteint → facture payée |
| GET / DELETE | `invoices/ID/settlements/SID` | supprimer un règlement d'une facture soldée la repasse « non payée » |

## Achats — `purchases`

| Méthode | Chemin | Note |
|---|---|---|
| GET | `purchases` | `with_details=1` · filtres : `company`, `title`, `invoice_ref`, `payment_ref`, `serial_number`, `purchase_type=pending|draft|unpaid|paid|prepaid|excluded|forecast`, `accounting_entry`, périodes (`period_type=billed`) · order : `paid`, `total`, `term`, `created`, `updated` |
| POST | `purchases` | `{supplier_id, invoiced_on, title, total_with_vat, vat_amount, …}` |
| GET / PATCH / DELETE | `purchases/ID` | |
| POST | `purchases/ID/upload` | justificatif |
| GET | `recurring_purchases` · `recurring_purchases/ID` | lecture seule |

Champs : `supplier_id`, `title`, `ref`, `total_with_vat`, `vat_amount`, `currency`,
`invoiced_on`, `term_on`, `paid_on`, `payment_mode` (codes achats), `payment_ref`,
`paid_in_main_currency`, `draft`, `reverse_charge`, `prepaid`, `notes`, `skip_export`,
`category_id`, `accounting_entry`, `accounting_asset`, `asset_end_on`, `asset_end_reason`,
`nature`. Lecture : `total` (HT), `supplier_identity`, `serial_number`, `files`.

## Fournisseurs — `suppliers`

GET (filtres `company`, `category_id`, `country`, `with_sepa`, `account_code`,
`accounting_entry` ; order `created`, `updated`), POST, GET/PATCH/DELETE `suppliers/ID`.
Mêmes champs d'identité qu'un client + `reverse_charge`.

## Produits — `products`

GET (filtres `ref`, `title` ; order `ref`, `created`, `updated`), POST, GET/PATCH/DELETE
`products/ID`. Champs : `ref`, `title`, `unit_price`, `vat`, `measure`, `nature`,
`sap_nature`, `category_id`, `notes`, `field1..5`. Supprimer un produit ne touche pas aux
lignes déjà facturées.

## Catégories — `categories`

GET (filtres `title`, `status`), POST `{title, status}`, GET/PATCH/DELETE `categories/ID`.

## Suivis commerciaux — `followups`

GET (filtres `title`, `status`), POST `{title, status}`, GET/PATCH/DELETE `followups/ID`.
Suivis système : `0` En cours, `-1` Terminé.

## Fichiers — `assets`

GET `assets/quotes` (`quote_id`), `assets/invoices`, `assets/customers`, `assets/purchases`
(order `title`, `size`, `updated`, `created`) · DELETE `assets/ID`. Upload via
`<ressource>/ID/upload`. Champs : `document_name`, `document_size`, `download_url`, `visible`.

## Codes d'erreur

| Code | Sens |
|---|---|
| 400 / 422 | données invalides ; détail dans `errors` |
| 401 | identifiants |
| 403 | droits (SEPA sans clé admin) |
| 404 | introuvable |
| 429 | quota, voir `Retry-After` |
| 501 | Content-Type absent |
