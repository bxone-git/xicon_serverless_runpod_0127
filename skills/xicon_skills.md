# XiCON Serverless RunPod Skills

Claude Skills for the XiCON automation system. These skills help generate RunPod Serverless Dockerfiles from ComfyUI workflows.

---

## /xicon:generate

**Purpose**: Generate Dockerfile, docker-compose.yml, and README.md from a ComfyUI workflow JSON.

**Trigger phrases**:
- "generate dockerfile for workflow"
- "create runpod endpoint"
- "xicon generate"

**Usage**:
```
/xicon:generate <workflow.json> [--output <dir>]
```

**Implementation**:
```python
# This skill runs the XiCON CLI generate command
import subprocess
import sys

workflow_path = args.get('workflow', '')
output_dir = args.get('output', '')

cmd = [sys.executable, 'xicon_cli.py', 'generate', workflow_path]
if output_dir:
    cmd.extend(['--output', output_dir])

result = subprocess.run(cmd, capture_output=True, text=True)
print(result.stdout)
if result.stderr:
    print("Errors:", result.stderr)
```

**Example**:
```
User: /xicon:generate XiCON/XiCON_Dance_SCAIL/workflow.json
Assistant: [Generates Dockerfile and related files]
```

---

## /xicon:add-node

**Purpose**: Add a custom node mapping to the registry for future use.

**Trigger phrases**:
- "add node to registry"
- "register comfyui node"

**Usage**:
```
/xicon:add-node <node_type> <github_url> [--pack-name <name>] [--has-requirements]
```

**Parameters**:
- `node_type`: The node's class_type (e.g., WanVideoModelLoader)
- `github_url`: GitHub repository URL
- `--pack-name`: Custom name for the node pack (optional)
- `--has-requirements`: Flag if the repo has requirements.txt

**Example**:
```
User: /xicon:add-node WanVideoModelLoader https://github.com/kijai/ComfyUI-WanVideoWrapper --has-requirements
Assistant: Added node mapping: WanVideoModelLoader -> ComfyUI-WanVideoWrapper
```

---

## /xicon:add-model

**Purpose**: Add a model URL to the registry for automatic Dockerfile generation.

**Trigger phrases**:
- "add model to registry"
- "register model url"

**Usage**:
```
/xicon:add-model <filename> <url> [--path <relative_path>] [--size <GB>]
```

**Parameters**:
- `filename`: Model filename (e.g., Wan2.1_VAE.pth)
- `url`: Download URL (HuggingFace, GitHub, etc.)
- `--path`: Relative path in ComfyUI (auto-detected if omitted)
- `--size`: Model size in GB

**Example**:
```
User: /xicon:add-model Wan2.1_VAE.pth https://huggingface.co/Wan-AI/Wan2.1-T2V-1.3B/resolve/main/Wan2.1_VAE.pth --size 0.5
Assistant: Added model: Wan2.1_VAE.pth (0.5 GB) to registry
```

---

## /xicon:analyze

**Purpose**: Analyze a workflow to see required nodes, models, and I/O types without generating files.

**Trigger phrases**:
- "analyze workflow"
- "what does this workflow need"

**Usage**:
```
/xicon:analyze <workflow.json> [-v|--verbose]
```

**Output includes**:
- Total nodes and unique node types
- Required custom node packs
- Unresolved nodes (need manual mapping)
- Required models and their URLs
- Unresolved models (need manual mapping)
- Input/output types (video/image)

**Example**:
```
User: /xicon:analyze my_workflow.json
Assistant:
Workflow Analysis:
- 35 nodes, 30 unique types
- 5 custom node packs required
- 0 unresolved nodes
- 7 models (29.8 GB total)
- Input: video + image
- Output: video
```

---

## /xicon:list

**Purpose**: List contents of the node or model registry.

**Usage**:
```
/xicon:list [nodes|models|all]
```

**Example**:
```
User: /xicon:list nodes
Assistant: [Lists all registered node packs and their repositories]
```

---

## Agent Definitions

### xicon:workflow-analyst (Haiku)

Fast workflow analysis agent for parsing JSON and extracting node/model info.

**Use when**: Need quick analysis of workflow structure
**Tools**: Read, Glob

### xicon:dockerfile-builder (Sonnet)

Dockerfile generation specialist that builds optimized Docker images.

**Use when**: Generating complete Dockerfile with custom optimizations
**Tools**: Read, Write, Glob, Grep

### xicon:deployment-guide (Sonnet)

RunPod deployment specialist for generating API documentation and deployment guides.

**Use when**: Creating deployment documentation or API examples
**Tools**: Read, Write, WebSearch

---

## Workflow

```
┌─────────────────┐
│ User provides   │
│ workflow.json   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Workflow        │
│ Analyzer        │
│ (Extract nodes, │
│  models, I/O)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│ Node Mapper     │────▶│ node_registry   │
│ (Match to repos)│     │     .json       │
└────────┬────────┘     └─────────────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│ Model Finder    │────▶│ model_registry  │
│ (Find URLs)     │     │     .json       │
└────────┬────────┘     └─────────────────┘
         │
         ▼
┌─────────────────┐
│ Dockerfile      │
│ Generator       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Output:         │
│ - Dockerfile    │
│ - docker-compose│
│ - README.md     │
└─────────────────┘
```

---

## Registry Format

### node_registry.json

```json
{
  "node_packs": {
    "ComfyUI-WanVideoWrapper": {
      "repo": "https://github.com/kijai/ComfyUI-WanVideoWrapper",
      "install_method": "git_clone",
      "install_command": "git clone https://github.com/kijai/ComfyUI-WanVideoWrapper.git",
      "has_requirements": true,
      "nodes": ["WanVideoModelLoader", "WanVideoDecode", ...]
    }
  },
  "node_to_pack": {
    "WanVideoModelLoader": "ComfyUI-WanVideoWrapper"
  }
}
```

### model_registry.json

```json
{
  "models": {
    "Wan2.1_VAE.pth": {
      "url": "https://huggingface.co/Wan-AI/Wan2.1-T2V-1.3B/resolve/main/Wan2.1_VAE.pth",
      "relative_path": "models/vae",
      "size_gb": 0.5,
      "description": "WanVideo 2.1 VAE model"
    }
  }
}
```
