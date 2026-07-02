# 개인 README: 개발자 프로필 카드

## Header

```text
이름: [Your Name]
팀명: [Team Name]
내가 맡은 역할: 로컬 LLM/TTS API 구축, 모델 리서치, API 배포 및 풀스택 연동 지원
```

## Tech Stack Badge

`Python` `PowerShell` `Docker` `Ollama` `Qwen3` `Qwen3-TTS` `FastAPI-style API` `zrok` `GitHub`

## Feature Log: 내가 구현한 핵심 기능

- 로컬 LLM 모델 리서치 및 최종 모델 선정
  - 3B~4B급 로컬 LLM 후보를 비교했다.
  - 최종적으로 `qwen3:4b`를 선택했다.
  - Ollama를 이용해 `local-qwen-4b` alias로 서빙했다.

- 로컬 LLM API 구성
  - Ollama의 OpenAI 호환 API를 활용했다.
  - 프로젝트 wrapper API를 만들어 `/chat`, `/v1/chat/completions` 형태로 호출할 수 있게 구성했다.
  - PowerShell 실행 스크립트를 만들어 Windows 환경에서 바로 실행할 수 있도록 정리했다.

- AI TTS 모델 적용
  - 초기에는 Orpheus 3B Korean TTS를 테스트했다.
  - 이후 속도와 시연 안정성을 고려해 `Qwen/Qwen3-TTS-12Hz-0.6B-CustomVoice`로 변경했다.
  - 한국어 speaker인 `Sohee`를 사용해 `/tts` 요청 시 WAV 파일이 생성되도록 구성했다.

- 외부 배포 및 풀스택 연동 준비
  - zrok을 이용해 로컬 API를 외부 public URL로 공유했다.
  - 풀스택 개발자가 사용할 수 있도록 API 명세를 정리했다.
  - `/health`, `/tts/voices`, `/tts`, `/chat`, `/chat/tts`, `/v1/chat/completions` 엔드포인트를 정리했다.

- 문서화
  - 모델 선정 이유를 정리했다.
  - TTS 모델 교체 이유를 정리했다.
  - 발표자료용 요약 문서와 풀스택 전달용 API 문서를 작성했다.

## Debug Log: 가장 어려웠던 점 / 해결 과정

### 1. TTS 모델 선택 문제

처음에는 3B급 TTS 모델 조건을 맞추기 위해 Orpheus 3B Korean 모델을 사용했다.  
하지만 Windows Docker 환경에서 GPU가 제대로 잡히지 않아 CPU 모드로 실행되었고, 짧은 한국어 문장 하나를 생성하는 데도 시간이 오래 걸렸다.

해결:

- Orpheus 3B Korean 모델을 실제로 테스트했다.
- CPU 모드에서 너무 느린 문제가 있다는 것을 확인했다.
- 시연 안정성을 위해 더 가벼운 `Qwen3-TTS-12Hz-0.6B-CustomVoice`로 교체했다.

### 2. zrok 외부 배포 중 timeout 문제

로컬에서는 `/tts`가 정상 동작했지만, zrok public URL을 통해 외부에서 호출할 경우 TTS 생성 시간이 길어져 요청이 끊기는 문제가 있었다.

원인:

- TTS 생성이 동기 방식으로 오래 걸렸다.
- zrok proxy가 응답을 기다리다가 timeout 또는 context canceled 상태가 발생했다.

시도한 해결:

- `/health`와 `/tts/voices`를 통해 API 서버 자체는 정상임을 확인했다.
- zrok URL로 `/health` 요청이 정상적으로 들어오는 것을 확인했다.
- 문제는 네트워크 연결 자체가 아니라 긴 TTS 요청 처리 방식이라는 것을 파악했다.

### 3. 최종 미해결 이슈

최종적으로 TTS 음성 파일 생성 자체는 성공했지만, 합성 영상에 TTS 목소리가 정상적으로 들어가지 않는 문제가 남았다.

원래는 이 부분까지 수정해서 영상 합성 결과물에 음성이 포함되도록 마무리하려고 했다.  
하지만 작업 중 사용 가능한 토큰을 모두 소진해 더 이상 디버깅을 이어가지 못했고, 결국 이 부분은 눈물을 머금고 미해결 상태로 마무리했다.

## Retrospective: 새롭게 배운 점

- 로컬 LLM은 모델만 고르는 것이 아니라 실행 환경, API 구조, 배포 방식까지 함께 고려해야 한다는 것을 배웠다.
- TTS는 단순히 음성 파일을 만드는 것에서 끝나지 않고, 프론트엔드 또는 영상 합성 파이프라인에 연결되는 과정이 중요하다는 것을 알게 되었다.
- Docker에서 GPU가 잡히지 않으면 모델 성능보다 실행 환경 문제가 더 큰 병목이 될 수 있다는 것을 경험했다.
- zrok 같은 터널링 도구는 빠르게 외부 공유를 할 수 있지만, 오래 걸리는 요청은 timeout 문제가 생길 수 있다는 점을 배웠다.

## 개선하고 싶은 점

- TTS 요청을 비동기 job 방식으로 바꿔 긴 요청이 timeout 되지 않게 개선하고 싶다.
- 생성된 WAV 파일이 영상 합성 파이프라인에 확실하게 포함되도록 후처리 로직을 보강하고 싶다.
- GPU Docker 환경을 정상화해 TTS 생성 속도를 개선하고 싶다.
- API 명세를 Swagger 또는 Postman collection 형태로 정리해 풀스택 연동을 더 쉽게 만들고 싶다.

## 한 줄 회고

로컬 LLM과 AI TTS를 직접 붙이고 외부 API로 배포하는 과정까지는 성공했지만, 마지막 영상 합성 단계에서 TTS 음성이 들어가지 않는 문제를 끝까지 해결하지 못한 점이 가장 아쉬웠다.
