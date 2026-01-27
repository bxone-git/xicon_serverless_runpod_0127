"""
ComfyUI Workflow Analyzer

Parses ComfyUI workflow JSON files and extracts:
- Node types and their configurations
- Model files and paths
- Input/Output types (image/video)
"""

import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ModelReference:
    """Represents a model file reference found in a workflow."""
    filename: str
    node_id: str
    node_type: str
    input_key: str
    relative_path: Optional[str] = None

    def __hash__(self):
        return hash(self.filename)

    def __eq__(self, other):
        if isinstance(other, ModelReference):
            return self.filename == other.filename
        return False


@dataclass
class NodeInfo:
    """Represents a node in the workflow."""
    node_id: str
    class_type: str
    title: Optional[str] = None
    inputs: dict = field(default_factory=dict)


@dataclass
class WorkflowAnalysis:
    """Complete analysis results of a workflow."""
    workflow_path: str
    nodes: list[NodeInfo]
    node_types: set[str]
    models: set[ModelReference]
    has_video_input: bool
    has_video_output: bool
    has_image_input: bool
    has_image_output: bool
    input_files: list[str]

    def get_unique_node_types(self) -> list[str]:
        """Return sorted list of unique node types."""
        return sorted(self.node_types)

    def get_model_filenames(self) -> list[str]:
        """Return sorted list of model filenames."""
        return sorted([m.filename for m in self.models])


