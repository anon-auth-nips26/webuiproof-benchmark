#!/bin/bash

# Script to run ui_eval_with_formatted_answer.py for case IDs (e.g., 000001) 

# Base directory
BASE_DIR=""

kill_port() {
  local port="$1"
  local pids=""

  if command -v lsof >/dev/null 2>&1; then
    pids="$(lsof -ti tcp:"${port}" 2>/dev/null || true)"
  elif command -v fuser >/dev/null 2>&1; then
    pids="$(fuser -n tcp "${port}" 2>/dev/null || true)"
  fi

  if [ -n "${pids}" ]; then
    kill ${pids} 2>/dev/null || true
    sleep 1
    kill -9 ${pids} 2>/dev/null || true
  fi
}

PORT=3010
kill_port "${PORT}"
for i in $(seq -f "%06g" 1); do
  kill_port "${PORT}"
  echo "Running case ID: $i"
  python $BASE_DIR/src/ui_test_llama/ui_eval_webgen_formatted.py \
    --base_dir ${BASE_DIR} \
    --case_id $i \
    --port ${PORT} \
    --data_src 'gemini25pro' \
    --formatted_output_folder webgen_formatted
done

echo "All cases completed!"
