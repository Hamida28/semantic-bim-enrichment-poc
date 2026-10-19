# Semantic BIM Enrichment PoC

[🇬🇧 English version](README.md)

## Vue d’ensemble

**Semantic BIM Enrichment** est une preuve de concept explorant la manière dont des données BIM structurées peuvent être reliées à des exigences techniques rédigées en langage naturel au moyen d’un workflow hybride associant IA et logique déterministe.

Le projet combine :

- l’extraction de données IFC avec IfcOpenShell ;
- la structure déterministe du BIM ;
- la recherche sémantique à l’aide d’embeddings ;
- le raisonnement contextuel avec un LLM ;
- la traçabilité des exigences ;
- la gestion explicite des informations manquantes ;
- la validation déterministe des propriétés IFC proposées ;
- des tests de régression automatisés.

L’objectif n’est **pas** de laisser un LLM décider de manière autonome si une maquette BIM est conforme.

Le PoC explore plutôt comment l’IA peut aider à :

- identifier les exigences techniques potentiellement pertinentes ;
- déterminer si les preuves BIM disponibles sont suffisantes ;
- distinguer un contexte d’applicabilité manquant de données requises manquantes ;
- proposer des propriétés IFC structurées ;
- conserver une validation déterministe et une validation humaine dans le workflow.

---

## Problème

Les exigences techniques d’un projet sont souvent exprimées en langage naturel, tandis que les maquettes BIM contiennent des informations structurées.

Par exemple :

> Toutes les portes situées sur des circulations protégées doivent disposer d’un degré de résistance au feu approprié documenté dans les données BIM.

Une maquette IFC peut contenir :

- la porte ;
- sa classe IFC ;
- les locaux qu’elle relie ;
- ses Property Sets ;
- des classifications architecturales ;

sans pour autant indiquer explicitement si le couloir associé constitue une **circulation protégée**.

Un système fiable doit donc distinguer :

- une exigence qui s’applique clairement ;
- une exigence qui ne s’applique clairement pas ;
- une exigence dont l’applicabilité ne peut pas encore être déterminée.

Le PoC utilise trois statuts :

```text
applicable
not_applicable
uncertain
```

Le statut `uncertain` est particulièrement important.

Une information BIM manquante ne doit pas être automatiquement interprétée comme une non-conformité.

---

## Architecture actuelle

```text
                        IFC MODEL
                            |
                            v
                      IFC extraction
                       IfcOpenShell
                            |
                            v
                    BIM object context
                            |
                +-----------+-----------+
                |                       |
                v                       v
        Structural IFC family     Retrieval query
           identification         + semantic hints
                |                       |
                |                       v
                |                  Embeddings
                |                       |
                +-----------+-----------+
                            |
                            v
                     Hybrid retrieval
                            |
                            v
                  Candidate requirements
                            |
                            v
                      LLM reasoning
                            |
               +------------+-------------+
               |            |             |
           applicable    uncertain    not_applicable
               |
               v
          IFC property proposal
               |
               v
            IfcOpenShell
     deterministic property validation
               |
               v
          Human validation
```

L’architecture sépare volontairement les tâches qui bénéficient de l’IA de celles qui peuvent être vérifiées de manière déterministe.

---

## Retrieval hybride

### Approche initiale

La première version reposait principalement sur la similarité sémantique entre les descriptions des objets BIM et les exigences techniques.

Sur un jeu d’exigences simple, le retrieval obtenait :

```text
Recall@1: 8/8 — 100%
```

Cependant, le jeu de données était petit et les exigences relativement faciles à distinguer.

Un score parfait sur ce jeu de données ne démontrait donc pas la robustesse du système.

### Stress test avec des hard negatives

Des exigences sémantiquement proches ont été introduites volontairement afin de rendre le retrieval plus difficile.

Par exemple :

```text
External windows ...
Internal windows ...

External doors ...
Internal doors connecting rooms to circulation areas ...

Floor slabs in technical areas ...
Floor slabs in residential areas ...
```

Le stress test de retrieval a produit :

```text
Recall@1: 4/8 — 50.00%
Recall@2: 5/8 — 62.50%
Recall@3: 8/8 — 100.00%
```

Cet échec était utile.

Il a montré que les embeddings étaient sollicités pour redécouvrir une information déjà explicitement disponible dans l’IFC.

Par exemple, la maquette BIM sait déjà si un objet est un :

```text
IfcDoor
IfcWindow
IfcWall
IfcSlab
```

Il n’y a donc aucune raison de dépendre uniquement de la similarité sémantique pour déterminer cette compatibilité structurelle.