class WorkflowAnalyzer:
    """Analyzes ComfyUI workflow JSON files."""

    # Node types that indicate video input
    VIDEO_INPUT_NODES = {
        "VHS_LoadVideo",
        "VHS_LoadVideoPath",
        "LoadVideo",
    }

    # Node types that indicate video output
    VIDEO_OUTPUT_NODES = {
        "VHS_VideoCombine",
        "SaveAnimatedWEBP",
        "SaveVideo",
    }

    # Node types that indicate image input
    IMAGE_INPUT_NODES = {
        "LoadImage",
        "LoadImageMask",
    }

    # Node types that indicate image output
    IMAGE_OUTPUT_NODES = {
        "SaveImage",
        "PreviewImage",
    }

    # Input keys that typically contain model filenames
    MODEL_INPUT_KEYS = {
        "model", "model_name", "ckpt_name", "vae_name", "vae",
        "lora", "lora_name", "clip_name", "clip_vision",
        "unet_name", "vitpose_model", "yolo_model", "url",
    }

    # File extensions that indicate model files
    MODEL_EXTENSIONS = {
        ".safetensors", ".pth", ".pt", ".ckpt", ".bin", ".onnx", ".torchscript"
    }

    def __init__(self):
        pass

    def analyze(self, workflow_path: str | Path) -> WorkflowAnalysis:
        """
        Analyze a ComfyUI workflow JSON file.

        Args:
            workflow_path: Path to the workflow JSON file

        Returns:
            WorkflowAnalysis object containing the analysis results
        """
        workflow_path = Path(workflow_path)

        with open(workflow_path, 'r', encoding='utf-8') as f:
            workflow_data = json.load(f)

        nodes = []
        node_types = set()
        models = set()
        input_files = []

        has_video_input = False
        has_video_output = False
        has_image_input = False
        has_image_output = False

        for node_id, node_data in workflow_data.items():
            class_type = node_data.get("class_type", "")
            inputs = node_data.get("inputs", {})
            meta = node_data.get("_meta", {})
            title = meta.get("title")

            node_info = NodeInfo(
                node_id=node_id,
                class_type=class_type,
                title=title,
                inputs=inputs
            )
            nodes.append(node_info)
            node_types.add(class_type)

            # Check for video/image input/output
            if class_type in self.VIDEO_INPUT_NODES:
                has_video_input = True
                # Extract video filename
                video_file = inputs.get("video")
                if video_file and isinstance(video_file, str):
                    input_files.append(video_file)

            if class_type in self.VIDEO_OUTPUT_NODES:
                has_video_output = True

            if class_type in self.IMAGE_INPUT_NODES:
                has_image_input = True
                # Extract image filename
                image_file = inputs.get("image")
                if image_file and isinstance(image_file, str):
                    input_files.append(image_file)

            if class_type in self.IMAGE_OUTPUT_NODES:
                has_image_output = True

            # Extract model references
            for key, value in inputs.items():
                if self._is_model_reference(key, value):
                    model_ref = ModelReference(
                        filename=value,
                        node_id=node_id,
                        node_type=class_type,
                        input_key=key,
                        relative_path=self._infer_model_path(key, value)
                    )
                    models.add(model_ref)

        return WorkflowAnalysis(
            workflow_path=str(workflow_path),
            nodes=nodes,
            node_types=node_types,
            models=models,
            has_video_input=has_video_input,
            has_video_output=has_video_output,
            has_image_input=has_image_input,
            has_image_output=has_image_output,
            input_files=input_files
        )

    def _is_model_reference(self, key: str, value) -> bool:
        """Check if a value is a model file reference."""
        if not isinstance(value, str):
            return False

        # Check if key suggests model
        if key.lower() in self.MODEL_INPUT_KEYS:
            return True

        # Check file extension
        for ext in self.MODEL_EXTENSIONS:
            if value.lower().endswith(ext):
                return True

        return False

    def _infer_model_path(self, key: str, filename: str) -> Optional[str]:
        """Infer the relative model path based on key and filename."""
        key_lower = key.lower()

        path_mapping = {
            "ckpt_name": "models/checkpoints",
            "checkpoint": "models/checkpoints",
            "vae_name": "models/vae",
            "vae": "models/vae",
            "lora": "models/loras",
            "lora_name": "models/loras",
            "clip_name": "models/clip_vision",
            "clip_vision": "models/clip_vision",
            "unet_name": "models/unet",
            "model_name": "models/diffusion_models",
        }

        for key_pattern, path in path_mapping.items():
            if key_pattern in key_lower:
                return path

        # Infer from filename extension
        if filename.endswith(".onnx"):
            return "models/onnx"

        return None

    def analyze_from_string(self, workflow_json: str) -> WorkflowAnalysis:
        """
        Analyze a workflow from a JSON string.

        Args:
            workflow_json: JSON string containing the workflow

        Returns:
            WorkflowAnalysis object
        """
        import tempfile

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write(workflow_json)
            temp_path = f.name

        try:
            result = self.analyze(temp_path)
            result.workflow_path = "<string>"
            return result
        finally:
            Path(temp_path).unlink()


def main():
    """CLI entry point for testing."""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python workflow_analyzer.py <workflow.json>")
        sys.exit(1)

    analyzer = WorkflowAnalyzer()
    analysis = analyzer.analyze(sys.argv[1])

    print(f"\n=== Workflow Analysis: {analysis.workflow_path} ===\n")
    print(f"Total nodes: {len(analysis.nodes)}")
    print(f"Unique node types: {len(analysis.node_types)}")
    print(f"Models referenced: {len(analysis.models)}")
    print(f"\nVideo input: {analysis.has_video_input}")
    print(f"Video output: {analysis.has_video_output}")
    print(f"Image input: {analysis.has_image_input}")
    print(f"Image output: {analysis.has_image_output}")

    print(f"\n--- Node Types ({len(analysis.node_types)}) ---")
    for node_type in analysis.get_unique_node_types():
        print(f"  - {node_type}")

    print(f"\n--- Models ({len(analysis.models)}) ---")
    for model in sorted(analysis.models, key=lambda m: m.filename):
        print(f"  - {model.filename}")
        print(f"      Node: {model.node_type} (ID: {model.node_id})")
        if model.relative_path:
            print(f"      Path: {model.relative_path}")

    if analysis.input_files:
        print(f"\n--- Input Files ---")
        for f in analysis.input_files:
            print(f"  - {f}")


if __name__ == "__main__":
    main()
