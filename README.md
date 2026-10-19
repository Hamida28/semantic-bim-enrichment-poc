# Semantic BIM Enrichment PoC

[🇫🇷 Version française](README.fr.md)

## Overview

**Semantic BIM Enrichment** is a proof of concept exploring how structured BIM data can be connected with natural-language technical requirements through a hybrid AI workflow.

The project combines:

- IFC data extraction with IfcOpenShell

- deterministic BIM structure

- semantic retrieval using embeddings

- contextual reasoning with an LLM

- requirement traceability

- explicit handling of missing information

- deterministic validation of IFC property suggestions

- automated regression testing

The objective is **not** to let an LLM autonomously decide whether a BIM model is compliant.

Instead, the PoC explores how AI can assist with:

- identifying potentially relevant technical requirements;

- determining whether available BIM evidence is sufficient;

- distinguishing missing applicability context from missing required data;

- proposing structured IFC properties;

- keeping deterministic validation and human review in the workflow.

---

## Problem

Technical project requirements are often expressed in natural language, while BIM models contain structured information.

For example:

> All doors on protected circulation routes must have an appropriate fire-resistance rating documented in the BIM data.

An IFC model may contain:

- the door;

- its IFC class;

- connected rooms;

- its Property Sets;

- architectural classifications;

while still not explicitly stating whether the associated corridor is a **protected circulation route**.

A reliable system must therefore distinguish between:

- a requirement that clearly applies;

- a requirement that clearly does not apply;

- a requirement whose applicability cannot yet be determined.

The PoC uses three statuses:

```text

applicable

not_applicable

uncertain

```

The `uncertain` status is particularly important.

Missing BIM information must not automatically be interpreted as non-compliance.

---

## Current Architecture

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

              |                       |

              v                       v

      Structural IFC family     Retrieval query

         identification         + semantic hints

              |                       |

              |                       v

              |                  Embeddings

              |                       |

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

             |            |             |

        applicable     uncertain    not_applicable

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

The architecture deliberately separates tasks that benefit from AI from tasks that can be verified deterministically.

---

## Hybrid Retrieval

### Initial approach

The first version relied primarily on semantic similarity between BIM object descriptions and technical requirements.

On a simple requirement set, retrieval achieved:

```text

Recall@1: 8/8 — 100%

```

However, the dataset was small and the requirements were relatively easy to distinguish.

A perfect score on that dataset did not demonstrate robustness.

### Stress test with hard negatives

Semantically similar requirements were deliberately introduced to make retrieval more difficult.

Examples included:

```text

External windows ...

Internal windows ...

External doors ...

Internal doors connecting rooms to circulation areas ...

Floor slabs in technical areas ...

Floor slabs in residential areas ...

```

The retrieval stress test produced:

```text

Recall@1: 4/8 — 50.00%

Recall@2: 5/8 — 62.50%

Recall@3: 8/8 — 100.00%

```

This failure was useful.

It revealed that embeddings were being asked to rediscover information already explicitly available in IFC.

For example, the BIM model already knows whether an object is an:

```text

IfcDoor

IfcWindow

IfcWall

IfcSlab

```

There is no reason to rely entirely on semantic similarity to determine that structural compatibility.

### Architectural improvement

The retrieval architecture was therefore changed to:

```text

IFC structural filtering

        +

semantic ranking

```

For example:

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

The deterministic filter removes structurally incompatible requirements before semantic ranking.

Embeddings are then used where semantic comparison is actually useful.

---

## Requirement Classification

Requirements are classified into IFC entity families before structural filtering.

Example:

```text

"External windows must include acoustic-performance information..."

→ IfcWindow

```

The current V1 uses a transparent deterministic keyword-based baseline classifier.

Controlled evaluation:

```text

9 / 9 requirement classifications correct

```

This result applies only to the current controlled dataset.

The classifier is intentionally simple and is **not** presented as a universal natural-language requirement classifier.

More ambiguous formulations remain a future research area.

---

## Retrieval and Reasoning Are Separate Responsibilities

A central design decision is to separate:

```text

retrieval

```

from:

```text

reasoning

```

Retrieval answers:

> Which requirements should be examined for this BIM object?

Reasoning answers:

> Given the available BIM evidence, what can be concluded about each requirement?

A retrieved requirement is therefore only a **candidate**.

It is never automatically considered applicable.

This distinction is especially important because several requirements may legitimately concern the same BIM object.

---

## LLM Reasoning

For each retrieved requirement, the LLM returns structured output similar to:

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

### Status definitions

#### `applicable`

The available BIM evidence supports the conditions that make the requirement applicable.

#### `not_applicable`

The available BIM evidence clearly shows that the requirement does not concern the object.

#### `uncertain`

The requirement may concern the object, but information required to determine applicability is missing.

---

## Missing Context vs Missing Required Data

The project explicitly separates two different kinds of missing information.

### `missing_context`

Information required to determine whether the requirement applies.

Example:

```text

Is this corridor a protected circulation route?

```

