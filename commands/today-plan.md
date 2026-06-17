---
description: Analyse les emails Attio récents, filtre le spam, et crée les tâches correspondantes dans Attio
argument-hint: "[nb_jours] (défaut: 1)"
allowed-tools: ToolSearch, mcp__attio__whoami, mcp__attio__search-emails-by-metadata, mcp__attio__get-email-content, mcp__attio__search-records, mcp__attio__list-records, mcp__attio__list-tasks, mcp__attio__create-task
---

# /today-plan — Plan du jour depuis la boîte mail (via Attio)

Objectif : passer en revue les emails synchronisés dans Attio sur une fenêtre récente, **écarter le bruit**, et **créer dans Attio les tâches actionnables**, rattachées au bon contact / société / deal et assignées à moi.

**Fenêtre d'analyse :** `$ARGUMENTS` jours en arrière. Si vide → **1 jour** (dernières 24 h).

## Procédure

### 0. Préparation
- Charge les schémas des outils Attio si besoin via `ToolSearch` (`select:mcp__attio__...`).
- `whoami` → récupère mon `workspace_member_id` (= assigné de toutes les tâches créées).

### 1. Récupérer les emails
- Calcule `sent_at_gt` = maintenant − (nb_jours) ; `sent_at_lt` = maintenant.
- `search-emails-by-metadata` avec ces bornes, `limit: 100`. Lis les `subject` / `summary` / `sender` / `recipients`.
- N'ouvre le **contenu complet** (`get-email-content`) **que** pour les emails ambigus dont l'action n'est pas claire depuis le résumé. Respecte la confidentialité : ne recopie pas le corps des emails dans le rapport.

### 2. Trier (signal vs bruit)
**À ÉCARTER (ne crée pas de tâche) :**
- Newsletters / contenus éditoriaux (domaines d'envoi `mail.`, `email.`, `news.`, `beehiiv`, `every.to`, ESP divers…).
- Démarchage commercial à froid (présence d'un lien de désinscription, pitch générique, « synergies », audit gratuit…).
- Reçus de commande, confirmations de paiement, notifications automatiques d'outils (logs WordPress, etc.).
- Accusés d'agenda (invitation acceptée/refusée, simple reprogrammation) → ce ne sont pas des tâches.
- Notifications système / formulaires automatisés (ex. demandes citoyennes routées vers d'autres services) où je suis seulement en copie.

**⚠️ PHISHING / SÉCURITÉ — ne crée pas de tâche, mais SIGNALE dans le rapport :**
- Expéditeur incohérent avec l'objet (ex. « Carte Vitale »/« périphérique de confiance » depuis un domaine étranger sans rapport), urgence suspecte, demandes d'identifiants. Ne clique jamais sur les liens. Signale aussi les anomalies de sécurité notables (pics de connexions échouées dans les logs).

**ACTIONNABLE (→ tâche) = un email qui attend une action de ma part :**
- Une réponse / relance attendue d'un client ou contact.
- Un retour client à traiter (modifs site, livrable, devis à préciser).
- Un RDV / call à caler.
- Un engagement ou une échéance explicite.

### 3. Rattacher
Pour chaque email actionnable :
- Résous la **société** et/ou la **personne** via `search-records` (par domaine de l'expéditeur ou nom). Réutilise la fiche existante ; ne crée pas de doublon. Si le contact n'est pas dans le CRM, crée quand même la tâche **sans lien** et précise-le.
- Si un **deal** existe pour cette société et que l'email s'y rapporte, lie la tâche au deal plutôt qu'à la société. Sinon lie à la société (ou à la personne).
- **Échéance** : déduis-la des indices du mail (« la semaine prochaine », « à la rentrée » = début septembre, « lundi », « avant le X »…). **N'invente pas de date** s'il n'y a aucun indice — laisse l'échéance vide.

### 4. Anti-doublon (vérification OBLIGATOIRE avant toute création)
Une tâche ne doit jamais faire doublon. Trois niveaux de contrôle :

1. **Dédoublonnage intra-run.** Regroupe d'abord les emails d'un même fil / même objet / même couple (société + action) : ils ne donnent qu'**une seule** tâche, pas une par message.

2. **Contre les tâches déjà dans Attio (ouvertes ET terminées récemment).** Pour chaque tâche candidate, une fois la fiche liée résolue, appelle `list-tasks` filtré sur cette fiche (`linked_record_object` + `linked_record_id`) et récupère les tâches **ouvertes** (`is_completed: false`) *et* celles **terminées sur la fenêtre d'analyse** (une tâche déjà faite ne doit pas réapparaître). Si la candidate n'a pas de fiche liée, fais une passe `list-tasks` sur mes tâches ouvertes (assignee = moi, paginer si besoin) pour comparer.

3. **Comparaison sémantique, pas seulement textuelle.** Il y a doublon si une tâche existante vise **la même action sur le même sujet** (ex. « relancer X sur la proposition », « traiter le retour de Y sur le site »), même si la formulation diffère. En cas de doute raisonnable sur une correspondance, **ne recrée pas**.

Toute candidate identifiée comme doublon est **écartée** (non créée) et reportée au §6 sous « Déjà suivi », avec le nom de la tâche existante.

### 5. Créer les tâches
- `create-task` pour chaque email actionnable à **forte confiance** : `content` clair et préfixé par le client (ex. « SYD — répondre à … »), `assignee_workspace_member_id` = moi, lien vers la fiche, échéance si déduite.
- Les cas **ambigus / borderline** : ne les crée pas, **liste-les** dans le rapport pour que je tranche.

### 6. Rapport (en français, concis)
1. **Tableau des tâches créées** : intitulé | rattachée à | échéance.
2. **Bruit écarté** : une ligne par catégorie (newsletters, démarchage, reçus, notifs système…) avec le nombre.
3. **⚠️ Alertes** : emails de phishing probables (expéditeur + objet) et anomalies de sécurité.
4. **À trancher** : les cas borderline non transformés en tâche.
5. **Déjà suivi** : candidates écartées car une tâche équivalente existe déjà (nom de la tâche existante).

Ne commits rien, ne supprime rien. Tu crées uniquement des tâches (action réversible). Si la connexion Attio est absente, signale-le et arrête-toi.
