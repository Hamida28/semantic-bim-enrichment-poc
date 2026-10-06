# Semantic BIM Enrichment — Proof of Concept

A small proof of concept exploring how AI can help connect **structured BIM/IFC data** with **unstructured technical project requirements**.

The objective is not to automate compliance decisions, but to investigate how semantic information can be proposed for BIM objects while preserving **context, uncertainty, traceability and human validation**.

## The problem

BIM models contain structured information about building objects such as walls, doors, windows, slabs, properties and classifications.

However, a significant part of project knowledge remains stored in unstructured sources such as:

- technical specifications;
- requirements documents;
- project documentation;
- standards and contractual information.

This project explores one question:

> **Can an AI system identify which textual requirements may be relevant to specific BIM objects using the information available in an IFC model?**

## Architecture

```text
IFC Model                    Technical Requirements
    │                               │
    ▼                               ▼
IfcOpenShell                     Text input
    │                               │
    ▼                               ▼
Structured BIM data ───────► Semantic analysis
                                  │
                     ┌────────────┴────────────┐
                     ▼                         ▼
            Deterministic baseline      LLM-assisted analysis
                     │                         │
                     └────────────┬────────────┘
                                  ▼
                         Suggested enrichment
                                  │
                                  ▼
                     Confidence + explanation
                                  │
                                  ▼
                          Human validation
```

## Technologies

- Python
- IFC4
- IfcOpenShell
- OpenAI API
- JSON / CSV
- LLM-assisted semantic analysis

## Method

The proof of concept compares two approaches applied to the **same BIM object and the same technical requirements**.

### 1. Deterministic baseline

The first implementation uses simple rules based on the IFC object class and keywords contained in the technical requirements.

For example:

```text
IfcDoor
   ↓
Search requirements containing "door"
   ↓
Associate matching requirement
```

This approach is deterministic and easy to audit.

However, it mainly identifies lexical relationships. It does not determine whether all the conditions contained in a requirement are actually satisfied by the BIM context.

### 2. LLM-assisted semantic analysis

The second implementation provides the language model with:

- the IFC object class;
- the available BIM properties;
- contextual information contained in the IFC data;
- the technical requirements.

The model is instructed to:

- avoid inventing unavailable information;
- identify potentially relevant requirements;
- explain why they may apply;
- report uncertainty through a confidence level;
- suggest a possible BIM property where appropriate;
- leave the final decision to a human reviewer.

## Experiment — same BIM object, different reasoning behaviour

The following BIM object was analysed using both approaches:

```text
GlobalId: 0pGAjlJMP3ifYPATVF5xAR
IFC class: IfcDoor
Name: Innentuer-2
```

The technical specification contained the following requirement:

> All doors on protected circulation routes must have an appropriate fire-resistance rating documented in the BIM data.

### Deterministic baseline

The deterministic baseline associates this requirement with the object because:

```text
Object class = IfcDoor
+
Requirement contains "doors"
```

Result:

![Deterministic baseline result](docs/baseline-door.png)

This establishes a lexical relationship between the BIM object and the requirement.

However, the rule does not analyse the additional condition:

> **on protected circulation routes**

The baseline therefore cannot determine whether this condition is actually supported by the IFC data.

### LLM-assisted analysis

The same BIM object was then analysed using the LLM.

The model identified that the door connects to a hallway (`Flur`), making the fire-resistance requirement potentially relevant.

However, it also identified that the available IFC data does **not establish that this hallway is a protected circulation route**.

It therefore returned:

```text
confidence: low
suggested property: Pset_DoorCommon.FireRating
suggested value: null
```

Result:

![LLM contextual analysis](docs/llm-door.png)

The important difference is therefore not that the LLM has proven the requirement to be applicable or not applicable.

Instead:

```text
Deterministic baseline
        ↓
"IfcDoor" matches "doors"
        ↓
requirement associated
```

versus:

```text
LLM-assisted analysis
        ↓
IfcDoor + BIM properties + requirement conditions
        ↓
requirement potentially relevant
        ↓
missing evidence identified
        ↓
confidence = low
        ↓
human validation required
```