### `missing_required_data`

Information required to assess or satisfy the requirement once its applicability conditions are established.

Example:

```text

What fire-resistance rating is required?

```

This distinction prevents missing BIM data from being interpreted too quickly as non-compliance.

---

## Retrieval Evidence vs Reasoning Evidence

The system also separates information used to improve retrieval from information used as evidence by the reasoning model.

For example, the source IFC contains the German ArchiCAD value:

```text

Außenwände

```

For semantic retrieval, the query may be enriched with:

```text

Semantic layer meaning: external walls

```

This helps embeddings work across heterogeneous terminology.

However, this added interpretation is **not passed to the LLM as original BIM evidence**.

The reasoning context retains the source value:

```text

Außenwände

```

The architecture therefore distinguishes:

```text

retrieval-oriented semantic normalization

```

from:

```text

source BIM evidence

```

This reduces the risk of a transformation introduced for search purposes silently becoming compliance evidence.

---

## IFC Property Suggestions

When information is missing, the LLM may suggest a standard IFC property.

Example:

```text

Pset_DoorCommon.FireRating

```

The LLM suggestion is not automatically trusted.

A second deterministic step verifies it using IfcOpenShell.

---

## Deterministic IFC Property Validation

For every proposed IFC property, the system verifies:

```text

Does the Property Set exist?

Does the property exist inside that Property Set?

Is the Property Set applicable to this IFC class?

```

Example of a valid proposal:

```text

Pset_DoorCommon.FireRating

→ valid: true

```

Example of a deliberately invalid proposal:

```text

Pset_DoorCommon.MadeUpRating

→ valid: false

```

The invalid property is rejected because `MadeUpRating` does not exist in `Pset_DoorCommon`.

The original LLM suggestion is preserved together with the validation result.

This creates an auditable distinction between:

```text

LLM proposal

```

and:

```text

deterministically validated IFC property

```

A `valid: true` result means that the IFC property path is structurally valid for the selected IFC schema and class.

It does **not** mean that the proposed property is automatically the correct regulatory interpretation of the requirement.

---

## Evaluation Strategy

The project evaluates different parts of the system separately instead of relying on one global accuracy number.

---

### 1. Controlled Reasoning Benchmark

The first controlled reasoning dataset evaluated the three reasoning statuses:

```text

applicable

uncertain

not_applicable

```

Result:

```text

32 / 32 expected decisions matched

```

Breakdown:

```text

applicable:      4 / 4

uncertain:       4 / 4

not_applicable: 24 / 24

```

These results apply only to the controlled evaluation dataset.

They are **not** presented as real-world accuracy.

---

### 2. Initial Retrieval Benchmark

On the first simple requirement set:

```text

Recall@1: 8 / 8

```

This result was intentionally challenged rather than treated as proof of robustness.

---

### 3. Retrieval Stress Test

After introducing semantically similar hard negatives:

```text

Recall@1: 4 / 8 — 50.00%

Recall@2: 5 / 8 — 62.50%

Recall@3: 8 / 8 — 100.00%

```

The drop in Recall@1 exposed a weakness in embedding-only retrieval.

That experiment directly motivated the move toward hybrid retrieval using:

```text

IFC structural filtering

+

semantic ranking

```

The failed stress test is intentionally kept as part of the project methodology because it documents how the architecture evolved from observed weaknesses.

---

### 4. Requirement Classifier Evaluation

The deterministic baseline requirement classifier was evaluated on the current stress-test requirement set.

Result:

```text

9 / 9 classifications correct

```

Again, this applies only to the controlled test set.

---

### 5. IFC Property Validator Test

The deterministic IFC property validator correctly accepted valid standard IFC4 properties such as:

```text

Pset_DoorCommon.FireRating

Pset_DoorCommon.AcousticRating

Pset_WallCommon.AcousticRating

Pset_WallCommon.FireRating

Pset_SlabCommon.FireRating

Pset_SlabCommon.AcousticRating

```

and rejected the deliberately invalid:

```text

Pset_DoorCommon.MadeUpRating

```

---

### 6. V1 End-to-End Regression Suite

The current architecture is covered by an automated end-to-end regression suite across:

```text

IfcDoor

IfcWindow

IfcWallStandardCase

IfcSlab

```

The regression test checks:

- requirements surviving structural filtering;

- requirements actually analysed by the LLM;

- expected reasoning statuses;

- deterministic validation of any proposed IFC property.

Current result:

```text

Total checks: 26

PASS: 26

FAIL: 0

Success rate: 100.00%

NO REGRESSION DETECTED

```

This means that the current V1 passes all checks in its controlled regression suite.

It does **not** imply 100% accuracy on unseen BIM projects, specifications, regulations, or IFC models.

---

## Example Workflow

Consider an interior IFC door connecting a bathroom to a hallway:

```text

IfcDoor

Bad ↔ Flur

```

The hybrid retrieval layer may retain:

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

The reasoning layer may then produce:

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

For the missing fire-resistance information, the LLM may suggest:

