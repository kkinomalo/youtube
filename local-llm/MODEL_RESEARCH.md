# 3B/4B Local LLM Research

## Goal

Run a 3B to 4B local LLM on a Windows PC and expose it through an API. Larger 7B+ models are excluded because the target range is now 3B to 4B.

## Candidate Comparison

| Candidate | Scale | Ollama size/context | Strengths | Weaknesses | Decision |
| --- | ---: | --- | --- | --- | --- |
| `qwen3:4b` | 4B | ~2.5GB / 256K | Newer Qwen generation, compact, long context, text-focused, supports tool/thinking tags in Ollama. Good general-purpose default. | Less established than older Llama 3.2 in some integrations. | Selected |
| `gemma3:4b` | 4B | ~3.3GB / 128K | Multimodal text+image input, 140+ language support, compact Google model family. | Requires Ollama 0.6+, multimodal support is extra complexity if only text API is needed. | Strong alternative |
| `llama3.2:3b` | 3B | ~2.0GB / 128K | Very lightweight, strong at instruction following, summarization, prompt rewriting, and tool use. | 3B capacity may be weaker than 4B candidates for reasoning-heavy prompts. | Low-resource alternative |
| `qwen2.5:3b` | 3B | 128K family context | Explicit multilingual support and stable Qwen2.5 family. | Older than Qwen3 and smaller than 4B options. | Conservative alternative |
| `qwen2.5-coder:3b` | 3B | code-focused family | Good when the task is specifically code generation/reasoning/fixing. | Too task-specific for a general local LLM API requirement. | Not selected |

## Final Model

The final selected model is `qwen3:4b`.

Reasons:

- It fits the requested 3B to 4B range.
- It is small enough for fast local serving while still being larger than 3B alternatives.
- Ollama lists it at about 2.5GB with a 256K context window, so it is lightweight and flexible.
- It is a text model, which keeps the API implementation simple compared with multimodal-first options.
- It can be served directly through Ollama's OpenAI-compatible `/v1/chat/completions` endpoint.

## API Plan

The API layer has two parts:

1. Ollama native OpenAI-compatible API:

```text
POST http://127.0.0.1:11434/v1/chat/completions
```

2. Project wrapper API:

```text
GET  http://127.0.0.1:8088/health
GET  http://127.0.0.1:8088/v1/models
POST http://127.0.0.1:8088/v1/chat/completions
POST http://127.0.0.1:8088/chat
```

## Sources

- Ollama qwen3:4b: https://ollama.com/library/qwen3:4b
- Ollama gemma3:4b: https://ollama.com/library/gemma3:4b
- Ollama llama3.2:3b: https://ollama.com/library/llama3.2:3b
- Ollama qwen2.5:3b: https://ollama.com/library/qwen2.5:3b
- Ollama qwen2.5-coder:3b: https://ollama.com/library/qwen2.5-coder:3b
- Ollama OpenAI compatibility: https://docs.ollama.com/api/openai-compatibility
