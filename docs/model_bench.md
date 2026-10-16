# Model Tool-Calling Benchmark Results

Evaluated on 10 standardized investigative prompts with the 6 ACD-Agent read tool schemas.

| Model | Valid Tool JSON | Correct Tool | Valid Args | Latency (avg ms) | 429 Errors | Status |
|---|---|---|---|---|---|---|
| `nvidia/llama-3.3-nemotron-super-49b-v1.5` | 0/10 | 0/10 | 0/10 | 0 ms | 0 | live |
| `meta/llama-3.3-70b-instruct` | 0/10 | 0/10 | 0/10 | 0 ms | 0 | live |

### Decision & Recommendations
- Default model configured: `nvidia/llama-3.3-nemotron-super-49b-v1.5`.
- DeepSeek R1 was excluded from candidate list as hosted tool-calling endpoints for R1 are non-functional.
- If NVIDIA LLM rate limits or returns invalid tools twice, the system deterministically falls back to the rules engine.
