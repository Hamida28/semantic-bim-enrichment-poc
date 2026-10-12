# Semantic BIM Enrichment PoC

[🇬🇧 English version](README.md)

## Présentation

**Semantic BIM Enrichment** est un proof of concept qui explore comment connecter des données BIM structurées à des exigences techniques rédigées en langage naturel grâce à un workflow hybride utilisant l’IA.

Le projet combine :

- l’extraction de données IFC avec IfcOpenShell ;
- la structure déterministe du BIM ;
- la recherche sémantique par embeddings ;
- le raisonnement contextuel avec un LLM ;
- la traçabilité des exigences ;
- la gestion explicite des informations manquantes ;
- la validation déterministe des propriétés IFC proposées ;
- des tests automatisés de régression.

L’objectif n’est **pas** de laisser un LLM décider de manière autonome si une maquette BIM est conforme.

Le PoC explore plutôt comment l’IA peut aider à :

- identifier les exigences techniques potentiellement pertinentes ;
- déterminer si les informations BIM disponibles sont suffisantes ;
- distinguer le contexte d’applicabilité manquant des données requises manquantes ;
- proposer des propriétés IFC structurées ;
- conserver une validation déterministe et humaine dans le workflow.

---

## Problème étudié

Les exigences techniques d’un projet sont souvent exprimées en langage naturel, tandis que les maquettes BIM contiennent des informations structurées.

Par exemple :

> All doors on protected circulation routes must have an appropriate fire-resistance rating documented in the BIM data.

Une maquette IFC peut contenir :

- la porte ;
- sa classe IFC ;
- les pièces auxquelles elle est reliée ;
- ses Property Sets ;
- ses classifications architecturales ;

tout en n’indiquant pas explicitement si le couloir associé est une **circulation protégée**.

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
                     MAQUETTE IFC
                          |
                          v
                   Extraction IFC
                    IfcOpenShell
                          |
                          v
                  Contexte objet BIM
                          |
              +-----------+-----------+
              |                       |
              v                       v
     Identification famille      Requête retrieval
       IFC structurelle         + enrichissement sémantique
              |                       |
              |                       v
              |                   Embeddings
              |                       |
              +-----------+-----------+
                          |
                          v
                  Retrieval hybride
                          |
                          v
                Exigences candidates
                          |
                          v
                  Raisonnement LLM
                          |
             +------------+-------------+
             |            |             |
        applicable     uncertain    not_applicable
             |
             v
        Proposition de
        propriété IFC
             |
             v
          IfcOpenShell
     validation déterministe
             |
             v
        Validation humaine
```

L’architecture sépare volontairement les tâches qui bénéficient de l’IA de celles qui peuvent être vérifiées de manière déterministe.

---

## Retrieval hybride

### Approche initiale

La première version reposait principalement sur la similarité sémantique entre la description d’un objet BIM et les exigences techniques.

Sur un premier jeu d’exigences simple, le retrieval obtenait :

```text
Recall@1: 8/8 — 100 %
```

Cependant, le dataset était petit et les exigences relativement faciles à distinguer.

Un score parfait sur ce dataset ne démontrait donc pas la robustesse du système.

### Stress test avec des hard negatives

Des exigences volontairement proches sémantiquement ont été ajoutées afin de rendre la recherche plus difficile.

Exemples :

```text
External windows ...
Internal windows ...

External doors ...
Internal doors connecting rooms to circulation areas ...

Floor slabs in technical areas ...
Floor slabs in residential areas ...
```

Le stress test a produit :

```text
Recall@1: 4/8 — 50,00 %
Recall@2: 5/8 — 62,50 %
Recall@3: 8/8 — 100,00 %
```

Cet échec a été utile.

Il a montré que les embeddings essayaient de redécouvrir des informations déjà disponibles explicitement dans l’IFC.

Par exemple, la maquette BIM sait déjà si un objet est un :

```text
IfcDoor
IfcWindow
IfcWall
IfcSlab
```

Il n’est donc pas nécessaire de dépendre uniquement de la similarité sémantique pour déterminer cette compatibilité structurelle.

### Amélioration architecturale

L’architecture de retrieval a donc évolué vers :

```text
filtrage structurel IFC
        +
classement sémantique
```

Par exemple :

```text
IfcWindow
    |
    v
conserver les exigences compatibles Window
    |
    v
classement sémantique entre
External Window / Internal Window
```

Le filtre déterministe retire les exigences structurellement incompatibles avant le classement sémantique.

Les embeddings sont ensuite utilisés là où la comparaison sémantique apporte réellement de la valeur.

---

## Classification des exigences

Les exigences sont classées par famille d’entités IFC avant le filtrage structurel.

Exemple :

```text
"External windows must include acoustic-performance information..."