```text

Pset_DoorCommon.FireRating

```

IfcOpenShell then independently validates whether that property exists and is applicable to `IfcDoor`.

---

## Current V1 Scope

The current version includes:

- IFC4 model extraction with IfcOpenShell

- BIM object extraction by GlobalId

- BIM property extraction

- semantic BIM query generation

- retrieval-oriented semantic normalization

- separate reasoning evidence generation

- technical requirement chunking

- object/process requirement separation

- requirement-to-IFC-family classification

- structural IFC filtering

- embedding-based semantic ranking

- contextual LLM reasoning

- requirement source traceability

- `applicable / uncertain / not_applicable` classification

- missing applicability context identification

- missing required data identification

- IFC property suggestions

- deterministic IFC property validation

- controlled reasoning evaluation

- retrieval evaluation

- retrieval stress testing

- requirement classifier evaluation

- property validator testing

- automated end-to-end regression testing

---

## Current Limitations

This project is an experimental PoC, not a production compliance system.

Current limitations include:

- one demonstration IFC model;

- small synthetic requirement datasets;

- limited IFC entity-family coverage;

- simple keyword-based requirement classification;

- no production regulatory dataset;

- no automated regulatory compliance decision;

- no large-scale labelled benchmark;

- no vector database;

- embeddings are currently recomputed during retrieval;

- multilingual BIM terminology is only partially normalized;

- no PDF or general document-ingestion pipeline yet;

- no automatic IFC write-back;

- no BIM viewer integration;

- no production-scale provenance model;

- no IDS generation pipeline yet;

- no IDS validation integrated into the current workflow.

Human validation intentionally remains part of the process.

---

## Future Work

Possible next steps include:

- ingestion of real project specifications;

- PDF and document processing;

- stronger multilingual normalization;

- support for additional IFC entity families;

- larger labelled evaluation datasets;

- embedding caching or vector storage;

- more robust requirement classification;

- requirement provenance across multiple documents;

- IDS integration;

- structured requirement generation after human validation;

- deterministic IFC/IDS validation;

- BIM viewer integration;

- controlled IFC enrichment and write-back;

- CI execution of regression tests.

A possible future architecture is:

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

AI interpretation and deterministic compliance validation remain separate responsibilities.

---

## Technology Stack

```text

Python

IfcOpenShell

OpenAI API

Embeddings

NumPy

IFC4

```

---

## Project Structure

The source code is organized by responsibility so that the current V1 architecture, evaluation tools, diagnostics, and earlier experimental versions remain clearly separated.

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

### Module responsibilities

- `core/` contains deterministic BIM and IFC utilities used across the project: IFC extraction, requirement-family classification, and IFC property validation.
- `rag/` contains the current V1 semantic retrieval and LLM reasoning pipeline.
- `evaluation/` contains automated benchmarks and regression checks used to measure retrieval, reasoning, classification, and end-to-end behaviour.
- `diagnostics/` contains exploratory and manual inspection scripts used to understand BIM objects, retrieved requirements, synthetic cases, and stress-test behaviour.
- `legacy/` preserves earlier stages of the PoC: the deterministic keyword baseline, the first LLM-only enrichment approach, and the original command-line entry point.

Keeping the legacy implementations makes the evolution of the architecture explicit:

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

Some local input/output files may be excluded from version control.

---

## Running the Main Tests

Activate the Python environment and run the desired module from the repository root.

### Controlled reasoning evaluation

```bash
python -m src.evaluation.evaluate_reasoning
```

### Retrieval evaluation

```bash
python -m src.evaluation.evaluate_retrieval
```

### Retrieval stress test

```bash
python -m src.evaluation.evaluate_retrieval_stress
```

### Requirement classifier evaluation

```bash
python -m src.evaluation.evaluate_requirement_classifier
```

### IFC property validator diagnostic

```bash
python -m src.diagnostics.test_property_validator
```

### End-to-end V1 regression suite

```bash
python -m src.evaluation.evaluate_pipeline_regression
```

Expected current regression result:

```text
Total checks: 26
PASS: 26
FAIL: 0
Success rate: 100.00%

NO REGRESSION DETECTED
```

The regression suite was rerun after reorganizing the Python modules by responsibility and still returned `26 / 26 PASS`, confirming that the refactor did not change the expected behaviour of the controlled V1 pipeline.

---

## Environment

Create a local `.env` file:

```env

OPENAI_API_KEY=your_api_key_here

OPENAI_MODEL=gpt-6-luna

```

The `.env` file must remain local and must not be committed.

Install dependencies with:

```bash

pip install -r requirements.txt

```

---

## Current Milestone

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

The project explores the intersection between:

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

## Disclaimer

The technical requirements used in this demonstration are synthetic and are not regulatory requirements.

This project must not be used to establish building-code, fire-safety, acoustic, thermal, accessibility, or other regulatory compliance.

The current system is a research and learning proof of concept intended to explore BIM, information retrieval, AI reasoning, deterministic validation, and software-quality methodologies.
