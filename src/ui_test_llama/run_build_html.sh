#!/bin/bash

# Base directory
BASE_DIR=""

MODEL_NAME="kimik2"

python $BASE_DIR/src/ui_test_llama/build_next_from_json.py --json $BASE_DIR/src/ui_test_llama/webgen_output/$MODEL_NAME_trial2.json --project webgen_$MODEL_NAME_trial2


