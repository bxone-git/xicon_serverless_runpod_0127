# XiCON Agents

Specialized agents for the XiCON Serverless RunPod Automation System.

---

## xicon:workflow-analyst

**Model Tier**: Haiku (fast, low-cost)
**Purpose**: Parse and analyze ComfyUI workflow JSON files

### Capabilities
- Extract all node types from workflow
- Identify model file references
- Detect input/output types (video/image)
- Count nodes and connections

### Tools Available
- Read
- Glob

### When to Use
- Quick analysis of workflow structure
- Extracting node lists for registry lookup
- Determining I/O requirements

### Example Prompt
```
Analyze this ComfyUI workflow JSON and extract:
1. All unique node class_types
2. All model filenames referenced in inputs
3. Whether it uses video input/output
```

---

## xicon:dockerfile-builder

**Model Tier**: Sonnet (balanced)
**Purpose**: Generate optimized Dockerfiles for RunPod Serverless

### Capabilities
- Generate Dockerfile with proper layer ordering
- Include custom node installation commands
- Add model download commands
- Create docker-compose.yml for local testing

### Tools Available
- Read
- Write
- Glob
- Grep

### When to Use
- Creating production-ready Dockerfiles
- Optimizing build caching
- Adding custom configurations

### Example Prompt
```
Generate a Dockerfile for the XiCON_Dance_SCAIL workflow that:
1. Uses runpod/worker-comfyui:5.5.1-base
2. Installs all required custom nodes
3. Downloads all required models
4. Sets proper permissions
```

---

## xicon:deployment-guide

**Model Tier**: Sonnet (balanced)
**Purpose**: Create deployment documentation and API guides

### Capabilities
- Generate README documentation
- Create API usage examples
- Write deployment instructions
- Provide troubleshooting guides

### Tools Available
- Read
- Write
- WebSearch

### When to Use
- Creating user-facing documentation
- Writing API examples
- Explaining deployment steps

### Example Prompt
```
Create a README.md for this RunPod Serverless endpoint that includes:
1. Quick start instructions
2. API usage examples with curl
3. List of custom nodes and models
4. Troubleshooting section
```

---

## xicon:node-researcher

**Model Tier**: Sonnet (balanced)
**Purpose**: Research and find GitHub repositories for unknown nodes

### Capabilities
- Search GitHub for node implementations
- Find installation instructions
- Identify dependencies
- Verify repository validity

### Tools Available
- WebSearch
- WebFetch
- Read

### When to Use
- Unknown node encountered in workflow
- Need to find node repository URL
- Verifying node pack compatibility

### Example Prompt
```
Find the GitHub repository for these ComfyUI nodes:
- WanVideoModelLoader
- VHS_LoadVideo
- NLFPredict

Provide:
1. Repository URL
2. Installation method (comfy-cli or git clone)
3. Whether it has requirements.txt
```

---

## xicon:model-researcher

**Model Tier**: Sonnet (balanced)
**Purpose**: Find download URLs for model files

### Capabilities
- Search HuggingFace for models
- Find Civitai model pages
- Verify download URLs
- Estimate model sizes

### Tools Available
- WebSearch
- WebFetch
- Read

### When to Use
- Model URL not in registry
- Need to verify download works
- Finding alternative model sources

### Example Prompt
```
Find the HuggingFace download URL for these models:
- Wan2.1_VAE.pth
- umt5-xxl-enc-bf16.safetensors
- vitpose_h_wholebody_model.onnx

Provide:
1. Direct download URL (resolve links)
2. Correct relative path in ComfyUI
3. Approximate file size
```

---

## Usage in OMC

These agents integrate with oh-my-claudecode orchestration:

```
# Analyze workflow
Task(
    subagent_type="xicon:workflow-analyst",
    model="haiku",
    prompt="Analyze workflow.json and extract all node types"
)

# Generate Dockerfile
Task(
    subagent_type="xicon:dockerfile-builder",
    model="sonnet",
    prompt="Generate Dockerfile for XiCON_Dance_SCAIL workflow"
)

# Research unknown node
Task(
    subagent_type="xicon:node-researcher",
    model="sonnet",
    prompt="Find GitHub repo for WanVideoModelLoader node"
)
```

---

## Agent Selection Guide

| Scenario | Agent | Model |
|----------|-------|-------|
| Quick workflow analysis | workflow-analyst | haiku |
| Generate Dockerfile | dockerfile-builder | sonnet |
| Create documentation | deployment-guide | sonnet |
| Find node repository | node-researcher | sonnet |
| Find model URL | model-researcher | sonnet |
| Complex debugging | architect | opus |
