---
layout: page
title: LLM-Assisted Generation
permalink: /llm/
nav_order: 4
---

`generate_sdg.py` takes a plain-text description of the data stream you want and calls an LLM to produce a valid `.sdg` file automatically.

---

## How It Works

1. Reads a natural language description from a `.txt` file.
2. Loads up to 3 example `.sdg` files from `examples/` as few-shot demonstrations.
3. Fills the prompt template (`prompt_template.txt`) with the description and examples.
4. Calls the configured LLM provider.
5. Extracts the `.sdg` content from the response (handles fenced code blocks automatically).
6. Writes the result to a `.sdg` file.

---

## Usage

```bash
python generate_sdg.py <description.txt>
python generate_sdg.py <description.txt> -o output.sdg
python generate_sdg.py <description.txt> --provider openai --model gpt-4o
python generate_sdg.py <description.txt> --provider ollama --model mistral
```

### All options

| Flag | Default | Description |
|------|---------|-------------|
| `input_file` | *(required)* | Path to `.txt` description file |
| `-o / --output` | same dir, `.sdg` extension | Output file path |
| `--provider` | `LLM_PROVIDER` env var | `openai`, `ollama`, or `custom` |
| `--model` | `LLM_MODEL` env var | Model name/ID |
| `--api-key` | `LLM_API_KEY` env var | API key |
| `--base-url` | `LLM_BASE_URL` env var | API base URL |
| `--temperature` | `0.3` | LLM temperature (lower = more deterministic) |
| `--max-tokens` | `4096` | Maximum response tokens |
| `--max-examples` | `3` | Number of few-shot examples to include in the prompt |

---

## Supported LLM Providers

| Provider type | Model examples | Environment variable |
|---------------|---------------|---------------------|
| `custom` *(Ariadne/AUTH)* | `gemini-2.5-pro`, `claude-sonnet-4` | *(API key passed via `--api-key`)* |
| `openai` | `gpt-4o`, `gpt-4` | `LLM_API_KEY` / `OPENAI_API_KEY` |
| `ollama` | `mistral`, `llama3`, `gemma3` | *(no key — run `ollama serve`)* |

For Ollama, install [Ollama](https://ollama.ai) and pull the model first:

```bash
ollama pull mistral
ollama serve
```

### Using environment variables

```bash
export LLM_PROVIDER=openai
export LLM_API_KEY=sk-...
export LLM_MODEL=gpt-4o
python generate_sdg.py description.txt
```

### Using the Ariadne custom API

```bash
python generate_sdg.py description.txt \
  --provider custom \
  --api-key sk-proj-... \
  --base-url https://ariadne.issel.ee.auth.gr/api \
  --model gemini-2.5-pro
```

---

## Provider API (`modelapi.py`)

`modelapi.py` can be imported directly for programmatic use:

```python
from modelapi import create_provider

# OpenAI
provider = create_provider('openai', api_key='sk-...', model='gpt-4o')

# Ollama (local)
provider = create_provider('ollama', model='mistral')

# Custom / Ariadne
provider = create_provider('custom',
                           api_key='sk-proj-...',
                           base_url='https://ariadne.issel.ee.auth.gr/api',
                           provider='gcp',
                           model='gemini-2.5-pro')

response = provider.chat("Describe a loan dataset with income and age features.")
```

All providers implement the same `chat()` / `chat_stream()` interface defined by `LLMProvider`.