## Initial observation

| Capability | Deterministic baseline | LLM-assisted approach |
|---|---|---|
| Uses IFC object class | Yes | Yes |
| Uses textual keywords | Yes | Yes |
| Uses BIM contextual properties | No / very limited | Yes |
| Interprets conditional wording | No | Partially |
| Provides an explanation | No | Yes |
| Represents uncertainty | No | Yes |
| Suggests BIM properties | No | Yes |
| Can produce incorrect results | Yes | Yes |
| Requires human validation | Yes | Yes |

This experiment **does not demonstrate that the LLM is globally more accurate than deterministic rules**.

It demonstrates a narrower point:

> A language model can use additional contextual information and explicitly represent uncertainty where a simple class/keyword matching rule cannot.

A proper accuracy comparison would require a manually labelled reference dataset and systematic evaluation.

## Why validation matters

Generative AI should not be treated as a source of truth for BIM, engineering or regulatory decisions.

The intended architecture therefore follows this principle:

```text
AI suggestion
      ↓
Evidence + explanation
      ↓
Confidence
      ↓
Automated validation where possible
      ↓
Human review
```

My background in software quality and test automation makes this validation layer particularly relevant to the direction of the project.

A future iteration will investigate not only how an AI system proposes BIM information, but also **how those outputs can be systematically tested and evaluated**.

## Current limitations

This is intentionally a small exploratory proof of concept.

Current limitations include:

- the technical specification is synthetic;
- requirements are stored in a simple text file;
- the entire requirement set is currently provided directly to the LLM;
- there is no retrieval pipeline yet;
- there is no RAG implementation yet;
- source passages are not yet attached to individual suggestions;
- only a limited number of IFC object classes are analysed;
- IFC relationships and spatial context are only partially exploited;
- generated results are not evaluated against a labelled reference dataset;
- information is not written back into the IFC model;
- LLM outputs can still contain incorrect interpretations;
- human validation remains mandatory.

## Next steps

### 1. Retrieval-Augmented Generation

Instead of providing all technical requirements to the LLM, retrieve only the passages that are semantically relevant to the BIM object being analysed.

Target architecture:

```text
BIM object
      +
BIM properties
      ↓
semantic query
      ↓
document retrieval
      ↓
relevant passages only
      ↓
LLM analysis
```

### 2. Source traceability

Every proposed enrichment should eventually include its documentary evidence:

```text
BIM object
→ requirement
→ source document
→ source passage
→ reasoning
→ confidence
→ proposed BIM property
```

### 3. Technical-document ingestion

Extend the system from a simple `.txt` specification to PDF specifications and other project documentation.

### 4. Automated evaluation

Create a manually labelled test dataset and compare expected results with generated results.

Metrics could include:

- true positives;
- false positives;
- false negatives;
- precision;
- recall.

### 5. BIM quality validation

Combine semantic AI analysis with deterministic BIM validation rules.

For example:

```text
AI identifies expected FireRating
        ↓
deterministic validator checks IFC
        ↓
property present?
        ↓
value populated?
        ↓
PASS / WARNING / FAIL
```

### 6. IFC write-back

After human approval, validated semantic information could be written into a copy of the IFC model.

### 7. User interface

A lightweight interface could eventually display:

```text
BIM object
+
retrieved documentary evidence
+
AI suggestion
+
confidence
+
validation status
```

## Professional context

My background combines:

**Architecture × Software Engineering / QA Automation × BIM**

I initially trained as an architect before moving into software quality and test automation, working on automated testing, APIs, data flows and reliability of complex software systems.

I am currently completing a Specialized Master in BIM and exploring the convergence between:

**BIM · automation · data · computational design · artificial intelligence for AEC**

This project is an initial practical exploration of that direction.

## Disclaimer

This repository is an exploratory proof of concept developed for learning and research purposes.

It does **not** perform regulatory or engineering compliance checking, and its outputs must not be considered authoritative technical decisions.