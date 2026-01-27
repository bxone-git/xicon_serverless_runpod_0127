"""
Dockerfile Generator Module

Generates Dockerfile, docker-compose.yml, and README.md from
workflow analysis results.
"""

from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional

from ..analyzer.workflow_analyzer import WorkflowAnalysis, WorkflowAnalyzer
from ..mapper.node_mapper import NodeMapper, NodeMappingResult
from ..mapper.model_finder import ModelFinder, ModelLookupResult


@dataclass
class GenerationConfig:
    """Configuration for Dockerfile generation."""
    base_version: str = "5.5.1-base"
    include_docker_compose: bool = True
    include_readme: bool = True
    include_input_copy: bool = False
    container_name: str = "xicon-comfyui"


@dataclass
class GenerationResult:
    """Result of Dockerfile generation."""
    dockerfile_content: str
    docker_compose_content: Optional[str] = None
    readme_content: Optional[str] = None
    output_dir: Optional[Path] = None
    workflow_name: str = ""
    warnings: list[str] = field(default_factory=list)


class DockerfileGenerator:
    """Generates Dockerfile and related files from workflow analysis."""

    def __init__(self,
                 templates_dir: Optional[str | Path] = None,
                 node_registry_path: Optional[str | Path] = None,
                 model_registry_path: Optional[str | Path] = None):
        """
        Initialize the generator.

        Args:
            templates_dir: Directory containing templates
            node_registry_path: Path to node_registry.json
            model_registry_path: Path to model_registry.json
        """
        if templates_dir is None:
            templates_dir = Path(__file__).parent.parent.parent / "templates"

        self.templates_dir = Path(templates_dir)

        # Initialize components
        self.analyzer = WorkflowAnalyzer()
        self.node_mapper = NodeMapper(node_registry_path)
        self.model_finder = ModelFinder(model_registry_path)

    def generate(self,
                 workflow_path: str | Path,
                 output_dir: Optional[str | Path] = None,
                 config: Optional[GenerationConfig] = None) -> GenerationResult:
        """
        Generate Dockerfile and related files from a workflow.

        Args:
            workflow_path: Path to ComfyUI workflow JSON
            output_dir: Directory to write output files (if None, just returns content)
            config: Generation configuration

        Returns:
            GenerationResult with generated content
        """
        if config is None:
            config = GenerationConfig()

        workflow_path = Path(workflow_path)
        workflow_name = workflow_path.stem

        # Analyze workflow
        analysis = self.analyzer.analyze(workflow_path)

        # Map nodes
        node_result = self.node_mapper.map_nodes(analysis.node_types)

        # Find models
        model_filenames = [m.filename for m in analysis.models]
        model_result = self.model_finder.lookup(model_filenames)

        # Generate content
        dockerfile_content = self._generate_dockerfile(
            analysis, node_result, model_result, config, workflow_name
        )

        docker_compose_content = None
        if config.include_docker_compose:
            docker_compose_content = self._generate_docker_compose(
                analysis, config, workflow_name
            )

        readme_content = None
        if config.include_readme:
            readme_content = self._generate_readme(
                analysis, node_result, model_result, config, workflow_name
            )

        # Collect warnings
        warnings = []
        if node_result.unresolved:
            warnings.append(
                f"Unresolved nodes ({len(node_result.unresolved)}): "
                f"{', '.join(node_result.unresolved[:5])}"
                + ("..." if len(node_result.unresolved) > 5 else "")
            )
        if model_result.unresolved:
            warnings.append(
                f"Unresolved models ({len(model_result.unresolved)}): "
                f"{', '.join(model_result.unresolved[:5])}"
                + ("..." if len(model_result.unresolved) > 5 else "")
            )

        result = GenerationResult(
            dockerfile_content=dockerfile_content,
            docker_compose_content=docker_compose_content,
            readme_content=readme_content,
            workflow_name=workflow_name,
            warnings=warnings
        )

        # Write files if output_dir specified
        if output_dir:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            result.output_dir = output_dir

            (output_dir / "Dockerfile").write_text(dockerfile_content, encoding='utf-8')

            if docker_compose_content:
                (output_dir / "docker-compose.yml").write_text(
                    docker_compose_content, encoding='utf-8'
                )

            if readme_content:
                (output_dir / "README.md").write_text(
                    readme_content, encoding='utf-8'
                )

        return result

    def _generate_dockerfile(self,
                             analysis: WorkflowAnalysis,
                             node_result: NodeMappingResult,
                             model_result: ModelLookupResult,
                             config: GenerationConfig,
                             workflow_name: str) -> str:
        """Generate Dockerfile content."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        lines = [
            "# ============================================================================",
            "# XiCON Serverless RunPod Dockerfile",
            "# Generated by XiCON Automation System",
            "# ============================================================================",
            f"# Workflow: {workflow_name}",
            f"# Generated: {timestamp}",
            "# ============================================================================",
            "",
            "# Base image with ComfyUI pre-installed",
            f"FROM runpod/worker-comfyui:{config.base_version}",
            "",
        ]

        # Custom node installation section
        lines.append("# ============================================================================")
        lines.append("# Custom Node Installation")
        lines.append("# ============================================================================")

        if node_result.required_packs:
            lines.append("")
            lines.append("# Install custom nodes required by the workflow")

            for pack in node_result.required_packs:
                lines.append("")
                lines.append(f"# --- {pack.name} ---")

                if pack.install_method == "comfy_cli":
                    lines.append(f"RUN {pack.install_command}")
                else:
                    # Git clone installation
                    lines.append(f"RUN cd /comfyui/custom_nodes && {pack.install_command}")
                    if pack.has_requirements:
                        lines.append(
                            f"RUN cd /comfyui/custom_nodes/{pack.name} && "
                            f"pip install -r requirements.txt"
                        )
        else:
            lines.append("# No custom nodes required")

        # Unresolved nodes section
        if node_result.unresolved:
            lines.append("")
            lines.append("# ============================================================================")
            lines.append("# UNRESOLVED NODES - Manual installation required")
            lines.append("# ============================================================================")
            lines.append("# The following nodes could not be automatically resolved:")
            for node in node_result.unresolved:
                lines.append(f"# - {node}")
            lines.append("# Please add installation commands manually or update the node registry.")

        lines.append("")

        # Model downloads section
        lines.append("# ============================================================================")
        lines.append("# Model Downloads")
        lines.append("# ============================================================================")

        if model_result.resolved:
            lines.append("")
            lines.append("# Download models required by the workflow")

            for filename, model in model_result.resolved.items():
                url = model.url
                relative_path = model.relative_path

                # Use comfy model download for HuggingFace models
                if model.source == "huggingface" or "huggingface.co" in url:
                    lines.append(
                        f"RUN comfy model download "
                        f"--url {url} "
                        f"--relative-path {relative_path} "
                        f"--filename {filename}"
                    )
                elif model.source == "github" or "github.com" in url:
                    # For GitHub releases, use wget
                    lines.append(
                        f"RUN mkdir -p /comfyui/{relative_path} && "
                        f"wget -q -O /comfyui/{relative_path}/{filename} {url}"
                    )
                else:
                    lines.append(
                        f"RUN comfy model download "
                        f"--url {url} "
                        f"--relative-path {relative_path} "
                        f"--filename {filename}"
                    )
        else:
            lines.append("# No models to download")

        # Unresolved models section
        if model_result.unresolved:
            lines.append("")
            lines.append("# ============================================================================")
            lines.append("# UNRESOLVED MODELS - Manual download required")
            lines.append("# ============================================================================")
            lines.append("# The following models could not be automatically resolved:")
            for model in model_result.unresolved:
                lines.append(f"# RUN # Could not find URL for {model}")
            lines.append("# Please add download commands manually or update the model registry.")

        # Input copy section
        if config.include_input_copy:
            lines.append("")
            lines.append("# ============================================================================")
            lines.append("# Input Files")
            lines.append("# ============================================================================")
            lines.append("# Copy input files (images/videos) into ComfyUI")
            lines.append("COPY input/ /comfyui/input/")

        # Finalize section
        lines.append("")
        lines.append("# ============================================================================")
        lines.append("# Finalize")
        lines.append("# ============================================================================")
        lines.append("# Ensure proper permissions")
        lines.append("RUN chmod -R 755 /comfyui/custom_nodes")
        lines.append("")
        lines.append("# Set working directory")
        lines.append("WORKDIR /comfyui")

        return '\n'.join(lines)

    def _generate_docker_compose(self,
                                 analysis: WorkflowAnalysis,
                                 config: GenerationConfig,
                                 workflow_name: str) -> str:
        """Generate docker-compose.yml content."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        container_name = config.container_name or workflow_name.lower().replace(" ", "-").replace("(", "").replace(")", "")

        return f"""# ============================================================================
# XiCON Serverless RunPod - Local Development Compose
# ============================================================================
# Workflow: {workflow_name}
# Generated: {timestamp}
# ============================================================================
#
# Usage:
#   docker-compose up --build     # Build and start
#   docker-compose down           # Stop
#
# Access ComfyUI at: http://localhost:8188
# ============================================================================

services:
  comfyui:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: {container_name}
    ports:
      - "8188:8188"
    volumes:
      # Mount output directory for generated files
      - ./output:/comfyui/output
      # Mount input directory for source files
      - ./input:/comfyui/input
    environment:
      - NVIDIA_VISIBLE_DEVICES=all
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
    # For local development, run ComfyUI directly
    command: ["python", "main.py", "--listen", "0.0.0.0"]

  # Optional: RunPod handler mode for testing
  handler:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: {container_name}-handler
    ports:
      - "8000:8000"
    volumes:
      - ./output:/comfyui/output
      - ./input:/comfyui/input
    environment:
      - NVIDIA_VISIBLE_DEVICES=all
      - RUNPOD_DEBUG=true
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]
    profiles:
      - handler
"""

    def _generate_readme(self,
                         analysis: WorkflowAnalysis,
                         node_result: NodeMappingResult,
                         model_result: ModelLookupResult,
                         config: GenerationConfig,
                         workflow_name: str) -> str:
        """Generate README.md content."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Determine input/output types
        input_types = []
        if analysis.has_video_input:
            input_types.append("video")
        if analysis.has_image_input:
            input_types.append("image")

        output_types = []
        if analysis.has_video_output:
            output_types.append("video")
        if analysis.has_image_output:
            output_types.append("image")

        input_type = " + ".join(input_types) if input_types else "none"
        output_type = " + ".join(output_types) if output_types else "none"

        # Build custom nodes section
        nodes_section = ""
        if node_result.required_packs:
            nodes_lines = []
            for pack in node_result.required_packs:
                nodes_lines.append(f"- **{pack.name}**: {pack.repo}")
            nodes_section = "\n".join(nodes_lines)
        else:
            nodes_section = "No custom nodes required."

        # Build unresolved nodes section
        unresolved_nodes_section = ""
        if node_result.unresolved:
            unresolved_lines = ["### Unresolved Nodes", "", "The following nodes need manual installation:"]
            for node in node_result.unresolved:
                unresolved_lines.append(f"- {node}")
            unresolved_nodes_section = "\n".join(unresolved_lines)

        # Build models section
        models_lines = []
        for filename, model in model_result.resolved.items():
            models_lines.append(f"- **{filename}** ({model.size_gb:.1f} GB)")
            models_lines.append(f"  - Path: `{model.relative_path}`")
            models_lines.append(f"  - URL: {model.url}")
        models_section = "\n".join(models_lines) if models_lines else "No models required."

        # Build unresolved models section
        unresolved_models_section = ""
        if model_result.unresolved:
            unresolved_lines = ["### Missing Model URLs", ""]
            for model in model_result.unresolved:
                unresolved_lines.append(f"- {model}")
            unresolved_models_section = "\n".join(unresolved_lines)

        return f"""# {workflow_name} - RunPod Serverless Endpoint