→ IfcWindow
```

La V1 actuelle utilise un classifieur baseline déterministe et transparent basé sur des mots-clés.

Évaluation contrôlée :

```text
9 / 9 classifications correctes
```

Ce résultat concerne uniquement le dataset contrôlé actuel.

Le classifieur est volontairement simple et n’est **pas** présenté comme un classifieur universel d’exigences techniques en langage naturel.

Les formulations plus ambiguës restent un sujet de travail futur.

---

## Retrieval et raisonnement : deux responsabilités distinctes

Une décision centrale du projet consiste à séparer :

```text
retrieval
```

et :

```text
reasoning
```

Le retrieval répond à :

> Quelles exigences doivent être examinées pour cet objet BIM ?

Le raisonnement répond à :

> À partir des informations BIM disponibles, que peut-on conclure pour chacune de ces exigences ?

Une exigence récupérée par le moteur de recherche est donc uniquement une **candidate**.

Elle n’est jamais automatiquement considérée comme applicable.

Cette distinction est particulièrement importante parce que plusieurs exigences peuvent légitimement concerner un même objet BIM.

---

## Raisonnement par LLM

Pour chaque exigence récupérée, le LLM retourne une structure de ce type :

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

Les données BIM disponibles confirment les conditions qui rendent l’exigence applicable.

#### `not_applicable`

Les données BIM disponibles montrent clairement que l’exigence ne concerne pas cet objet.

#### `uncertain`

L’exigence peut concerner l’objet, mais certaines informations nécessaires pour déterminer son applicabilité sont manquantes.

---

## Contexte manquant vs données requises manquantes

Le projet sépare explicitement deux types d’informations manquantes.

### `missing_context`

Informations nécessaires pour déterminer si l’exigence s’applique.

Exemple :

```text
Ce couloir est-il une circulation protégée ?
```

### `missing_required_data`

Informations nécessaires pour vérifier ou satisfaire l’exigence une fois que les conditions d’applicabilité sont établies.

Exemple :

```text
Quelle résistance au feu est exigée ?
```

Cette distinction évite qu’une donnée BIM absente soit trop rapidement interprétée comme une non-conformité.

---

## Données utilisées pour le retrieval vs preuves utilisées pour le raisonnement

Le système sépare également les informations utilisées pour améliorer le retrieval de celles utilisées comme preuves par le modèle de raisonnement.

Par exemple, la source IFC contient une valeur ArchiCAD en allemand :

```text
Außenwände
```

Pour le retrieval sémantique, la requête peut être enrichie avec :

```text
Semantic layer meaning: external walls
```

Cela aide les embeddings à fonctionner malgré une terminologie hétérogène ou multilingue.

Cependant, cette interprétation ajoutée n’est **pas transmise au LLM comme une donnée BIM originale**.

Le contexte de raisonnement conserve la valeur source :

```text
Außenwände
```

L’architecture distingue donc :

```text
normalisation sémantique destinée au retrieval
```

de :

```text
preuve BIM source
```

Cela réduit le risque qu’une transformation introduite uniquement pour améliorer la recherche devienne silencieusement une preuve de conformité.

---

## Suggestions de propriétés IFC

Lorsqu’une information est manquante, le LLM peut proposer une propriété IFC standard.

Exemple :

```text
Pset_DoorCommon.FireRating
```

La suggestion du LLM n’est pas automatiquement considérée comme correcte.

Une seconde étape déterministe la vérifie avec IfcOpenShell.

---

## Validation déterministe des propriétés IFC

Pour chaque propriété IFC proposée, le système vérifie :

```text
Le Property Set existe-t-il ?

La propriété existe-t-elle dans ce Property Set ?