### Amélioration de l’architecture

L’architecture de retrieval a donc été modifiée pour combiner :

```text
IFC structural filtering
        +
semantic ranking
```

Par exemple :

```text
IfcWindow
    |
    v
keep Window-compatible requirements
    |
    v
semantic ranking between
External Window / Internal Window rules
```

Le filtre déterministe élimine les exigences structurellement incompatibles avant le classement sémantique.

Les embeddings sont ensuite utilisés uniquement là où la comparaison sémantique apporte réellement de la valeur.

---

## Classification des exigences

Les exigences sont classées par famille d’entités IFC avant le filtrage structurel.

Exemple :

```text
"External windows must include acoustic-performance information..."

→ IfcWindow
```

La V1 actuelle utilise un classificateur déterministe simple et transparent basé sur des mots-clés.

Évaluation contrôlée :

```text
9 / 9 requirement classifications correct
```

Ce résultat ne concerne que le jeu de données contrôlé actuel.

Le classificateur est volontairement simple et n’est **pas** présenté comme un classificateur universel d’exigences en langage naturel.

Les formulations plus ambiguës restent un sujet de travail futur.

---

## Retrieval et raisonnement : deux responsabilités distinctes

Une décision centrale de l’architecture consiste à séparer :

```text
retrieval
```

de :

```text
reasoning
```

Le retrieval répond à la question :

> Quelles exigences doivent être examinées pour cet objet BIM ?

Le raisonnement répond à la question :

> À partir des preuves BIM disponibles, que peut-on conclure pour chacune de ces exigences ?

Une exigence retrouvée par le retrieval n’est donc qu’une **candidate**.

Elle n’est jamais considérée automatiquement comme applicable.

Cette distinction est particulièrement importante car plusieurs exigences peuvent légitimement concerner le même objet BIM.

---

## Raisonnement du LLM

Pour chaque exigence récupérée, le LLM renvoie une sortie structurée proche de :

```json
{
  "source_chunk_id": "REQ-001",
  "requirement": "...",
  "status": "uncertain",
  "reason": "...",
  "missing_context": [],
  "missing_required_data": [],
  "confidence": "medium",
  "suggested_property": "Pset_DoorCommon.FireRating",
  "suggested_value": null
}
```

### Définition des statuts

#### `applicable`

Les preuves BIM disponibles confirment les conditions qui rendent l’exigence applicable.

#### `not_applicable`

Les preuves BIM disponibles montrent clairement que l’exigence ne concerne pas l’objet.

#### `uncertain`

L’exigence peut concerner l’objet, mais certaines informations nécessaires pour déterminer son applicabilité sont manquantes.

---

## Contexte manquant vs données requises manquantes

Le projet distingue explicitement deux catégories différentes d’informations manquantes.

### `missing_context`

Informations nécessaires pour déterminer si l’exigence s’applique.

Exemple :

```text
Is this corridor a protected circulation route?
```

### `missing_required_data`

Informations nécessaires pour évaluer ou satisfaire l’exigence une fois ses conditions d’applicabilité établies.

Exemple :

```text
What fire-resistance rating is required?
```

Cette distinction évite qu’une donnée BIM manquante soit interprétée trop rapidement comme une non-conformité.

---

## Preuves utilisées pour le retrieval vs preuves utilisées pour le raisonnement

Le système distingue également les informations utilisées pour améliorer le retrieval des informations utilisées comme preuves par le modèle de raisonnement.

Par exemple, l’IFC source contient la valeur ArchiCAD allemande :

```text
Außenwände
```

Pour le retrieval sémantique, la requête peut être enrichie avec :

```text
Semantic layer meaning: external walls
```

Cela aide les embeddings à fonctionner malgré une terminologie hétérogène ou multilingue.

Cependant, cette interprétation ajoutée n’est **pas transmise au LLM comme une donnée BIM d’origine**.

Le contexte utilisé pour le raisonnement conserve la valeur source :

```text
Außenwände
```

L’architecture distingue donc :

```text
retrieval-oriented semantic normalization
```

de :

```text
source BIM evidence
```

Cela réduit le risque qu’une transformation introduite uniquement pour améliorer la recherche soit silencieusement utilisée comme preuve de conformité.

---

## Suggestions de propriétés IFC

Lorsqu’une information est manquante, le LLM peut proposer une propriété IFC standard.

Exemple :

```text
Pset_DoorCommon.FireRating
```

Cette suggestion du LLM n’est pas automatiquement considérée comme fiable.

Une deuxième étape déterministe la vérifie avec IfcOpenShell.