Generated by XiCON Serverless RunPod Automation System

## Overview

- **Workflow**: {workflow_name}
- **Generated**: {timestamp}
- **Input Type**: {input_type}
- **Output Type**: {output_type}

## Requirements

- Docker with NVIDIA GPU support
- NVIDIA Container Toolkit
- ~{model_result.total_size_gb:.1f} GB disk space for models

## Quick Start

### Local Development

1. **Build and run with Docker Compose**:
```bash
docker-compose up --build
```

2. **Access ComfyUI**: Open http://localhost:8188

3. **Load the workflow**: Use the workflow JSON file

### RunPod Deployment

1. **Push to GitHub** (recommended):
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/your-username/your-repo.git
git push -u origin main
```

2. **Create RunPod Endpoint**:
   - Go to [RunPod Serverless](https://runpod.io/console/serverless)
   - Create new endpoint
   - Select "Custom Source" and enter your GitHub repo URL
   - Configure GPU type (recommended: A100/A40 for video generation)

3. **API Usage**:
```bash
curl -X POST "https://api.runpod.ai/v2/${{ENDPOINT_ID}}/run" \\
  -H "Authorization: Bearer ${{RUNPOD_API_KEY}}" \\
  -H "Content-Type: application/json" \\
  -d '{{
    "input": {{
      "workflow": <your-workflow-json>,
      "images": [
        {{
          "name": "input_image.jpg",
          "image": "<base64-encoded-image>"
        }}
      ]
    }}
  }}'
