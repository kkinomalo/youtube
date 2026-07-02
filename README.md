# Local LLM + Qwen3-TTS API 정리

## 프로젝트 개요

이 프로젝트는 로컬 PC에서 실행되는 텍스트 LLM과 TTS 모델을 API로 제공하기 위해 구성했다.

텍스트 생성은 Ollama 기반의 `qwen3:4b` 모델을 사용하고, 음성 생성은 `Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice` 모델을 사용한다. 외부 연동은 zrok을 통해 로컬 API 서버를 public URL로 공유하는 방식으로 구성했다.

## 최종 구성

| 구분 | 사용 모델/도구 | 역할 |
| --- | --- | --- |
| Text LLM | `qwen3:4b` | 대화, 코드 분석, CTF 풀이 보조, 스크립트 작성 |
| LLM Runtime | Ollama | 로컬 LLM 실행 및 OpenAI 호환 API 제공 |
| TTS Model | `Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice` | 한국어 음성 생성 |
| TTS Speaker | `Sohee` | 한국어 female voice |
| TTS Runtime | Docker + `qwen-tts` | Qwen3-TTS 서버 실행 |
| Public Share | zrok | 로컬 API 외부 공유 |

## 모델 선정 이유

### Text LLM: `qwen3:4b`

`qwen3:4b`는 3B 이상 4B급 로컬 LLM 조건에 맞는 모델이다. 모델 크기가 비교적 작아 로컬 PC에서 실행하기 좋고, Ollama를 통해 OpenAI 호환 API로 쉽게 서빙할 수 있다.

주요 장점:

- 3B 이상 조건 충족
- 약 4B급 모델로 3B 모델보다 응답 품질 기대 가능
- Ollama에서 설치와 실행이 간단함
- `/v1/chat/completions` 형태로 API 제공 가능
- 코드 분석, CTF 풀이, 간단한 스크립트 작성에 활용 가능

### TTS: `Qwen3-TTS-12Hz-0.6B-CustomVoice`

초기에는 Orpheus 3B Korean TTS를 테스트했지만, Windows Docker 환경에서 GPU가 잡히지 않아 CPU 모드로 동작했고 짧은 문장 생성에도 시간이 오래 걸렸다. 따라서 시연 안정성과 속도를 위해 Qwen3-TTS 12Hz 0.6B 모델로 교체했다.

주요 장점:

- Qwen 공식 TTS 모델군
- 한국어 지원
- 0.6B 모델이라 Orpheus 3B보다 가벼움
- `Sohee`라는 한국어 speaker 제공
- 자연어 instruction으로 감정과 말투를 어느 정도 제어 가능

## API 구조

```text
사용자 / 프론트엔드
        |
        v
Project API Server : http://127.0.0.1:8088
        |
        +-- Text 요청 -> Ollama -> qwen3:4b
        |
        +-- TTS 요청  -> Qwen3-TTS Server -> WAV 생성
```

## 주요 엔드포인트

| Method | Endpoint | 설명 |
| --- | --- | --- |
| GET | `/health` | API 상태 확인 |
| GET | `/tts/voices` | TTS 모델/목소리 확인 |
| POST | `/chat` | 간단한 채팅 API |
| POST | `/chat/tts` | LLM 응답 생성 후 TTS 변환 |
| POST | `/tts` | 입력 텍스트를 음성 WAV로 변환 |
| POST | `/v1/chat/completions` | OpenAI 호환 채팅 API |
| GET | `/audio/{file}.wav` | 생성된 음성 파일 다운로드/재생 |

## 실행 순서

### 1. Ollama LLM 준비

```powershell
cd C:\Users\nojiw\Desktop\windows-ctfd-handoff-private
Set-ExecutionPolicy -Scope Process Bypass
.\local-llm\Start-LocalLLM.ps1
```

### 2. Qwen3-TTS 서버 실행

```powershell
cd C:\Users\nojiw\Desktop\windows-ctfd-handoff-private
.\local-llm\Start-QwenTTS.ps1
```

첫 실행 시 Docker 이미지 빌드와 모델 다운로드 때문에 시간이 걸릴 수 있다.

### 3. 프로젝트 API 서버 실행

```powershell
cd C:\Users\nojiw\Desktop\windows-ctfd-handoff-private
.\local-llm\Start-LocalLLMApi.ps1 -TTSEngine qwen3
```

### 4. 자유 대화 테스트

```powershell
cd C:\Users\nojiw\Desktop\windows-ctfd-handoff-private
.\local-llm\Chat-LocalLLM.ps1
```

예시:

```text
You> 안녕. 지금 어떤 모델이야?
You> /tts 안녕하세요
You> "안녕하세요"를 TTS로 만들어줘
```

### 5. zrok 외부 배포

```powershell
cd C:\Users\nojiw\Desktop\windows-ctfd-handoff-private
.\local-llm\Start-ZrokShare.ps1
```

출력된 주소를 풀스택 개발자에게 전달한다.

```text
https://xxxxx.shares.zrok.io
```

## 테스트 예시

### 상태 확인

```powershell
Invoke-RestMethod -Method Get -Uri http://127.0.0.1:8088/health
```

### TTS 목소리 확인

```powershell
Invoke-RestMethod -Method Get -Uri http://127.0.0.1:8088/tts/voices
```

### TTS 생성

```powershell
$body = @{
  text = "안녕하세요. Qwen3 TTS 테스트입니다."
  voice = "Sohee"
  rate = 8
} | ConvertTo-Json

$r = Invoke-RestMethod -Method Post `
  -Uri http://127.0.0.1:8088/tts `
  -ContentType "application/json; charset=utf-8" `
  -Body $body `
  -TimeoutSec 600

$r
```

응답 예시:

```json
{
  "audio_url": "/audio/example.wav",
  "engine": "qwen3-tts-12hz-0.6b",
  "model": "Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice",
  "voice": "Sohee",
  "content_type": "audio/wav"
}
```

## 풀스택 전달 정보

```text
Base URL:
https://xxxxx.shares.zrok.io

Text LLM:
qwen3:4b

TTS:
Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice

TTS Voice:
Sohee

TTS Endpoint:
POST /tts

Audio URL:
GET /audio/{file}.wav
```

## 참고 자료

- Qwen3-TTS GitHub: https://github.com/QwenLM/Qwen3-TTS
- Qwen3-TTS 0.6B CustomVoice: https://huggingface.co/Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice
- Ollama qwen3:4b: https://ollama.com/library/qwen3:4b
- Ollama OpenAI compatibility: https://docs.ollama.com/api/openai-compatibility
