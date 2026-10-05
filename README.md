# Semantic BIM Enrichment — mini proof of concept

A small demonstrator inspired by the problem of enriching BIM/IFC model data
using information extracted from technical documentation.

## What the project demonstrates

Input:
- one IFC model;
- one short technical specification.

Pipeline:
1. Parse the IFC with IfcOpenShell.
2. Extract a small set of walls, doors, windows and slabs.
3. Read written project requirements.
4. Link requirements to BIM objects:
   - first with a deterministic baseline;
   - then optionally with an LLM.
5. Produce an auditable JSON result.

This is intentionally a **small proof of concept**, not a production BIM tool.

## Why there are two modes

### `baseline`
No AI and no API key.
It proves that the IFC parsing + requirement mapping + output pipeline works.

### `llm`
Uses an LLM to propose richer semantic links between written requirements and IFC objects.
The prompt explicitly prevents the model from declaring compliance and asks for confidence levels.

The comparison between the two modes is useful:
it shows that AI is an enrichment layer, while deterministic logic remains a useful baseline.

## Setup

### 1. Create a virtual environment

Windows PowerShell:

```bash
python -m venv .venv
.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
python -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Get a small IFC model

IfcOpenShell provides a sample IFC from its official getting-started page:

https://docs.ifcopenshell.org/ifcopenshell-python/hello_world.html

Open that page, click **Download sample IFC**, save it as:

```text
data/model.ifc
```

### 4. Run the baseline first

```bash
python -m src.main --ifc data/model.ifc --spec data/spec.txt --mode baseline
```

Expected output:
- `output/enriched_baseline.json`
- `output/enriched_baseline.csv`

Open the CSV and inspect which requirements were associated with each BIM element.

## Add the LLM layer

The current example uses the OpenAI Responses API.
You can replace the provider later; the BIM pipeline is independent from the LLM provider.

### 1. Create `.env`

Copy:

```text
.env.example
```

to:

```text
.env
```

Then add your API key.

### 2. Run

```bash
python -m src.main --ifc data/model.ifc --spec data/spec.txt --mode llm
```

Expected output:

```text
output/enriched_llm.json
```

## What you should be able to explain in an interview

Do not present this as a finished AI product.

Explain the problem:

> A BIM model contains structured object data, while important project knowledge
> often remains in unstructured documents. This prototype explores how to connect
> the two while keeping the result traceable and subject to human validation.

Then explain the architecture:

```text
IFC model
   |
IfcOpenShell
   |
structured BIM objects
   |
   + technical specification
   |
baseline / LLM semantic matching
   |
auditable JSON enrichment suggestions
   |
human validation
```

## Sensible next steps

Only after the MVP works:
1. PDF ingestion instead of a `.txt` file.
2. Chunk documents into passages.
3. Add embeddings + retrieval (RAG).
4. Add source citations for every extracted requirement.
5. Write approved properties back into a copy of the IFC.
6. Add a small web viewer.
7. Compare LLM results against a manually labelled test set.

Do **not** add multi-agent systems before the basic extraction and evaluation pipeline is reliable.

## Suggested GitHub description

> Proof of concept exploring semantic enrichment of IFC/BIM objects from technical
> project requirements. Python + IfcOpenShell with deterministic and LLM-assisted
> enrichment, designed around traceability and human validation.

## Important

The technical specification included here is synthetic demonstration data.
Do not claim the tool performs regulatory compliance checking.