---

## Validation déterministe des propriétés IFC

Pour chaque propriété IFC proposée, le système vérifie :

```text
Does the Property Set exist?

Does the property exist inside that Property Set?

Is the Property Set applicable to this IFC class?
```

Exemple de proposition valide :

```text
Pset_DoorCommon.FireRating
→ valid: true
```

Exemple de proposition volontairement invalide :

```text
Pset_DoorCommon.MadeUpRating
→ valid: false
```

La propriété invalide est rejetée parce que `MadeUpRating` n’existe pas dans `Pset_DoorCommon`.

La suggestion initiale du LLM est conservée avec le résultat de sa validation.

Cela crée une distinction traçable entre :

```text
LLM proposal
```

et :

```text
deterministically validated IFC property
```

Un résultat `valid: true` signifie que le chemin de propriété IFC est structurellement valide pour le schéma IFC et la classe sélectionnés.

Cela ne signifie **pas** que la propriété proposée constitue automatiquement la bonne interprétation réglementaire de l’exigence.

---

## Stratégie d’évaluation

Le projet évalue séparément plusieurs composantes du système plutôt que de s’appuyer sur un unique chiffre global de précision.

---

### 1. Benchmark contrôlé du raisonnement

Le premier jeu de données contrôlé évaluait les trois statuts de raisonnement :

```text
applicable
uncertain
not_applicable
```

Résultat :

```text
32 / 32 expected decisions matched
```

Répartition :

```text
applicable:      4 / 4
uncertain:       4 / 4
not_applicable: 24 / 24
```

Ces résultats ne concernent que le jeu de données contrôlé utilisé pour cette évaluation.

Ils ne sont **pas** présentés comme une mesure de précision en conditions réelles.

---

### 2. Benchmark initial du retrieval

Sur le premier jeu d’exigences simple :

```text
Recall@1: 8 / 8
```

Ce résultat a volontairement été mis à l’épreuve plutôt que considéré comme une preuve de robustesse.

---

### 3. Stress test du retrieval

Après l’introduction de hard negatives sémantiquement proches :

```text
Recall@1: 4 / 8 — 50.00%
Recall@2: 5 / 8 — 62.50%
Recall@3: 8 / 8 — 100.00%
```

La baisse du Recall@1 a mis en évidence une faiblesse du retrieval reposant uniquement sur les embeddings.

Cette expérience a directement motivé le passage à un retrieval hybride combinant :

```text
IFC structural filtering
+
semantic ranking
```

Le stress test ayant échoué est volontairement conservé dans la méthodologie du projet car il documente l’évolution de l’architecture à partir d’une faiblesse réellement observée.

---

### 4. Évaluation du classificateur d’exigences

Le classificateur déterministe d’exigences a été évalué sur le jeu d’exigences utilisé pour le stress test.

Résultat :

```text
9 / 9 classifications correct
```

Là encore, ce résultat concerne uniquement ce jeu de test contrôlé.

---

### 5. Test du validateur de propriétés IFC

Le validateur déterministe de propriétés IFC a correctement accepté des propriétés IFC4 standard valides telles que :

```text
Pset_DoorCommon.FireRating
Pset_DoorCommon.AcousticRating
Pset_WallCommon.AcousticRating
Pset_WallCommon.FireRating
Pset_SlabCommon.FireRating
Pset_SlabCommon.AcousticRating
```

et rejeté la propriété volontairement invalide :

```text
Pset_DoorCommon.MadeUpRating
```

---

### 6. Suite de régression end-to-end de la V1

L’architecture actuelle est couverte par une suite automatisée de régression end-to-end sur :

```text
IfcDoor
IfcWindow
IfcWallStandardCase
IfcSlab
```

Le test de régression vérifie :

- les exigences conservées après le filtrage structurel ;
- les exigences effectivement analysées par le LLM ;
- les statuts de raisonnement attendus ;
- la validation déterministe des propriétés IFC éventuellement proposées.

Résultat actuel :

```text
Total checks: 26
PASS: 26
FAIL: 0

Success rate: 100.00%

NO REGRESSION DETECTED
```

Cela signifie que la V1 actuelle passe tous les contrôles définis dans sa suite de régression contrôlée.

Cela ne signifie **pas** qu’elle atteint 100 % de précision sur des projets BIM, spécifications, réglementations ou modèles IFC jamais vus auparavant.

---

## Exemple de workflow

Considérons une porte intérieure IFC reliant une salle de bain à un couloir :

```text
IfcDoor
Bad ↔ Flur
```

La couche de retrieval hybride peut conserver :

