---
name: facturation-pro
description: Pilote l'outil de facturation Facturation.PRO (facturation.pro / facturation.dev) via son API REST — clients, devis, factures, avoirs, règlements, achats, fournisseurs, produits, PDF, envoi par mail, reporting CA / impayés. Utilise ce skill dès que l'utilisateur parle de facturer, faire un devis, une facture, un avoir, encaisser ou relancer un client, enregistrer un achat ou une note de frais, sortir son chiffre d'affaires, ses impayés ou "sa compta", même sans nommer Facturation.PRO. Toujours passer par scripts/fp.py, jamais par des appels curl improvisés.
---

# Facturation.PRO — devis, factures et compta par l'API

Facturation.PRO est l'outil de facturation de l'utilisateur. Ce skill fournit un client CLI
(`scripts/fp.py`) et les règles métier de l'API pour créer des devis, des factures, encaisser,
gérer les achats et sortir des chiffres, sans jamais réinventer l'appel HTTP.

## Avant tout appel

1. Vérifie la configuration : `python3 scripts/fp.py account`. La réponse liste les `firms`
   (entreprises) et leurs ID. Si le script réclame des variables, indique à l'utilisateur de
   remplir `~/.config/facturation-pro/config.env` à partir de `assets/config.env.example`
   (clés sur https://www.facturation.pro/account/api). Ne demande jamais la clé en clair
   dans la conversation et ne l'écris jamais dans une note ou un fichier suivi par git.
2. Reste dans le quota : 600 requêtes / 5 min et 10 000 / jour. Les listes renvoient 50
   éléments par page et **tous les champs** : ne refais pas un GET par élément après une liste.
   Filtre côté API (`-p company=…`, `-p bill_type=unpaid`, `-p period_start=…`) plutôt que de
   tout télécharger.
3. Toutes les commandes acceptent `--dry-run` : sers-t'en pour montrer la requête à
   l'utilisateur avant une action qui l'engage. Le dry-run passe sans `--yes`, mais il ne
   valide rien côté serveur : un 422 (champ manquant) n'apparaît qu'au vrai envoi.
4. Dans `account`, `disk_free: 0` signifie que le compte n'a pas l'option Gold : les
   `upload` de pièces jointes sont refusés (le script sort en code 4 avec l'explication).
   Ne promets pas de joindre un fichier dans ce cas ; propose de le garder localement.

## Le client fp.py

```
python3 scripts/fp.py account
python3 scripts/fp.py get <ressource>[/<id>] [-p cle=valeur …] [--all] [--fields a,b,c] [--sum champ]
python3 scripts/fp.py post <ressource> [-p …] -d '<json>' | -d @fichier.json [--yes]
python3 scripts/fp.py patch <ressource>/<id> [-p …] -d '<json>' [--yes]
python3 scripts/fp.py delete <ressource>/<id> --yes
python3 scripts/fp.py pdf quotes|invoices <id> [-o fichier.pdf] [--proforma] [--original]
python3 scripts/fp.py upload customers|quotes|invoices|purchases <id> <fichier> [--filename x] [--visible]
```

Les chemins relatifs sont préfixés par `/firms/FIRM_ID/` et suffixés par `.json`. Le script
suit la pagination (`--all`), réessaie sur 429 en respectant `Retry-After`, et affiche le corps
d'erreur JSON avec un indice. `--fields` réduit la sortie aux colonnes utiles : utilise-le
systématiquement sur les listes pour ne pas noyer la conversation.

### Garde-fou sur les opérations irréversibles

Le script refuse sans `--yes` : toute suppression, la création d'une facture finalisée, la
finalisation d'un brouillon, la conversion devis → facture, un avoir, un envoi de mail.
Une suppression est « douce » : l'enregistrement reste lisible avec `soft_deleted: true` et
`hard_delete_on` (purge 14 jours plus tard), mais l'API n'expose pas de restauration. Une
facture finalisée reçoit un numéro légal et ses montants deviennent immuables ; la seule
correction possible ensuite est un avoir. Demande donc une confirmation explicite à
l'utilisateur (montre-lui le récapitulatif : client, lignes, total HT/TTC, date), puis relance
avec `--yes`. Ne passe jamais `--yes` de ta propre initiative.

## Règles de données de l'API

- Montants et quantités en **chaînes décimales** avec un point : `"1500.00"`. Prix unitaires **HT**.
- TVA en fraction : `"0.200"` pour 20 %, `"0.100"`, `"0.055"`, `"0.0"` pour exonéré
  (ajoute alors `vat_exemption` sur le document, ex. `"TVA non applicable, art. 293 B du CGI"`).
- Dates au format `AAAA-MM-JJ`. Périodes de recherche en `AAAA-MM` ou `AAAA-MM-JJ`.
- Ne transmets jamais `total`, `total_with_vat` ni le total d'une ligne : calculés côté serveur.
- Un devis ou une facture exige au moins une ligne dans `items`, chacune avec `position`,
  `title`, `quantity`, `unit_price`, `vat`. `product_id` recopie un produit du catalogue.
- En PATCH, si tu touches aux `items`, renvoie **la liste complète** : ligne sans `id` = ajout,
  avec `id` = modification, `{"id": X, "_destroy": "1"}` = suppression.
- Un client est **professionnel par défaut** ; pour un particulier envoie `"individual": true`.
  Sans `company_name`, le nom de société est dérivé de prénom + nom.
- Codes numériques (`payment_mode`, `pay_before`, `nature`, `quote_status`, `bill_type`…) :
  voir `references/values.md`. Ne devine pas un code.
- Champs libres `api_id` (entier) et `api_custom` (texte) : utiles pour stocker une référence
  externe (numéro de projet, ID Attio…) et la retrouver par `-p api_custom=…`.

## Workflows

### Trouver ou créer un client

```
fp.py get customers -p company=acme --fields id,company_name,short_name,email,city,pay_before
fp.py get customers -p last_name=durand -p mode=all --fields id,company_name,first_name,last_name,email
```
Recherche aussi par `-p email=…` quand le nom de société est incertain. Si aucun résultat,
**demande le SIRET avant de créer une société française** : ce compte le rend obligatoire
(422 « siret doit être renseigné »). Ne l'invente jamais et ne bascule pas en
`individual: true` pour contourner ; collecte-le dès la première question à l'utilisateur,
avec l'adresse de facturation. Puis crée le client et réutilise `id` :
```
fp.py post customers -d '{"company_name":"ACME SAS","email":"compta@acme.fr","street":"12 rue X","zip_code":"44000","city":"Nantes","country":"FR","siret":"…","vat_number":"FR…","pay_before":"30"}'
```
`pay_before` : « 30 jours » se traduit par `"30"` (à compter de la livraison) ; utilise la
variante `"30-inv"` seulement si l'utilisateur précise « à compter de la facture ».
`mode=archived` / `mode=all` pour retrouver un client archivé ; `POST customers/ID/archive`
pour masquer un client sans le supprimer. La suppression n'est possible que s'il n'a jamais
été facturé.

### Créer un devis, le faire accepter, le facturer

1. Vérifie le catalogue si l'utilisateur cite une prestation récurrente :
   `fp.py get products --fields id,ref,title,unit_price,vat`.
2. Crée le devis :
```
fp.py post quotes -d '{
  "customer_id": 123, "title": "Refonte site vitrine", "invoiced_on": "2026-09-03",
  "pay_before": "30", "language": "fr",
  "items": [
    {"position": 1, "title": "Conception et maquettes", "quantity": "1", "unit_price": "1800", "vat": "0.200"},
    {"position": 2, "title": "Intégration WordPress", "quantity": "5", "measure": "jour", "unit_price": "600", "vat": "0.200"},
    {"position": 3, "title": "Maintenance annuelle", "quantity": "1", "unit_price": "900", "vat": "0.200", "optional": true}
  ]
}' --fields id,quote_ref,total,total_with_vat,term_on,public_download_url
```
   Lignes spéciales : `"style": "title"` (titre en gras), `"comment"`, `"subtotal"`,
   `"new_page"`. `"optional": true` sort la ligne du total (bloc options en fin de devis).
   `rebate_percentage` applique une remise globale.
3. PDF : `fp.py pdf quotes ID -o devis.pdf` (ou `--proforma`). Envoi par mail :
   `fp.py post emails -p bill_id=ID -d '{"subject":"…","message":"…"}' --yes` (nécessite un
   SMTP configuré dans Facturation.PRO). Vérifie d'abord que la fiche client a un `email`,
   sinon passe `"to"` explicitement. Si un modèle d'envoi existe dans le compte, la doc ne
   précise pas si `subject`/`message` le remplacent ou s'y ajoutent : dis-le à l'utilisateur.
   Montre toujours le mail en `--dry-run` avant de demander le feu vert.
4. Accepté par le client : `fp.py patch quotes/ID -d '{"quote_status": 1}'` (9 = refusé).
5. Facturer : `fp.py post quotes/ID/invoice --yes` crée directement une facture finalisée
   reprenant toutes les lignes. Pour un acompte ou une facturation partielle, crée plutôt une
   facture brouillon à la main (ci-dessous) et laisse `amount_invoiced` / `fully_invoiced`
   suivre l'avancement sur le devis.

Suivi : `fp.py get quotes -p status=to_invoice --fields id,quote_ref,customer_identity,total,amount_invoiced`
liste les devis acceptés non soldés ; `status=pending` les devis en cours.

### Créer une facture (brouillon d'abord)

```
fp.py post invoices -p type_doc=draft -d '{"customer_id":123,"title":"Prestation septembre 2026","invoiced_on":"2026-09-03","pay_before":"30","items":[…]}'
```
Le brouillon reste modifiable et supprimable. Montre le récapitulatif à l'utilisateur, puis :
```
fp.py patch invoices/ID -p type_doc=final -d '{}' --yes
```
Après finalisation seuls `information`, `internal_note`, `pay_before`, `paid_on`,
`payment_mode`, `payment_ref`, `overdue_at` restent modifiables. Pour enregistrer dans
Facturation.PRO une facture émise ailleurs : `-p external=1` avec `external_ref` obligatoire.

### Encaisser

- Règlement total : `fp.py patch invoices/ID -d '{"paid_on":"2026-09-10","payment_mode":3,"payment_ref":"VIR-…"}'`
  (3 = virement, 2 = CB, 4 = chèque, 1 = PayPal, 8 = prélèvement).
- Plusieurs modes de règlement sur une même facture :
  `fp.py post invoices/ID/settlements -d '{"total":"500","payment_mode":4,"paid_on":"2026-09-10"}'`.
  Quand la somme des règlements atteint le total, la facture passe payée automatiquement.
  Ce n'est pas un système de paiement échelonné : pour un paiement en plusieurs fois, la
  méthode légale est acomptes + facture de solde.
- Annuler ou rembourser : `fp.py post invoices/ID/refund --yes` génère un avoir numéroté du
  montant total. Il n'y a pas d'avoir partiel par l'API.

### Relancer les impayés

```
fp.py get invoices -p bill_type=term --all --fields id,invoice_ref,customer_identity,total_with_vat,term_on,overdue_at --sum total_with_vat
fp.py get invoices -p bill_type=unpaid --all --fields id,invoice_ref,customer_identity,total_with_vat,term_on
```
`term` = échues à relancer, `unpaid` = toutes les non payées. Sans `bill_type`, la liste
mélange factures finalisées et brouillons (`draft: true`, `invoice_ref` vide) : filtre toujours. L'envoi via `emails` sur une
facture échue utilise automatiquement le modèle « Relance » du compte. Note la relance dans
`overdue_at` si l'utilisateur relance par un autre canal.

### Achats, notes de frais, fournisseurs

```
fp.py get suppliers -p company=ovh --fields id,company_name
fp.py post suppliers -d '{"company_name":"OVH","country":"FR"}'
fp.py post purchases -d '{"supplier_id":45,"title":"Hébergement sept. 2026","invoiced_on":"2026-09-01","total_with_vat":"71.99","vat_amount":"12.00","paid_on":"2026-09-01","payment_mode":2,"category_id":12,"nature":2}'
fp.py upload purchases ID ./facture-ovh.pdf
```
Un achat se saisit en **TTC + montant de TVA** (le HT est déduit). `category_id` est
optionnel : vérifie `get categories` (le compte peut n'en avoir aucune, la liste est alors
vide) et omets le champ plutôt que d'inventer un ID. L'upload du justificatif exige l'option
Gold (voir « Avant tout appel »). `payment_mode` des achats a
ses propres codes (20 = crédit fournisseur, 7 = compte courant d'associé). `draft: true` pour
un achat à compléter, `prepaid: true` pour un pré-paiement, `skip_export: true` pour l'exclure
de l'export comptable. Les catégories (`get categories`) ont un `status` : 1 ventes, 2 achats,
0 les deux. Les achats récurrents ne sont consultables qu'en lecture.

### Reporting (CA, TVA, encaissements)

- CA facturé sur une période : `fp.py get invoices -p period_type=billed -p period_start=2026-01 -p period_end=2026-06 -p bill_type=invoice --all --fields id,invoice_ref,invoiced_on,customer_identity,total,total_with_vat --sum total`
- Encaissements (période de paiement, défaut) : même requête sans `period_type`, avec `bill_type=paid`, `--sum total_with_vat`.
- Avoirs : `bill_type=refund` (totaux négatifs, à additionner au CA).
- Dépenses : `fp.py get purchases -p period_type=billed -p period_start=… --all --fields id,invoiced_on,supplier_identity,title,total,vat_amount,total_with_vat --sum total_with_vat`.

Le script imprime `{"count": N, "sum_champ": X}` sur stderr (`2>&1 | head -1` pour ne lire que
le total) : reprends ces chiffres dans ta réponse et précise la période et le périmètre (HT ou TTC, factures ou encaissements). Ne
produis pas de conclusion comptable ou fiscale à la place de l'utilisateur : donne les
chiffres, la requête utilisée et les limites (`bill_type=invoice` exclut les brouillons et les avoirs ; factures externes incluses ou
non).

## Erreurs fréquentes

| Symptôme | Cause probable |
|---|---|
| 401 | identifiant ou clé API incorrects, compte non activé |
| 403 sur `with_sepa=1` | clé non administrateur |
| 404 | mauvais FIRM_ID ou ID d'un autre type de ressource |
| 422 « can't be blank » sur items | ligne sans `title` / `unit_price` / `quantity`, ou devis sans aucune ligne |
| 422 sur PATCH facture | facture finalisée : seuls les champs de règlement/information sont modifiables |
| 422 « siret doit être renseigné » | société FR sans SIRET : demande-le à l'utilisateur |
| 422 sur DELETE customer | client déjà facturé : utilise `archive` |
| Exit 4, « réponse HTML au lieu de JSON » | fonctionnalité hors abonnement (pièces jointes = option Gold) |
| 501 | Content-Type manquant (le script le pose ; vérifie que tu n'appelles pas curl à la main) |
| 429 | quota : le script attend `Retry-After` ; réduis les pages ou filtre davantage |

## Références

- `references/api-reference.md` : tous les endpoints et filtres, ressource par ressource.
- `references/values.md` : tables de codes (`payment_mode`, `pay_before`, `nature`, statuts, `bill_type`).
- `references/facturation-pro-llms.txt` : documentation officielle complète (source :
  https://facturation.dev/llms.txt). Consulte-la pour un champ ou un cas non couvert ici,
  avec `grep -n` plutôt qu'en lisant tout le fichier.
