---
description: Synchronise les justificatifs bancaires Partikuls — transactions Qonto sans justificatif → reçus d'achat trouvés dans Gmail (forward à Qonto) + factures de vente Facturation.PRO (rattachées à la transaction)
argument-hint: "[nb_jours] (défaut: 90)"
model: opus
allowed-tools: ToolSearch, Bash, Read, mcp__claude_ai_Qonto__list_bank_accounts, mcp__claude_ai_Qonto__list_transactions, mcp__claude_ai_Qonto__get_transaction, mcp__claude_ai_Qonto__list_transaction_attachments, mcp__claude_ai_Qonto__list_supplier_invoices, mcp__claude_ai_Qonto__request_attachment_upload, mcp__claude_ai_Qonto__upload_attachment, mcp__claude_ai_Gmail__search_threads, mcp__claude_ai_Gmail__get_thread, mcp__claude_ai_Gmail__get_message, mcp__claude_ai_Gmail__forward
---

# /qonto-sync — Justificatifs bancaires Partikuls

Objectif : pour chaque transaction Qonto **sans justificatif**, retrouver la pièce (reçu d'achat dans Gmail, facture de vente dans Facturation.PRO) et la faire parvenir à Qonto. En deux temps : **un plan que je valide, puis l'exécution**. Rien n'est envoyé ni rattaché avant mon feu vert.

**Fenêtre d'analyse :** `$ARGUMENTS` jours en arrière. Si vide → **90 jours**.

## Constantes du compte

- Compte Qonto principal : `fe5c4644-bf9c-4134-856b-6b612efa9dcc` (« Compte principal »). Le compte « Provisions » (`ecb2c551-8834-497d-88bc-cddb40940f3e`) n'a quasiment pas de mouvements : ne l'inclus que si le principal ne renvoie rien d'anormal et que je le demande.
- Adresse de dépôt des justificatifs Qonto : `receipts-djn5mvndlfdk@inbox.qonto.com`. Si un forward vers cette adresse est rejeté, retrouve l'adresse à jour dans un mail envoyé précédemment (`in:sent to:inbox.qonto.com`) et signale-moi l'écart.
- Facturation.PRO : skill `facturation-pro`, client `python3 ~/.claude/skills/facturation-pro/scripts/fp.py` (firm Partikuls, id 14198). Pas d'option Gold : aucun upload côté Facturation.PRO, seulement des téléchargements de PDF.
- Fichiers temporaires (PDF) : dans le scratchpad de session, jamais dans le vault.

## Procédure

### 0. Préparation
- Charge les schémas Qonto et Gmail via `ToolSearch` (`select:mcp__claude_ai_Qonto__…,mcp__claude_ai_Gmail__…`).
- Calcule `emitted_at_from` = aujourd'hui − nb_jours (ISO 8601, `T00:00:00Z`).
- Si l'un des connecteurs (Qonto, Gmail) est absent ou si `fp.py account` échoue : dis-le et arrête-toi. Ne bricole pas d'appel HTTP à la main.

### 1. Transactions Qonto sans justificatif
- `list_transactions` sur le compte principal avec `with_attachments: false`, `emitted_at_from`, `per_page: 100`, `sort_by: "emitted_at:desc"`. Pagine si `meta.next_page` n'est pas nul.
- La réponse est volumineuse et atterrit souvent dans un fichier : lis-la avec `jq` (Bash) plutôt qu'en entier. Colonnes utiles : `id`, `emitted_at`, `side`, `amount`, `currency`, `local_amount`, `local_currency`, `operation_type`, `label`, `clean_counterparty_name`, `reference`, `attachment_required`, `attachment_lost`.
- **Écarte** sans les traiter (mais compte-les dans le rapport) :
  - `attachment_required: false` — Qonto n'exige rien (URSSAF, DGFIP/SIE, virements vers moi-même, remboursements CPAM, prélèvements Malakoff/Humanis…).
  - `operation_type` ∈ {`qonto_fee`, `account_remuneration`} — Qonto génère lui-même ces pièces.
  - `attachment_lost: true` — j'ai déclaré la pièce perdue ; ne cherche pas, liste-les à part.
- Sépare ce qui reste en **débits** (achats → Gmail) et **crédits** (ventes → Facturation.PRO). Un crédit d'un tiers non client (ex. `GOCARDLESS SAS` = reversement, `ASP AGENCE COMPTABLE` = aide/subvention, `CPAM` = remboursement) reste dans les crédits mais sera probablement orphelin : signale-le.

### 1bis. Documents déjà reçus par Qonto mais en attente de revue
- `list_supplier_invoices` avec `filter_marked_as_read: false` (onglet « À vérifier » de Qonto) et, si utile, `filter_status: "to_review"`. Un reçu forwardé peut rester là sans être rattaché à la transaction tant que je n'ai pas confirmé s'il s'agit d'une facture à payer ou d'une preuve d'achat.
- Croise avec les débits sans justificatif (montant + fournisseur) : ceux qui ont déjà un document en attente vont dans **« Déjà transmis à Qonto »** avec la mention « à confirmer dans Qonto > Fournisseurs > À vérifier ». Ne les re-forwarde pas.

### 2. Débits → reçus d'achat dans Gmail

Pour chaque débit, cherche le mail qui contient le reçu ou la facture.

**Construire la requête.** Pars de `clean_counterparty_name` (sinon `label`), garde le mot le plus discriminant (`WP UMBRELLA` → `umbrella`, `OPENAI *CHATGPT SUBSCR` → `openai`, `AMZ DIGITAL FRA` → `amazon`, `Google CLOUD KBMH89` → `google cloud`). Fenêtre : `after:` = date d'émission − 5 jours, `before:` = date + 5 jours (format `YYYY/MM/DD`). Filtre sur les mots typiques d'un reçu :

```
umbrella (facture OR invoice OR receipt OR reçu OR payment) after:2026/09/03 before:2026/09/13
```

Si rien, élargis : retire les mots-clés de reçu, puis élargis la fenêtre à ±15 jours (les abonnements annuels ou les factures envoyées en décalé). Si toujours rien, la transaction est **orpheline**.

**Vérifier le match.** La recherche par mot-clé est bruyante (« openai » remonte aussi un reçu Groq qui cite ChatGPT) : **l'expéditeur fait foi**, pas le sujet. Ouvre le fil en `MINIMAL` (`get_thread`) ; ne passe en `PLAIN_TEXT` que si le montant n'apparaît pas dans le sujet/snippet. Un match est **sûr** si le domaine de l'expéditeur correspond au marchand **et** que le montant (`amount` en EUR, ou `local_amount` en devise pour les achats en USD/GBP) apparaît dans le mail. Sinon il est **probable** (marchand OK, montant absent ou différent) et va dans « À trancher ». Ne recopie jamais le corps des mails dans le rapport.

**Déjà envoyé ?** Si le fil contient déjà un message vers `inbox.qonto.com` (un forward précédent), ne le renvoie pas. La réponse automatique de `support@qonto.com` dans le fil dit où il en est :
- « automatiquement associée à cette/ces transaction(s) » → rattaché ; si la transaction apparaît quand même sans justificatif, c'est un décalage de synchronisation, signale-le.
- « Votre document a été ajouté pour que vous puissiez le vérifier » → en attente dans Qonto (cf. §1bis), à confirmer à la main.
Dans les deux cas : « Déjà transmis à Qonto ».
Pour repérer d'un coup tous les forwards récents : `in:sent to:inbox.qonto.com newer_than:<nb_jours>d`.

**Cas particuliers.**
- Plusieurs débits identiques (ex. deux paiements KRAKEN, deux Malakoff) : associe les reçus par date la plus proche ; en cas de doute, « À trancher ».
- Pas de reçu par mail (KRAKEN, DELIVEROO, TRANSAVIA, commerces physiques, Amazon Prime) : orphelin, avec l'indication du portail où télécharger la pièce quand tu la connais (Amazon → « Mes commandes », OpenAI → « Billing », Kraken → « Historique »). Tu ne vas pas la chercher toi-même sur le web.
- Achat en devise (USD) : le reçu affiche le montant en devise, `local_amount` ; le mail Qonto d'association parle aussi en devise. Compare sur `local_amount`.

### 3. Crédits → factures de vente Facturation.PRO

- Une seule requête pour toute la période (les listes renvoient tous les champs, ne fais pas un GET par facture) :

```
python3 ~/.claude/skills/facturation-pro/scripts/fp.py get invoices -p bill_type=invoice -p period_type=billed -p period_start=<AAAA-MM de (from − 60 j)> -p period_end=<AAAA-MM d'aujourd'hui> --all --fields id,invoice_ref,invoiced_on,customer_identity,total_with_vat,paid_on,payment_ref
```

  `period_start` remonte 60 jours avant la fenêtre : un client paie souvent une facture du mois précédent.
- Matching : `customer_identity` ≈ `clean_counterparty_name`/`label` du crédit (insensible à la casse, aux formes juridiques SAS/SASU/SARL et aux accents) **et** `total_with_vat` == `amount`. Une facture déjà `paid_on` non nul et déjà associée à un autre crédit ne sert qu'une fois.
- **Collectivités et organismes publics** : le virement arrive au nom du comptable public, pas du client (`SGC RAMBOUILLET` ou une « Trésorerie » paie pour la Commune de Jouars-Pontchartrain ; un `DGFIP`/`DDFIP` en crédit peut régler une facture d'une administration). Matche alors sur le **montant exact + facture non soldée** du client public le plus plausible, et classe-le **probable** (pas sûr) s'il y a plusieurs candidats au même montant.
- Un crédit qui règle **plusieurs factures d'un coup** (montant = somme de 2 ou 3 factures du même client) : rattache-les toutes à la transaction. Un client qui paie **deux factures par deux virements le même jour** (ex. LINKURIOUS 1440 + 1380) : matche chaque virement sur son montant exact.
- Pas de facture correspondante (montant orphelin, client inconnu de Facturation.PRO, `ASP AGENCE COMPTABLE` = subvention/aide, `GOCARDLESS` = reversement) : orphelin, à signaler.

### 4. Plan (STOP — attends ma validation)

Présente un plan groupé, puis **arrête-toi** :

1. **Achats → forward Gmail** : `date | marchand | montant | mail trouvé (expéditeur, sujet, date) | confiance (sûr / probable)`.
2. **Ventes → rattachement PDF** : `date | client | montant | facture(s) Facturation.PRO (ref, id)`.
3. **Déjà transmis à Qonto** (forward existant, pas d'action).
4. **Orphelins** : rien trouvé, avec la piste manuelle si connue.
5. **Écartés** : compte par motif (non exigé, frais Qonto, pièce perdue).

Je valide « go », « go achats », « go ventes », ou par ligne (« go sauf 3 et 7 »). Les lignes **probables** ne partent que si je les nomme explicitement.

### 5. Exécution (après validation seulement)

**Achats (forward).** Pour chaque ligne validée : `forward` avec `messageId` = le message du fil qui porte la pièce (celui du marchand, pas ma réponse), `to: ["receipts-djn5mvndlfdk@inbox.qonto.com"]`, `forwardText` vide. Un forward par transaction ; si un même mail couvre deux transactions (facture groupée), forward une seule fois et signale-le.

**Ventes (rattachement direct).** Pour chaque ligne validée, dans l'ordre :
1. `fp.py pdf invoices <id> -o <scratchpad>/<invoice_ref>.pdf` (les `/` d'une ref → `-`).
2. `request_attachment_upload` avec `file_name: "<invoice_ref>.pdf"`, `content_type: "application/pdf"`, `size_bytes` = taille réelle (`stat -f%z`). Récupère `upload_url` et `blob_ref` (valables 15 min : enchaîne tout de suite).
3. Envoi des octets (Bash) : `curl -sS -X PUT -H "Content-Type: application/pdf" --data-binary @<fichier> "<upload_url>"` — code HTTP 200 attendu, sinon arrête cette ligne et note l'erreur.
4. `upload_attachment` avec `blob_ref`, `target: "transaction"`, `transaction_id: <id Qonto>`.
5. Contrôle : `list_transaction_attachments` sur la transaction doit lister la pièce.

Ne mets **pas** à jour Facturation.PRO (`paid_on`) dans cette commande : c'est un autre geste, à faire sur demande.

### 6. Rapport final (en français, concis)

1. **Transmis** : tableau transaction | pièce | canal (forward / rattachement) | statut (ok / erreur).
2. **Déjà transmis à Qonto** (rappel : à vérifier dans Qonto > Documents si l'association n'est pas faite).
3. **Orphelins** : liste avec piste manuelle.
4. **À trancher** : matchs probables non exécutés.
5. **Erreurs** : upload refusé, forward rejeté, quota Facturation.PRO…

Ne supprime rien, ne modifie aucune transaction, ne touche à aucune facture. Les seules actions d'écriture sont le **forward de mails** et le **rattachement de PDF à une transaction** (réversible dans Qonto via `remove_transaction_attachment`, que cette commande n'utilise pas).
