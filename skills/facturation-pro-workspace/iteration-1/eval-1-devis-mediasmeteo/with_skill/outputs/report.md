# Eval 1 — Devis Mediasmeteo (avec skill facturation-pro)

Date d'exécution : 2026-09-03 · Compte : firm 14198 « Partikuls » (SASU, Nantes)

## Résultat en une ligne

**Bloqué avant la création du client** : l'API renvoie `422 — siret doit être renseigné` pour une société française, et l'utilisateur n'a pas fourni de SIRET. Aucun enregistrement n'a été créé. Le devis est prêt (requête vérifiée en `--dry-run`) et sera créé dès que le SIRET est connu.

## Commandes fp.py exécutées, dans l'ordre

```
# 1. Vérification de la configuration
python3 scripts/fp.py account

# 2. Recherche du client (actifs, puis tous modes, puis recherche large)
python3 scripts/fp.py get customers -p company=mediasmeteo --fields id,company_name,short_name,email,city,pay_before
python3 scripts/fp.py get customers -p company=mediasmeteo -p mode=all --fields id,company_name,short_name,email,city,pay_before
python3 scripts/fp.py get customers -p company=meteo -p mode=all --fields id,company_name,short_name,email,city,pay_before
# → [] à chaque fois : le client n'existe pas

# 3. Catalogue (prestations récurrentes ?)
python3 scripts/fp.py get products --fields id,ref,title,unit_price,vat
# → 1 seul produit « Site Internet Multilingue » à 0.0 € : inutilisable

# 4. Création du client — dry-run puis POST réel
python3 scripts/fp.py post customers --dry-run -d '{"company_name":"Mediasmeteo","email":"contact@mediasmeteo.com","country":"FR","pay_before":"30"}'
python3 scripts/fp.py post customers -d '{"company_name":"Mediasmeteo","email":"contact@mediasmeteo.com","country":"FR","pay_before":"30"}' --fields id,company_name,short_name,email,country,pay_before,individual
# → 422 Unprocessable Entity : {"errors":{"siret":["doit être renseigné"]}}

# 5. Diagnostic : la règle est-elle générale ?
python3 scripts/fp.py get customers -p mode=missing_siret --fields id,company_name,country,siret,individual
# → 96 clients FR existants sans SIRET : l'obligation est un réglage récent du compte
#   (ou une règle liée à la facturation électronique), pas une règle historique de l'API

# 6. Devis — dry-run uniquement (customer_id à remplacer par l'ID du client une fois créé)
python3 scripts/fp.py post quotes --dry-run -d '{
  "customer_id": 0,
  "title": "Refonte du site WordPress",
  "invoiced_on": "2026-09-03",
  "pay_before": "30",
  "language": "fr",
  "items": [
    {"position": 1, "title": "Conception (maquettes, architecture, direction artistique)", "quantity": "3", "measure": "jour", "unit_price": "600", "vat": "0.200"},
    {"position": 2, "title": "Intégration WordPress", "quantity": "6", "measure": "jour", "unit_price": "600", "vat": "0.200"}
  ]
}' --fields id,quote_ref,total,total_with_vat,term_on,public_download_url
```

Hors fp.py (recherche du SIRET manquant, sans succès) : recherche web « Mediasmeteo SIRET » et lecture de
https://mediasmeteo.com/a-propos et https://mediasmeteo.com/mentions-legales.

## IDs créés

| Objet | ID | Statut |
|---|---|---|
| Client Mediasmeteo | — | **non créé** (422 siret) |
| Devis | — | **non créé** (dépend du client) |

Rien à nettoyer côté orchestrateur.

## Récapitulatif que je présenterais à l'utilisateur

> **Devis — Refonte du site WordPress — Mediasmeteo**
> Client : Mediasmeteo (société, contact@mediasmeteo.com) — *à créer*
> Date : 03/09/2026 · Langue : fr
>
> | # | Désignation | Qté | Unité | PU HT | Total HT |
> |---|---|---|---|---|---|
> | 1 | Conception (maquettes, architecture, direction artistique) | 3 | jour | 600,00 € | 1 800,00 € |
> | 2 | Intégration WordPress | 6 | jour | 600,00 € | 3 600,00 € |
>
> | | |
> |---|---|
> | **Total HT** | **5 400,00 €** |
> | TVA 20 % | 1 080,00 € |
> | **Total TTC** | **6 480,00 €** |
> | Conditions | 30 jours nets (`pay_before: "30"`) |
> | Échéance indicative | 03/10/2026 |
>
> Rien n'est envoyé : le devis serait créé en attente (`quote_status 0`), sans numéro légal, et
> l'envoi par mail (`post emails … --yes`) attendrait ton feu vert explicite.

