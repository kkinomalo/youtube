# Local LLM API

This folder contains the local LLM serving setup for a 3B/4B model requirement.

## Final Choice

- Serving engine: Ollama
- Selected model: `qwen3:4b`
- Local alias: `local-qwen-4b`
- Default context: `8192`
- Native Ollama API: `http://127.0.0.1:11434/v1/chat/completions`
- Wrapper API: `http://127.0.0.1:8088/v1/chat/completions`
- TTS engine: Qwen3-TTS 12Hz 0.6B CustomVoice

Why this model:

- The requirement is a 3B to 4B local LLM, so 7B+ models are intentionally excluded.
- `qwen3:4b` is a compact, newer-generation text model with a long context window.
- The Ollama model size is about 2.5GB, so it has plenty of headroom on a 32GB GPU and is also practical on smaller machines.
- Ollama already exposes an OpenAI-compatible API, and this folder also includes a small wrapper API for submission/demo purposes.

See [MODEL_RESEARCH.md](./MODEL_RESEARCH.md) for the research notes.
See [TTS_RESEARCH.md](./TTS_RESEARCH.md) for the Korean AI TTS selection notes.

## Run

Install Ollama first, then run:

Windows:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\local-llm\Start-LocalLLM.ps1
```

macOS:

```bash
chmod +x ./local-llm/*.sh
./local-llm/start-local-llm.sh
```

Test the native OpenAI-compatible Ollama API:

```powershell
.\local-llm\Test-LocalLLM.ps1
```

Start the wrapper API:

Windows:

```powershell
.\local-llm\Start-LocalLLMApi.ps1
```

macOS:

```bash
./local-llm/start-local-llm-api.sh
```

Start Qwen3-TTS before using `/tts` or `/chat/tts`.

The project wrapper expects the Qwen3-TTS server at `http://127.0.0.1:5010/tts`.
It uses `Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice` with the Korean speaker `Sohee`.

Windows Qwen3-TTS server:

```powershell
.\local-llm\Start-QwenTTS.ps1
```

Windows wrapper API with Qwen3-TTS:

```powershell
.\local-llm\Start-LocalLLMApi.ps1 -TTSEngine qwen3
```

macOS wrapper API with Qwen3-TTS:

```bash
export LOCAL_TTS_ENGINE=qwen3
export QWEN_TTS_BASE_URL=http://127.0.0.1:5010
export QWEN_TTS_MODEL=Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice
export QWEN_TTS_VOICE=Sohee
./local-llm/start-local-llm-api.sh
```

Legacy Piper fallback is still available only if needed:

Windows:

```powershell
.\local-llm\Install-Piper.ps1
.\local-llm\Start-LocalLLMApi.ps1 -TTSEngine piper
```

macOS/Linux:

```bash
chmod +x ./local-llm/install-piper.sh
./local-llm/install-piper.sh
LOCAL_TTS_ENGINE=piper ./local-llm/start-local-llm-api.sh
```

Check wrapper health:

```powershell
Invoke-RestMethod -Method Get -Uri http://127.0.0.1:8088/health
```

Call the simple wrapper endpoint:

```powershell
$body = @{ message = "Explain what a CTF challenge is in one sentence." } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8088/chat -ContentType "application/json" -Body $body
```

Call the OpenAI-compatible wrapper endpoint:

```powershell
$body = @{
  model = "local-qwen-4b"
  messages = @(
    @{ role = "user"; content = "Write a tiny Python hello-world script." }
  )
  stream = $false
} | ConvertTo-Json -Depth 10

Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8088/v1/chat/completions -ContentType "application/json" -Body $body
```

Start an interactive terminal chat client:

```powershell
.\local-llm\Chat-LocalLLM.ps1
```

List local TTS voice/model:

```powershell
Invoke-RestMethod -Method Get -Uri http://127.0.0.1:8088/tts/voices
```

Create speech from text:

```powershell
$body = @{ text = "안녕하세요. Qwen3 12Hz 0.6B AI TTS API 테스트입니다."; voice = "Sohee"; rate = 8 } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8088/tts -ContentType "application/json; charset=utf-8" -Body $body
```

Create an LLM answer and synthesize it to speech:

```powershell
$body = @{ message = "Answer in Korean: say that the local LLM and TTS API is working." } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8088/chat/tts -ContentType "application/json; charset=utf-8" -Body $body
```

Download a test WAV file:

Windows:

```powershell
.\local-llm\Test-LocalTTS.ps1
```

macOS:

```bash
./local-llm/test-local-tts.sh
```

## OpenAI SDK Example

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://127.0.0.1:8088/v1/",
    api_key="local",
)

response = client.chat.completions.create(
    model="local-qwen-4b",
    messages=[{"role": "user", "content": "Write a tiny Python hello-world script."}],
)

print(response.choices[0].message.content)
```

## Alternatives

Use the same scripts with another candidate when needed:

```powershell
.\local-llm\Start-LocalLLM.ps1 -Model llama3.2:3b -Alias local-llama-3b -Context 4096
.\local-llm\Start-LocalLLM.ps1 -Model gemma3:4b -Alias local-gemma-4b -Context 8192
.\local-llm\Start-LocalLLM.ps1 -Model qwen2.5:3b -Alias local-qwen-3b -Context 8192
```

## Notes

- Ollama's OpenAI-compatible API accepts an API key field in clients, but the local server does not enforce authentication by itself.
- Do not expose the API directly to the public internet without VPN, Cloudflare Access, or reverse proxy authentication.
- TTS defaults to Qwen3-TTS 12Hz 0.6B CustomVoice. Piper, Edge TTS, and Orpheus are legacy fallback paths only.
- Qwen3-TTS runs in a separate Docker service on port `5010`; the wrapper proxies `/tts` to that service and stores the returned WAV under `local-llm/tts_output`.
- vLLM is included as an optional Linux/WSL/NVIDIA path in `docker-compose.vllm.yml`, but Ollama is the simpler path for this 3B/4B requirement.
