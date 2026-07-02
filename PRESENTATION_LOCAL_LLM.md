# 발표자료용 요약

## 로컬 AI API 구성

본 프로젝트에서는 로컬 환경에서 실행 가능한 AI API를 구성했다. 텍스트 생성 모델은 Ollama 기반의 `qwen3:4b`를 사용했고, TTS 모델은 `Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice`를 사용했다.

## 사용 모델

### 텍스트 생성 모델

- 모델명: `qwen3:4b`
- 실행 환경: Ollama
- API 별칭: `local-qwen-4b`
- 용도: 대화형 응답, 코드 분석, CTF 문제 풀이 보조, 스크립트 작성

`qwen3:4b`는 3B 이상 4B급 로컬 LLM 조건을 만족하며, Ollama를 통해 OpenAI 호환 API 형태로 쉽게 서빙할 수 있어 선택했다.

### TTS 모델

- 모델명: `Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice`
- 실행 환경: Docker + `qwen-tts`
- 기본 speaker: `Sohee`
- 출력 형식: WAV

TTS는 단순 OS 음성이나 Google TTS가 아니라, Qwen에서 공개한 AI TTS 모델을 사용했다. 한국어를 지원하며, `Sohee` speaker를 통해 한국어 음성을 생성한다.

## 시스템 구조

```text
사용자 요청
  -> Local API Server
    -> qwen3:4b / Ollama: 텍스트 응답 생성
    -> Qwen3-TTS 0.6B: 한국어 음성 생성
  -> 텍스트 응답 또는 WAV 파일 반환
```

## API 구성

```text
GET  /health
GET  /tts/voices
POST /chat
POST /chat/tts
POST /tts
POST /v1/chat/completions
GET  /audio/{file}.wav
```

## 외부 배포

로컬 API는 zrok을 이용해 외부 URL로 공유했다.

```text
Local API: http://127.0.0.1:8088
Public URL: https://xxxxx.shares.zrok.io
```

## 최종 결과

- 로컬 LLM API 구성 완료
- Qwen3-TTS 기반 한국어 TTS API 구성 완료
- `/tts` 호출 시 WAV 파일 생성 확인
- zrok을 통한 외부 공유 구조 구성 완료