```

## Custom Nodes Used

{nodes_section}

{unresolved_nodes_section}

## Models

{models_section}

{unresolved_models_section}

## Input/Output

### Input
{"- Reference image (JPEG/PNG)" if analysis.has_image_input else ""}
{"- Source video (MP4, any length)" if analysis.has_video_input else ""}

### Output
{"- Generated video (MP4/H264)" if analysis.has_video_output else ""}
{"- Generated images (PNG)" if analysis.has_image_output else ""}

## Troubleshooting

### Build Failures

1. **Custom node installation fails**:
   - Check if the GitHub repo exists and is accessible
   - Some nodes may have additional dependencies

2. **Model download fails**:
   - Verify the HuggingFace URL is correct
   - Some models may require authentication

### Runtime Issues

1. **Out of Memory**:
   - Use a GPU with more VRAM (24GB+ recommended for video)
   - Enable model offloading in the workflow

2. **Slow Generation**:
   - Check GPU utilization
   - Consider using FP8 or FP16 models

## License

This generated configuration is provided as-is. Please check the licenses of:
- Individual custom nodes
- Model files
- ComfyUI itself

---

Generated with [XiCON Serverless RunPod Automation](https://github.com/your-repo)
"""


def main():
    """CLI entry point for testing."""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python dockerfile_generator.py <workflow.json> [output_dir]")
        sys.exit(1)

    workflow_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None

    generator = DockerfileGenerator()
    result = generator.generate(workflow_path, output_dir)

    print(f"\n=== Generation Results ===\n")
    print(f"Workflow: {result.workflow_name}")

    if result.warnings:
        print("\nWarnings:")
        for warning in result.warnings:
            print(f"  - {warning}")

    if result.output_dir:
        print(f"\nFiles written to: {result.output_dir}")
    else:
        print("\n--- Dockerfile ---")
        print(result.dockerfile_content[:1000] + "..." if len(result.dockerfile_content) > 1000 else result.dockerfile_content)


if __name__ == "__main__":
    main()