```text
REQ-001
Doors on protected circulation routes
→ fire resistance

REQ-006
Internal doors connecting rooms to circulation areas
→ acoustic performance

REQ-007
External doors
→ thermal performance
```

La couche de raisonnement peut ensuite produire :

```text
REQ-001 → uncertain

The door connects to a hallway,
but the model does not establish whether
that hallway is a protected circulation route.
```

```text
REQ-006 → uncertain

The door is internal and connects to a hallway,
but the project acoustic requirement is unknown.
```

```text
REQ-007 → not_applicable

The available BIM evidence identifies
the object as an internal door.
```

Pour l’information de résistance au feu manquante, le LLM peut proposer :

```text
Pset_DoorCommon.FireRating
```

IfcOpenShell vérifie ensuite indépendamment si cette propriété existe et si elle est applicable à `IfcDoor`.

---

## Périmètre actuel de la V1

La version actuelle comprend :

- extraction d’un modèle IFC4 avec IfcOpenShell ;
- extraction des objets BIM par GlobalId ;
- extraction des propriétés BIM ;
- génération d’une requête BIM sémantique ;
- normalisation sémantique orientée retrieval ;
- génération séparée des preuves utilisées pour le raisonnement ;
- découpage des exigences techniques ;
- séparation des exigences objet/processus ;
- classification des exigences par famille IFC ;
- filtrage structurel IFC ;
- classement sémantique basé sur les embeddings ;
- raisonnement contextuel avec un LLM ;
- traçabilité des sources des exigences ;
- classification `applicable / uncertain / not_applicable` ;
- identification du contexte d’applicabilité manquant ;
- identification des données requises manquantes ;
- suggestion de propriétés IFC ;
- validation déterministe des propriétés IFC ;
- évaluation contrôlée du raisonnement ;
- évaluation du retrieval ;
- stress test du retrieval ;
- évaluation du classificateur d’exigences ;
- test du validateur de propriétés ;
- tests de régression end-to-end automatisés.

---

## Limites actuelles

Ce projet est un PoC expérimental, et non un système de conformité destiné à la production.

Les limites actuelles comprennent :

- un seul modèle IFC de démonstration ;
- de petits jeux d’exigences synthétiques ;
- une couverture limitée des familles d’entités IFC ;
- un classificateur d’exigences simple basé sur des mots-clés ;
- aucun jeu de données réglementaire de production ;
- aucune décision automatisée de conformité réglementaire ;
- aucun benchmark annoté à grande échelle ;
- aucune base de données vectorielle ;
- les embeddings sont actuellement recalculés lors du retrieval ;
- la terminologie BIM multilingue n’est que partiellement normalisée ;
- aucun pipeline général d’ingestion de PDF ou de documents ;
- aucune réécriture automatique dans l’IFC ;
- aucune intégration avec un viewer BIM ;
- aucun modèle de provenance à l’échelle production ;
- aucun pipeline de génération IDS ;
- aucune validation IDS intégrée dans le workflow actuel.

La validation humaine reste volontairement une partie du processus.

---

## Travaux futurs

Les prochaines évolutions possibles comprennent :

- l’ingestion de spécifications réelles de projets ;
- le traitement de PDF et d’autres documents ;
- une normalisation multilingue plus robuste ;
- la prise en charge de familles IFC supplémentaires ;
- des jeux d’évaluation annotés plus importants ;
- la mise en cache des embeddings ou un stockage vectoriel ;
- une classification des exigences plus robuste ;
- la provenance des exigences à travers plusieurs documents ;
- l’intégration IDS ;
- la génération d’exigences structurées après validation humaine ;
- la validation déterministe IFC/IDS ;
- l’intégration d’un viewer BIM ;
- l’enrichissement contrôlé de l’IFC et le write-back ;
- l’exécution des tests de régression dans une CI.

Une architecture future possible serait :

```text
Project documents
       |
       v
RAG / semantic interpretation
       |
       v
Structured requirement proposal
       |
       v
Human validation
       |
       v
IDS
       |
       v
Deterministic IFC validation
```

L’interprétation par IA et la validation déterministe de conformité restent des responsabilités distinctes.

---

## Stack technologique

```text
Python
IfcOpenShell
OpenAI API
Embeddings
NumPy
IFC4
```

---

## Structure du projet

Le code source est organisé par responsabilité afin de séparer clairement l’architecture V1 actuelle, les outils d’évaluation, les scripts de diagnostic et les versions expérimentales antérieures.