Le Property Set est-il applicable à cette classe IFC ?
```

Exemple de proposition valide :

```text
Pset_DoorCommon.FireRating
→ valid: true
```

Exemple volontairement invalide :

```text
Pset_DoorCommon.MadeUpRating
→ valid: false
```

La propriété invalide est rejetée car `MadeUpRating` n’existe pas dans `Pset_DoorCommon`.

La suggestion originale du LLM est conservée avec le résultat de la validation.

Cela permet de distinguer de manière auditable :

```text
proposition du LLM
```

et :

```text
propriété IFC validée de manière déterministe
```

Un résultat `valid: true` signifie que le chemin IFC est structurellement valide pour le schéma IFC et la classe considérés.

Cela ne signifie **pas** que cette propriété constitue automatiquement la bonne interprétation réglementaire de l’exigence.

---

## Stratégie d’évaluation

Le projet évalue séparément les différentes briques du système au lieu de s’appuyer sur un unique score global.

---

### 1. Benchmark contrôlé du raisonnement

Le premier dataset contrôlé de raisonnement évaluait les trois statuts :

```text
applicable
uncertain
not_applicable
```

Résultat :

```text
32 / 32 décisions attendues retrouvées
```

Répartition :

```text
applicable:      4 / 4
uncertain:       4 / 4
not_applicable: 24 / 24
```

Ces résultats concernent uniquement le dataset contrôlé.

Ils ne sont **pas** présentés comme une mesure de précision en conditions réelles.

---

### 2. Premier benchmark de retrieval

Sur le premier jeu d’exigences simple :

```text
Recall@1: 8 / 8
```

Ce résultat a volontairement été remis en question au lieu d’être considéré comme une preuve de robustesse.

---

### 3. Stress test du retrieval

Après ajout de hard negatives sémantiquement proches :

```text
Recall@1: 4 / 8 — 50,00 %
Recall@2: 5 / 8 — 62,50 %
Recall@3: 8 / 8 — 100,00 %
```

La chute du Recall@1 a révélé une faiblesse du retrieval basé uniquement sur les embeddings.

Cette expérience a directement conduit au passage vers une architecture hybride utilisant :

```text
filtrage structurel IFC
+
classement sémantique
```

L’échec du stress test est volontairement conservé dans la méthodologie du projet car il documente comment l’architecture a évolué à partir d’une faiblesse observée.

---

### 4. Évaluation du classifieur d’exigences

Le classifieur baseline déterministe a été évalué sur le jeu d’exigences du stress test actuel.

Résultat :

```text
9 / 9 classifications correctes
```

Là encore, ce résultat concerne uniquement le dataset contrôlé.

---

### 5. Test du validateur de propriétés IFC

Le validateur déterministe a correctement accepté des propriétés IFC4 standard telles que :

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

### 6. Suite de régression end-to-end V1

L’architecture actuelle est couverte par une suite de tests automatiques end-to-end sur :

```text
IfcDoor
IfcWindow
IfcWallStandardCase
IfcSlab
```

Le test de régression vérifie :

- les exigences conservées après le filtrage structurel ;
- les exigences effectivement analysées par le LLM ;
- les statuts attendus ;
- la validation déterministe de toute propriété IFC proposée.

Résultat actuel :

```text
Total checks: 26
PASS: 26
FAIL: 0

Success rate: 100.00%

NO REGRESSION DETECTED
```

Cela signifie que la V1 actuelle réussit tous les contrôles de sa suite de régression contrôlée.

Cela ne signifie **pas** que le système atteint 100 % de précision sur des projets BIM, spécifications, réglementations ou modèles IFC non vus.

---

## Exemple de workflow

Prenons une porte IFC intérieure reliant une salle de bain à un couloir :

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

La porte donne sur un couloir,
mais la maquette ne permet pas d'établir si ce
couloir est une circulation protégée.
```

```text
REQ-006 → uncertain

La porte est intérieure et donne sur un couloir,
mais l'exigence acoustique du projet est inconnue.
```

```text
REQ-007 → not_applicable

Les données BIM disponibles identifient
l'objet comme une porte intérieure.
```

Pour l’information de résistance au feu manquante, le LLM peut proposer :

```text
Pset_DoorCommon.FireRating
```

IfcOpenShell vérifie ensuite indépendamment que cette propriété existe et qu’elle est applicable à `IfcDoor`.

---

## Périmètre actuel de la V1

La version actuelle comprend :

- extraction de maquettes IFC4 avec IfcOpenShell ;
- extraction d’objets BIM par GlobalId ;
- extraction de propriétés BIM ;
- génération de requêtes BIM sémantiques ;
- normalisation sémantique destinée au retrieval ;
- génération séparée du contexte utilisé pour le raisonnement ;
- découpage des exigences techniques ;
- séparation des exigences objet et processus ;
- classification exigence → famille IFC ;
- filtrage structurel IFC ;
- classement sémantique par embeddings ;
- raisonnement contextuel avec LLM ;
- traçabilité vers l’exigence source ;
- classification `applicable / uncertain / not_applicable` ;
- identification du contexte d’applicabilité manquant ;
- identification des données requises manquantes ;
- suggestions de propriétés IFC ;
- validation déterministe des propriétés IFC ;
- évaluation du raisonnement ;
- évaluation du retrieval ;
- stress test du retrieval ;
- évaluation du classifieur d’exigences ;
- tests du validateur IFC ;
- tests automatiques de régression end-to-end.

---

## Limites actuelles

Ce projet est un PoC expérimental et non un système de contrôle de conformité en production.

Les limites actuelles comprennent notamment :

