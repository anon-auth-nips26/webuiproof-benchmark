# WebUIProof: Benchmarking WebUI Code Generator with UI-Agent Execution Harness

WebUIProof is a comprehensive benchmark for evaluating AI models' ability to generate functional and accurate web user interfaces from natural language descriptions. This benchmark tests LLM-generated React/TypeScript/Three.js components through automated UI testing with vision-language model agents.

## Overview

WebUIProof Benchmark provides:
- **149 diverse web UI tasks** spanning data management, dashboards, forms, and interactive applications
- **Structured test cases** covering functionality, data display, and design validation
- **Automated evaluation pipeline** using vision-language models (VLMs) to test generated UIs

## Repository Structure

```
webuiproof-benchmark/
├── tasks/                          # Benchmark tasks
│   └── general_webui/              # 149 web UI generation tasks (000001-000149.json)
├── src/
│   └── ui_test_llama/              # Core evaluation framework
│       ├── webui_generation.py     # LLM-based UI generation
│       ├── build_next_from_json.py # Next.js project builder
│       ├── ui_eval_webgen_formatted.py  # Automated UI testing
│       ├── host_agent.py           # VLM agent for UI testing
│       ├── parse_interact_messages.py   # Test result parsing
│       ├── compute_acc.py          # Accuracy computation
│       ├── compute_ici.py          # Inter-category inconsistency metrics
│       ├── launch_react_project.py # React project launcher
│       └── start_service.py        # Service orchestration
├── results_webgen_formatted/       # Evaluation results
└── webgen_all_v2_formatted_from_agent_summaries.jsonl  # Training data
```

## Task Format

Each task in `tasks/general_webui/` contains:

```json
{
  "website_summary": {
    "name": "Application Name",
    "description": "Detailed description",
    "category": "Data Management | Dashboard | Form | etc.",
    "appearance": "Visual design specifications",
    "functionality": "Interactive features and behaviors"
  },
  "test_cases": {
    "functionality_testing": [...],    // Interactive element tests
    "data_display_testing": [...],     // Data visualization tests
    "design_validation_testing": [...]  // UI/UX consistency tests
  },
  "element_requirement": [...]         // Required UI components
}
```

### Test Case Categories

1. **Functionality Testing (FT)**: Validates interactive elements (buttons, dropdowns, forms)
2. **Data Display Testing (DDT)**: Verifies data visualization accuracy (charts, tables, cards)
3. **Design Validation Testing (DVT)**: Checks UI consistency (colors, layout, styling)

## Getting Started

### Prerequisites

```bash
# Python 3.8+
pip install openai requests tqdm browser_cookie3

# Node.js 18+ and npm
# For Next.js projects
```

### Environment Setup

Set your API key for model access:

```bash
export OPENROUTER_API_KEY="your-api-key-here"
```

### Generate a Web UI

```python
from src.ui_test_llama.webui_generation import generate_ui

# Generate UI from task description
task = load_task("tasks/general_webui/000001.json")
generated_code = generate_ui(
    model="anthropic/claude-sonnet-4",
    prompt=task["website_summary"]["description"]
)
```

### Build and Deploy

```bash
# Build Next.js project from generated code
python src/ui_test_llama/build_next_from_json.py \
    --input generated_code.json \
    --output ./output_project

# Launch the project
cd output_project
npm install
npm run dev
```

### Install WebVoyager
```
git clone https://github.com/MinorJerry/WebVoyager
```

### Run Automated Testing

```python
from src.ui_test_llama.ui_eval_webgen_formatted import run_evaluation

# Evaluate generated UI against test cases
results = run_evaluation(
    project_path="./output_project",
    task_file="tasks/general_webui/000001.json",
    agent_model="qwen-vl-model"
)
```

## Evaluation Pipeline

The benchmark uses a multi-stage evaluation process:

1. **Generation**: LLM generates React/TypeScript component from task description
2. **Building**: Automated Next.js project setup with proper dependencies
3. **Deployment**: Local server hosting with proper routing
4. **Testing**: VLM agent executes test cases via browser automation
5. **Scoring**: Accuracy computation across test categories

### Supported Models

**Generation Models** (via OpenRouter):
- Claude Sonnet 4 (`anthropic/claude-sonnet-4`)
- GPT-5 Mini (`openai/gpt-4.1`)
- Gemini 2.5 Pro/Flash (`google/gemini-2.5-pro`, `google/gemini-2.5-flash`)
- Llama 4 Maverick (`meta-llama/llama-4-maverick`)
- DeepSeek R1 (`deepseek/deepseek-r1-0528`)
- Qwen3 Coder (`qwen/qwen3-coder`)
- Kimi K2 (`moonshotai/kimi-k2`)

**Testing Agent**:
- Qwen2.5-VL-72B (via vLLM)

## Metrics

### Accuracy Metrics
- **Overall Accuracy**: Percentage of passed test cases across all categories
- **Category-wise Accuracy**: FT, DDT, DVT individual scores
- **Pass Rate**: Successful UI generations that compile and run

### Inter-Category Inconsistency (ICI)
Measures consistency of model performance across test categories:
```
ICI = std_dev(FT_acc, DDT_acc, DVT_acc)
```
Lower ICI indicates more balanced performance.

## Dataset Statistics

- **Total Tasks**: 149
- **Test Cases**: ~600+ across all tasks
- **Categories**: Data Management, Dashboards, Forms, E-commerce, Social Media, Analytics
- **Complexity Levels**: Simple forms to complex multi-chart dashboards

## Key Features

### Automated UI Generation
- System prompts optimized for React/TypeScript/Tailwind
- Automatic dependency management
- Support for shadcn/ui components and Recharts

### Robust Testing Framework
- Vision-language model agents for UI interaction
- Screenshot-based verification
- Detailed test execution logs
- Error recovery and retry mechanisms

### Comprehensive Evaluation
- Multi-dimensional scoring (functionality, data, design)
- Statistical analysis tools
- Result aggregation and reporting

## Example Usage

```python
# Complete evaluation workflow
from src.ui_test_llama import webui_generation, build_next_from_json, ui_eval_webgen_formatted

# 1. Generate UI
code = webui_generation.generate_from_task("tasks/general_webui/000001.json")

# 2. Build project
build_next_from_json.build_project(code, output_dir="./test_project")

# 3. Evaluate
results = ui_eval_webgen_formatted.evaluate_project(
    "./test_project",
    "tasks/general_webui/000001.json"
)

# 4. Compute metrics
from src.ui_test_llama.compute_acc import compute_accuracy
accuracy = compute_accuracy(results)
print(f"Overall Accuracy: {accuracy['overall']:.2%}")
```

## Training Data

The `webgen_all_v2_formatted_from_agent_summaries.jsonl` file contains:
- System prompts for UI generation
- User requests for various web applications
- Model-generated React components
- Metadata for training and fine-tuning




## Acknowledgments

- Built with Next.js, React, TypeScript, and Tailwind CSS
- Testing powered by Qwen2.5-VL and vLLM
- Model access via OpenRouter API
