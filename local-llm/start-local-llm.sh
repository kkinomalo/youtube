#!/usr/bin/env bash
set -euo pipefail

MODEL="${MODEL:-qwen3:4b}"
ALIAS="${ALIAS:-local-qwen-4b}"
CONTEXT="${CONTEXT:-8192}"
HOST_ADDRESS="${OLLAMA_HOST:-0.0.0.0:11434}"

if ! command -v ollama >/dev/null 2>&1; then
  echo "Ollama is not installed or is not on PATH."
  echo "Install it from https://ollama.com/download, then rerun this script."
  exit 1
fi

export OLLAMA_HOST="$HOST_ADDRESS"

if ! curl -fsS http://127.0.0.1:11434/api/tags >/dev/null 2>&1; then
  echo "Starting Ollama on $HOST_ADDRESS ..."
  nohup ollama serve >/tmp/local-llm-ollama.log 2>&1 &

  ready=0
  for _ in $(seq 1 30); do
    sleep 1
    if curl -fsS http://127.0.0.1:11434/api/tags >/dev/null 2>&1; then
      ready=1
      break
    fi
  done

  if [ "$ready" -ne 1 ]; then
    echo "Ollama did not become ready. Check /tmp/local-llm-ollama.log"
    exit 1
  fi
fi

if ! ollama list | awk '{print $1}' | grep -qx "$MODEL"; then
  echo "Pulling $MODEL ..."
  ollama pull "$MODEL"
fi

modelfile="$(mktemp)"
cat >"$modelfile" <<EOF
FROM $MODEL
PARAMETER num_ctx $CONTEXT
PARAMETER temperature 0.2
PARAMETER top_p 0.9
SYSTEM You are a local assistant. Be concise, accurate, and explicit about uncertainty.
EOF

echo "Creating Ollama alias $ALIAS with num_ctx=$CONTEXT ..."
ollama create "$ALIAS" -f "$modelfile"
rm -f "$modelfile"

echo "Probing OpenAI-compatible API ..."
curl -fsS http://127.0.0.1:11434/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d "{\"model\":\"$ALIAS\",\"messages\":[{\"role\":\"user\",\"content\":\"Answer in one short sentence: is the local LLM API ready?\"}],\"stream\":false}" \
  | python3 -c 'import json,sys; print(json.load(sys.stdin)["choices"][0]["message"]["content"])'

echo
echo "Ready:"
echo "  Base URL: http://127.0.0.1:11434/v1/"
echo "  Model:    $ALIAS"
echo "  LAN URL:  http://<server-ip>:11434/v1/chat/completions"