Ce que j'aurais demandé à l'utilisateur avant de poursuivre :

1. **Le SIRET de Mediasmeteo** (obligatoire pour créer une société française sur ce compte). Point
   d'attention : le site mediasmeteo.com est édité par une **association loi 1901**
   (« Observatoire de la Transparence Médiatique », directeur de publication Fabrice Epelboin), pas
   par une société « Mediasmeteo ». Quelle entité juridique facturer, et avec quel SIRET ? La seule
   société homonyme trouvée au registre (MEDIAS WEATHER / AGATE METEO, SIREN 831 291 216,
   Raimbeaucourt) est une entreprise de météorologie sans rapport : je ne l'ai pas utilisée.
2. Adresse de facturation du client (absente des infos données ; non bloquante pour l'API).
3. Délai de paiement : « 30 jours » → `"30"` (30 jours nets à compter de la livraison, comme dans
   l'exemple du skill) ou `"30-inv"` (à compter de la facturation) ? J'ai retenu `"30"`.
4. Libellé de la ligne 1 (j'ai proposé « Conception (maquettes, architecture, direction
   artistique) ») et titre du devis (« Refonte du site WordPress »).

Actions non exécutées parce qu'elles exigent `--yes` (et qui n'étaient pas demandées) : envoi du
devis par mail, conversion en facture, suppression. Aucune n'a été tentée.

## Difficultés rencontrées avec le skill / le script

1. **SIRET obligatoire non documenté** (bloquant). `SKILL.md` §« Trouver ou créer un client » montre
   un exemple avec `siret` mais ne dit nulle part qu'il est **requis** pour une société FR ; la
   table « Erreurs fréquentes » ne couvre pas ce 422 ; `api-reference.md` et `llms.txt` le
   donnent simplement « modifiable ». Or 96 clients FR du compte sont sans SIRET, donc la règle
   est récente (réglage du compte ou exigence facturation électronique). À ajouter au skill :
   « Pour un client professionnel FR, `siret` est exigé (422 sinon) : demande-le à l'utilisateur
   avant de créer le client ; ne l'invente jamais, ne bascule pas en `individual: true` pour
   contourner. » Idéalement, faire du SIRET une info à collecter **dès la première question** à
   l'utilisateur pour éviter un aller-retour.
2. **Ambiguïté `pay_before`** : « paiement à 30 jours » correspond à `"30"` (livraison) ou
   `"30-inv"` (facturation). Le skill utilise `"30"` dans ses exemples sans expliquer le choix ;
   une ligne de guidance (« par défaut `30`, sauf si l'utilisateur précise "à compter de la
   facture" ») éviterait de deviner.
3. **`--dry-run` n'est pas un test** : il affiche la requête mais ne valide rien côté serveur ; le
   422 n'apparaît qu'au POST réel. Le skill présente `--dry-run` comme moyen de « montrer la
   requête avant une action qui engage » — c'est exact, mais il vaudrait la peine de préciser
   qu'il ne détecte pas les erreurs de validation.
4. **Recherche client** : la recherche `company=` est partielle et insensible à la casse (OK), mais
   il n'y a pas de filtre `email=` documenté dans SKILL.md alors que `api-reference.md` le liste ;
   utile pour retrouver un client par contact quand le nom de société diffère. À remonter dans le
   SKILL.md.
5. **Le script lui-même** : comportement conforme — préfixe firm, masquage de la clé dans le
   dry-run, message 422 lisible avec indice, `--fields` fonctionnel sur les listes. Rien à signaler.
6. Mineur : `get customers` sans `--all` affiche un avertissement de pagination sur stdout mélangé
   au JSON (« Pagination : {...} — ajoute --all… ») ; le sortir sur stderr faciliterait le pipe
   vers `jq`.