```text
data/
├── model.ifc
├── spec.txt
└── spec_stress.txt

src/
├── __init__.py
│
├── core/
│   ├── __init__.py
│   ├── ifc_extract.py
│   ├── ifc_property_validator.py
│   └── requirement_classifier.py
│
├── rag/
│   ├── __init__.py
│   ├── rag_retriever.py
│   └── rag_enrich.py
│
├── evaluation/
│   ├── __init__.py
│   ├── evaluate_pipeline_regression.py
│   ├── evaluate_reasoning.py
│   ├── evaluate_requirement_classifier.py
│   ├── evaluate_retrieval.py
│   └── evaluate_retrieval_stress.py
│
├── diagnostics/
│   ├── __init__.py
│   ├── inspect_candidates.py
│   ├── list_candidates.py
│   ├── test_property_validator.py
│   ├── test_rag.py
│   ├── test_rag_stress.py
│   ├── test_retrieval.py
│   └── test_synthetic_cases.py
│
└── legacy/
    ├── __init__.py
    ├── baseline_enrich.py
    ├── llm_enrich.py
    └── main.py
```

### Rôle des modules

- `core/` contient les utilitaires BIM/IFC déterministes utilisés dans l’ensemble du projet : extraction IFC, classification des exigences par famille IFC et validation des propriétés IFC.

- `rag/` contient le pipeline actuel de retrieval sémantique et de raisonnement LLM de la V1.

- `evaluation/` contient les benchmarks automatisés et les tests de régression utilisés pour mesurer le retrieval, le raisonnement, la classification et le comportement end-to-end.

- `diagnostics/` contient les scripts exploratoires et d’inspection manuelle permettant de comprendre les objets BIM, les exigences retrouvées, les cas synthétiques et le comportement des stress tests.

- `legacy/` conserve les étapes antérieures du PoC : la baseline déterministe par mots-clés, la première approche d’enrichissement reposant directement sur le LLM et le point d’entrée historique en ligne de commande.

Conserver ces implémentations antérieures permet de rendre explicite l’évolution de l’architecture :

```text
deterministic keyword baseline
        ↓
LLM-only enrichment
        ↓
hybrid RAG
        ↓
deterministic IFC validation
        ↓
automated regression testing
```

Certains fichiers locaux d’entrée ou de sortie peuvent être exclus du contrôle de version.

---

## Exécution des principaux tests

Activez l’environnement Python puis exécutez le module souhaité depuis la racine du dépôt.

### Évaluation contrôlée du raisonnement

```bash
python -m src.evaluation.evaluate_reasoning
```

### Évaluation du retrieval

```bash
python -m src.evaluation.evaluate_retrieval
```

### Stress test du retrieval

```bash
python -m src.evaluation.evaluate_retrieval_stress
```

### Évaluation du classificateur d’exigences

```bash
python -m src.evaluation.evaluate_requirement_classifier
```

### Diagnostic du validateur de propriétés IFC

```bash
python -m src.diagnostics.test_property_validator
```

### Suite de régression end-to-end de la V1

```bash
python -m src.evaluation.evaluate_pipeline_regression
```

Résultat de régression actuel attendu :

```text
Total checks: 26
PASS: 26
FAIL: 0
Success rate: 100.00%

NO REGRESSION DETECTED
```

La suite de régression a été relancée après la réorganisation des modules Python par responsabilité et a de nouveau retourné `26 / 26 PASS`, confirmant que ce refactoring n’a pas modifié le comportement attendu du pipeline V1 contrôlé.

---

## Environnement

Créez un fichier `.env` local :

```env
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-6-luna
```

Le fichier `.env` doit rester local et ne doit pas être commité.

Installez les dépendances avec :

```bash
pip install -r requirements.txt
```

---

## Jalon actuel

```text
V1

Hybrid BIM retrieval
+
contextual LLM reasoning
+
traceable uncertainty
+
deterministic IFC property validation
+
automated regression testing
```

Le projet explore l’intersection entre :

```text
BIM
IFC / openBIM
software engineering
QA automation
information retrieval
LLMs
AI-assisted AEC workflows
```

---

## Avertissement

Les exigences techniques utilisées dans cette démonstration sont synthétiques et ne constituent pas des exigences réglementaires.

Ce projet ne doit pas être utilisé pour établir la conformité à un code du bâtiment, à des exigences de sécurité incendie, acoustiques, thermiques, d’accessibilité ou à toute autre réglementation.

Le système actuel est une preuve de concept de recherche et d’apprentissage destinée à explorer le BIM, le retrieval d’information, le raisonnement par IA, la validation déterministe et les méthodologies de qualité logicielle.
