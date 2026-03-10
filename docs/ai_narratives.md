# AI Narrative Generation

This document covers the setup and prompts used for generating property
summaries using a locally hosted LLM (Llama 3.1 via Ollama) and LangChain.

## 6.3.1 Ollama Setup

- Container image runs `ollama` with GPU passthrough when an NVIDIA GPU is
  available (`deploy.resources.reservations.devices` in compose).
- On first start the container pulls the model `llama3.1:8b-instruct-q4_K_M`.
  The quantized model consumes ~4.7 GB of RAM.
- Fallback path for CPU-only machines; inference timeout 30 seconds to avoid
  blocking.
- Inference is executed asynchronously via Celery workers; API endpoints never
  block.
- Temperature set to 0.3 for factual summaries; response is requested in JSON
  structured format to ease parsing.

## 6.3.2 Prompt Architecture (LangChain)

### Two‑stage pipeline

1. **Property Data Extraction Prompt**
   - Formats structured data: subject property attributes, selected comps (with
     adjustments), ARV range, neighborhood statistics, permit flags.
   - Records are transformed into a consistent context block template.
2. **Summary Generation Prompt**
   - System prompt: instructs model to act as an expert real estate analyst.
   - User prompt injects the context block and asks for a 200‑word investment
     summary covering:
     - Estimated ARV range
     - Key value‑add opportunities
     - Comparable sales evidence
     - Neighborhood trajectory
     - Risk flags (flood/seismic, open permits, condition grade)

### Hallucination guard

After generation, the output is parsed and any numeric values are compared
against the source data.  A mismatch triggers regeneration (up to 2 retries).

### Comp justification

A secondary prompt generates a 2‑sentence explanation for each of the top 3
comps, describing why it was chosen and how adjustments were applied.

### Caching

Summaries are cached in Redis with 24‑hour TTL using keys composed of
`property_id + model_version + arv_estimate_id` to avoid unnecessary
recomputations.
