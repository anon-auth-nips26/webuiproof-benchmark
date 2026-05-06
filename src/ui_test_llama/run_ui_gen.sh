#!/bin/bash

BASE_DIR=""

# Loop through case IDs from 000001 to 000010
for i in $(seq 1 3); do
  echo "Running Trial: $i"
  python $BASE_DIR/src/ui_test_llama/webui_generation.py --model kimik2 --trial $i --jsonl $BASE_DIR/data/webgen_all_v2_formatted_from_agent_summaries.jsonl --output $BASE_DIR/src/ui_test_llama/webgen_output
done

echo "All Generation are completed!"