# Full-stack API Handoff

## Base URL

로컬 테스트:

```text
http://127.0.0.1:8088
```

zrok 외부 배포:

```text
https://xxxxx.shares.zrok.io
```

## Models

```text
Text LLM:
qwen3:4b

LLM alias:
local-qwen-4b

TTS:
Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice

TTS speaker:
Sohee
```

## Endpoints

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/health` | API 상태 확인 |
| GET | `/tts/voices` | TTS 모델과 voice 확인 |
| POST | `/chat` | 간단한 채팅 요청 |
| POST | `/chat/tts` | LLM 응답 생성 후 TTS 변환 |
| POST | `/tts` | 텍스트를 WAV 음성으로 변환 |
| POST | `/v1/chat/completions` | OpenAI 호환 채팅 API |
| GET | `/audio/{file}.wav` | 생성된 음성 파일 접근 |

## Health Check

```http
GET /health
```

Response:

```json
{
  "status": "ok",
  "model": "local-qwen-4b",
  "tts": {
    "engine": "qwen3"
  }
}
```

## TTS Voices

```http
GET /tts/voices
```

Response:

```json
{
  "engine": "qwen3-tts-12hz-0.6b",
  "model": "Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice",
  "language": "Korean",
  "default_voice": "Sohee",
  "voices": [
    {
      "name": "Sohee",
      "language": "ko-KR",
      "style": "warm Korean female voice with rich emotion"
    }
  ]
}
```

## TTS Request

```http
POST /tts
Content-Type: application/json
```

Request:

```json
{
  "text": "안녕하세요. Qwen3 TTS 테스트입니다.",
  "voice": "Sohee",
  "rate": 8
}
```

Response:

```json
{
  "audio_id": "example",
  "audio_url": "/audio/example.wav",
  "content_type": "audio/wav",
  "engine": "qwen3-tts-12hz-0.6b",
  "model": "Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice",
  "voice": "Sohee"
}
```

Audio URL:

```text
https://xxxxx.shares.zrok.io/audio/example.wav
```

## Chat Request

```http
POST /chat
Content-Type: application/json
```

Request:

```json
{
  "message": "CTF에서 ELF 바이너리 분석 순서를 알려줘."
}
```

Response:

```json
{
  "model": "local-qwen-4b",
  "response": "..."
}
```

## OpenAI-compatible Chat

```http
POST /v1/chat/completions
Content-Type: application/json
```

Request:

```json
{
  "model": "local-qwen-4b",
  "messages": [
    {
      "role": "user",
      "content": "Write a Python hello world script."
    }
  ],
  "stream": false
}
```

## Notes

- `/tts`는 WAV 파일을 생성하고 `audio_url`을 반환한다.
- 프론트엔드는 `Base URL + audio_url`로 음성 파일을 재생하면 된다.
- zrok 창이 닫히면 외부 URL도 끊긴다.
- 첫 TTS 요청은 모델 로딩 때문에 느릴 수 있다.
