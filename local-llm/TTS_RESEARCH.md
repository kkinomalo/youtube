# Korean AI TTS Research

## 요구사항

- 로컬 환경에서 TTS를 API 형태로 제공해야 한다.
- 단순 OS 음성, Google TTS, Edge TTS가 아니라 AI 기반 TTS 모델을 사용해야 한다.
- 한국어 음성 생성이 가능해야 한다.
- 프론트엔드에서 호출하기 쉬운 API 형태여야 한다.

## 최종 선택

- TTS 모델: `Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice`
- 실행 방식: Docker + `qwen-tts`
- 프로젝트 API 엔진명: `qwen3-tts-12hz-0.6b`
- 기본 speaker: `Sohee`
- 출력 형식: WAV

## Qwen3-TTS를 선택한 이유

`Qwen3-TTS-12Hz-0.6B-CustomVoice`는 Qwen에서 공개한 AI TTS 모델이다. 한국어를 포함한 다국어 음성 생성을 지원하며, CustomVoice 모델에는 한국어 speaker인 `Sohee`가 포함되어 있다.

초기에는 `Orpheus-3b-Korean-FT-Q8_0.gguf`도 테스트했다. 하지만 현재 Windows Docker 환경에서 GPU가 정상적으로 잡히지 않아 CPU 모드로 실행되었고, 짧은 문장 생성에도 시간이 오래 걸렸다. 따라서 시연 안정성과 실제 사용성을 위해 더 가벼운 Qwen3-TTS 0.6B 모델로 교체했다.

## 비교

| 후보 | 장점 | 단점 | 결과 |
| --- | --- | --- | --- |
| Orpheus 3B Korean | 3B급 한국어 TTS 모델, GGUF 제공 | 현재 환경에서 GPU Docker가 잡히지 않아 CPU 생성 속도가 매우 느림 | 교체 |
| Qwen3-TTS 12Hz 0.6B CustomVoice | Qwen 공식 TTS, 한국어 지원, Sohee speaker, 상대적으로 가벼움 | 3B 모델은 아님 | 최종 선택 |
| Edge TTS / Google TTS | 빠르고 간단함 | 로컬 AI TTS 모델이 아님 | 제외 |
| Piper | 로컬 실행 가능 | 공식 한국어 voice 구성이 애매하고 원하는 품질과 거리가 있음 | 제외 |

## API 구조

```text
Frontend
  -> Project API Server : POST /tts
  -> Qwen3-TTS Server   : POST /tts
  -> WAV file           : /audio/{id}.wav
```

## 실행

Qwen3-TTS 서버:

```powershell
.\local-llm\Start-QwenTTS.ps1
```

프로젝트 API 서버:

```powershell
.\local-llm\Start-LocalLLMApi.ps1 -TTSEngine qwen3
```

목소리 확인:

```powershell
Invoke-RestMethod -Method Get -Uri http://127.0.0.1:8088/tts/voices
```

TTS 생성:

```powershell
$body = @{
  text = "안녕하세요. Qwen3 TTS 테스트입니다."
  voice = "Sohee"
  rate = 8
} | ConvertTo-Json

Invoke-RestMethod -Method Post `
  -Uri http://127.0.0.1:8088/tts `
  -ContentType "application/json; charset=utf-8" `
  -Body $body `
  -TimeoutSec 600
```

## 발표자료용 문장

TTS 모델은 `Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice`를 사용했다. 이 모델은 Qwen에서 공개한 AI TTS 모델이며 한국어 음성 생성을 지원한다. 기본 speaker는 `Sohee`로 설정했고, Local API의 `/tts` 엔드포인트를 통해 입력 텍스트를 WAV 파일로 변환하도록 구성했다.

## 참고 자료

- Qwen3-TTS GitHub: https://github.com/QwenLM/Qwen3-TTS
- Qwen3-TTS 0.6B CustomVoice: https://huggingface.co/Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice
