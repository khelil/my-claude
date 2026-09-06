# Compte-rendu — eval-3 : achat OVH 71,99 € TTC (with_skill)

Date d'exécution : 2026-09-03. Compte : Partikuls (firm 14198). Skill lu en entier avant toute action, puis `references/values.md` et `references/api-reference.md` (section purchases).

## Résultat

- Fournisseur OVH : **déjà existant**, réutilisé (id 29306), aucun doublon créé.
- Achat : **créé**, id **2195446** (serial_number 601), TTC 71.99 / TVA 12.00 / HT déduit 59.99, payé le 2026-09-01 par CB.
- Justificatif PDF : **non joint** — l'API renvoie HTTP 200 avec une page HTML « Cette fonctionnalité n'est pas disponible dans votre abonnement » (stockage de pièces jointes = option Gold, absente du compte ; `disk_used: 0, disk_free: 0` dans `account`). `files` et `file_assets` de l'achat restent vides.

Rien supprimé, aucune facture finalisée, aucun mail envoyé.

## Commandes fp.py exécutées, dans l'ordre

Toutes lancées depuis `/Users/khelil/.claude/skills/facturation-pro/`.

```
1. python3 scripts/fp.py account
2. python3 scripts/fp.py get suppliers -p company=ovh --fields id,company_name,short_name
3. python3 scripts/fp.py --help ; python3 scripts/fp.py upload --help ; python3 scripts/fp.py post --help
4. python3 scripts/fp.py get categories --all --fields id,title,status
   → []  (aucune catégorie définie, donc category_id omis)
5. python3 scripts/fp.py post purchases -d '{"supplier_id":29306,"title":"Hébergement OVH - septembre 2026","invoiced_on":"2026-09-01","total_with_vat":"71.99","vat_amount":"12.00","paid_on":"2026-09-01","payment_mode":2,"nature":2}'
6. python3 scripts/fp.py upload purchases 2195446 "/Users/khelil/.claude/skills/facturation-pro-workspace/iteration-1/facture-ovh-sept.pdf"
   → HTML « fonctionnalité non disponible dans votre abonnement », exit code 0
7. python3 scripts/fp.py upload purchases 2195446 "…/facture-ovh-sept.pdf" --dry-run
   (vérification de la requête : POST …/purchases/2195446/upload.json, multipart 509 octets)
8. python3 scripts/fp.py get purchases/2195446 --fields id,files,file_assets
   → files: [], file_assets: []
9. python3 scripts/fp.py get assets/purchases -p purchase_id=2195446
   → même page HTML (option Gold)
```

Hors fp.py : un snippet Python réutilisant `fp.load_config / build_url / multipart / call` pour lire le statut HTTP brut de l'upload → `HTTP 200`, `Content-Type: text/html; charset=utf-8`, 505 octets. (Cet appel a rejoué l'upload une fois de plus ; sans effet puisque la fonctionnalité est refusée.)

Choix de codes (depuis `references/values.md`) : `payment_mode: 2` = carte bancaire (achats), `nature: 2` = prestation de service. `category_id` omis car `get categories` renvoie une liste vide.

## IDs

| Objet | ID | Créé ? |
|---|---|---|
| Fournisseur OVH | 29306 | non (existant, réutilisé) |
| Achat | 2195446 | **oui** |
| Fichier joint | — | non (refusé par l'abonnement) |

## JSON de l'achat renvoyé par l'API (POST purchases)

```
Location: https://www.facturation.pro/firms/14198/purchases/2195446
```

```json
{
  "id": 2195446,
  "supplier_id": 29306,
  "supplier_identity": "OVH",
  "title": "Hébergement OVH - septembre 2026",
  "ref": null,
  "total_with_vat": "71.99",
  "vat_amount": "12.0",
  "total": "59.99",
  "currency": "EUR",
  "invoiced_on": "2026-09-01",
  "term_on": "2026-09-01",
  "paid_on": "2026-09-01",
  "payment_mode": 2,
  "payment_ref": null,
  "paid_in_main_currency": "71.99",
  "estimated_total_in_main_currency": "71.99",
  "draft": false,
  "reverse_charge": false,
  "prepaid": false,
  "notes": null,
  "skip_export": false,
  "serial_number": 601,
  "category_id": null,
  "accounting_entry": null,
  "accounting_asset": false,
  "asset_end_on": null,
  "asset_end_reason": null,
  "nature": 2,
  "created_at": "2026-09-03T17:22:35.718+02:00",
  "updated_at": "2026-09-03T17:22:35.718+02:00",
  "paid_in_euros": "71.99",
  "estimated_total_euro_paid": 71.99,
  "soft_deleted": false,
  "hard_delete_on": null,
  "files": [],
  "api_id": null,
  "api_custom": null,
  "file_assets": []
}
```

## Difficultés rencontrées

1. **Échec silencieux de `upload` (script).** L'API répond `200 text/html` quand l'option de stockage n'est pas souscrite. `cmd_upload` ne teste que `status >= 400`, puis `decode()` retombe sur le texte brut : le script imprime la page HTML sur stdout et sort avec le code 0. Un agent qui ne lit pas la sortie croit l'upload réussi. Suggestion : dans `cmd_upload` (et plus généralement dans `emit`/`decode`), traiter une réponse non-JSON (ou un `Content-Type` `text/html`) comme une erreur : exit code non nul, message sur stderr du type « Réponse HTML au lieu de JSON — fonctionnalité probablement absente de l'abonnement (option Gold requise pour les pièces jointes) », et éventuellement extraire le texte de la `<div class="note">`.

2. **Doc du skill (SKILL.md).** Le workflow « Achats » présente `fp.py upload purchases ID ./facture.pdf` comme une étape standard, sans signaler que les pièces jointes exigent l'option Gold. Le tableau « Erreurs fréquentes » ne couvre pas ce cas. Suggestion : ajouter une ligne « réponse HTML 200 "non disponible dans votre abonnement" → option Gold absente, vérifier `disk_free` dans `account` », et une note dans « Avant tout appel » : si `disk_free == 0` dans `account`, les `upload` échoueront.

3. **`category_id` dans l'exemple.** L'exemple `post purchases` du skill inclut `"category_id":12` comme s'il était attendu ; ici le compte n'a aucune catégorie (`get categories` → `[]`). Le champ est bien optionnel (achat créé sans), mais le skill pourrait le dire explicitement pour éviter un aller-retour ou une invention de code.

4. **Mineur.** `vat_amount` envoyé `"12.00"` revient `"12.0"` : simple normalisation côté serveur, pas un problème. Le `--dry-run` de `upload` masque bien l'Authorization et ne montre pas le corps binaire, ce qui est le comportement attendu.

Aucune erreur 4xx/5xx, pas de 429, pas d'option manquante bloquante en dehors du point 1.