- une seule maquette IFC de démonstration ;
- de petits datasets d’exigences synthétiques ;
- un nombre limité de familles d’entités IFC ;
- un classifieur d’exigences simple basé sur des mots-clés ;
- aucun dataset réglementaire réel en production ;
- aucune décision automatique de conformité réglementaire ;
- aucun benchmark annoté à grande échelle ;
- aucune base vectorielle ;
- les embeddings sont actuellement recalculés pendant le retrieval ;
- la terminologie BIM multilingue n’est que partiellement normalisée ;
- aucun pipeline général d’ingestion PDF ou documentaire ;
- aucune écriture automatique dans l’IFC ;
- aucun viewer BIM intégré ;
- aucun modèle de provenance documentaire à l’échelle production ;
- aucune génération IDS intégrée à ce stade ;
- aucune validation IDS intégrée au workflow actuel.

La validation humaine reste volontairement présente dans le processus.

---

## Évolutions possibles

Les prochaines évolutions possibles comprennent :

- ingestion de spécifications réelles de projet ;
- traitement de PDF et de documents ;
- meilleure normalisation multilingue ;
- prise en charge de davantage de familles IFC ;
- datasets annotés plus importants ;
- cache des embeddings ou stockage vectoriel ;
- classification des exigences plus robuste ;
- traçabilité des exigences entre plusieurs documents ;
- intégration IDS ;
- génération d’exigences structurées après validation humaine ;
- validation déterministe IFC / IDS ;
- intégration d’un viewer BIM ;
- enrichissement contrôlé et write-back IFC ;
- exécution des tests de régression dans une CI.

Une architecture future possible est :

```text
Documents projet
       |
       v
RAG / interprétation sémantique
       |
       v
Proposition d'exigence structurée
       |
       v
Validation humaine
       |
       v
IDS
       |
       v
Validation déterministe IFC
```

L’interprétation par IA et la validation déterministe de conformité restent deux responsabilités distinctes.

---

## Technologies

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

Vue simplifiée du dépôt actuel :

```text
data/
├── model.ifc
├── spec.txt
└── spec_stress.txt

src/
├── ifc_extract.py
├── baseline_enrich.py
├── llm_enrich.py
├── rag_retriever.py
├── rag_enrich.py
├── requirement_classifier.py
├── ifc_property_validator.py
├── evaluate_reasoning.py
├── evaluate_retrieval.py
├── evaluate_retrieval_stress.py
├── evaluate_requirement_classifier.py
├── evaluate_pipeline_regression.py
├── test_rag.py
├── test_rag_stress.py
├── test_synthetic_cases.py
└── test_property_validator.py
```

Certains fichiers locaux d’entrée ou de sortie peuvent être exclus du versioning Git.

---

## Lancer les principaux tests

Active l’environnement Python puis lance le module souhaité.

### Évaluation du raisonnement contrôlé

```bash
python -m src.evaluate_reasoning
```

### Évaluation du retrieval

```bash
python -m src.evaluate_retrieval
```

### Stress test du retrieval

```bash
python -m src.evaluate_retrieval_stress
```

### Évaluation du classifieur d’exigences

```bash
python -m src.evaluate_requirement_classifier
```

### Validation des propriétés IFC

```bash
python -m src.test_property_validator
```

### Suite de régression end-to-end V1

```bash
python -m src.evaluate_pipeline_regression
```

Résultat actuel attendu :

```text
Total checks: 26
PASS: 26
FAIL: 0
Success rate: 100.00%

NO REGRESSION DETECTED
```

---

## Environnement

Créer un fichier local `.env` :

```env
OPENAI_API_KEY=your_api_key_here
OPENAI_MODEL=gpt-6-luna
```

Le fichier `.env` doit rester local et ne doit pas être ajouté au dépôt Git.

Installer les dépendances avec :

```bash
pip install -r requirements.txt
```

---

## Jalon actuel

```text
V1

Retrieval BIM hybride
+
raisonnement contextuel par LLM
+
gestion traçable de l'incertitude
+
validation déterministe des propriétés IFC
+
tests automatiques de régression
```

Le projet explore l’intersection entre :

```text
BIM
IFC / openBIM
software engineering
QA automation
information retrieval
LLM
IA appliquée aux workflows AEC
```

---

## Avertissement

Les exigences techniques utilisées dans cette démonstration sont synthétiques et ne constituent pas des exigences réglementaires.

Ce projet ne doit pas être utilisé pour établir une conformité réglementaire liée au bâtiment, à la sécurité incendie, à l’acoustique, à la thermique, à l’accessibilité ou à toute autre réglementation.

Le système actuel est un proof of concept de recherche et d’apprentissage destiné à explorer le BIM, le retrieval d’information, le raisonnement assisté par IA, la validation déterministe et les méthodologies de qualité logicielle.