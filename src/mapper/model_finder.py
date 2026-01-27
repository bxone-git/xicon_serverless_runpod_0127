"""
Model Finder Module

Looks up model file URLs from the registry and provides
fallback search functionality for HuggingFace.
"""

import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ModelInfo:
    """Information about a model file."""
    filename: str
    url: str
    relative_path: str
    size_gb: float = 0.0
    description: str = ""
    source: str = "unknown"
    alternatives: list[str] = field(default_factory=list)
    note: Optional[str] = None


@dataclass
class ModelLookupResult:
    """Result of looking up models."""
    resolved: dict[str, ModelInfo]  # filename -> ModelInfo
    unresolved: list[str]  # filenames that couldn't be resolved
    total_size_gb: float


class ModelFinder:
    """Finds model download URLs from registry."""

    def __init__(self, registry_path: Optional[str | Path] = None):
        """
        Initialize the model finder.

        Args:
            registry_path: Path to model_registry.json. If None, uses default location.
        """
        if registry_path is None:
            registry_path = Path(__file__).parent.parent.parent / "data" / "model_registry.json"

        self.registry_path = Path(registry_path)
        self._load_registry()

    def _load_registry(self):
        """Load the model registry from JSON file."""
        if not self.registry_path.exists():
            raise FileNotFoundError(f"Model registry not found: {self.registry_path}")

        with open(self.registry_path, 'r', encoding='utf-8') as f:
            self.registry = json.load(f)

        self.models = self.registry.get("models", {})
        self.model_paths = self.registry.get("model_paths", {})

    def lookup(self, filenames: list[str] | set[str]) -> ModelLookupResult:
        """
        Look up download URLs for model files.

        Args:
            filenames: List or set of model filenames (can also be URLs)

        Returns:
            ModelLookupResult with resolved and unresolved models
        """
        resolved = {}
        unresolved = []
        total_size = 0.0

        for filename in filenames:
            # Handle URL-based references (extract filename from URL)
            original_ref = filename
            if filename.startswith("http://") or filename.startswith("https://"):
                # Extract filename from URL
                filename = filename.rstrip("/").split("/")[-1]

            if filename in self.models:
                model_data = self.models[filename]
                model_info = ModelInfo(
                    filename=filename,
                    url=model_data.get("url", ""),
                    relative_path=model_data.get("relative_path", ""),
                    size_gb=model_data.get("size_gb", 0.0),
                    description=model_data.get("description", ""),
                    source=model_data.get("source", "unknown"),
                    alternatives=model_data.get("alternatives", []),
                    note=model_data.get("note")
                )
                resolved[filename] = model_info
                total_size += model_info.size_gb
            else:
                unresolved.append(filename)

        return ModelLookupResult(
            resolved=resolved,
            unresolved=sorted(unresolved),
            total_size_gb=total_size
        )

    def add_model(self, filename: str, url: str,
                  relative_path: Optional[str] = None,
                  size_gb: float = 0.0,
                  description: str = "",
                  source: str = "huggingface",
                  save: bool = True):
        """
        Add a new model to the registry.

        Args:
            filename: Model filename
            url: Download URL
            relative_path: Path relative to ComfyUI root (auto-detected if None)
            size_gb: Model size in GB
            description: Model description
            source: Source type (huggingface, github, civitai)
            save: Whether to save changes to file
        """
        if relative_path is None:
            relative_path = self._infer_path(filename)

        model_data = {
            "url": url,
            "relative_path": relative_path,
            "size_gb": size_gb,
            "description": description,
            "source": source
        }

        self.models[filename] = model_data
        self.registry["models"][filename] = model_data

        if save:
            self._save_registry()

    def _infer_path(self, filename: str) -> str:
        """Infer the model path from filename extension."""
        filename_lower = filename.lower()

        if filename_lower.endswith(".onnx"):
            return "models/onnx"
        elif filename_lower.endswith(".torchscript"):
            return "models/checkpoints"
        elif "vae" in filename_lower:
            return "models/vae"
        elif "lora" in filename_lower:
            return "models/loras"
        elif "clip" in filename_lower:
            return "models/clip_vision"
        elif "text_encoder" in filename_lower or "umt5" in filename_lower:
            return "models/text_encoders"
        elif "diffusion" in filename_lower:
            return "models/diffusion_models"
        else:
            return "models/checkpoints"

    def _save_registry(self):
        """Save the registry back to JSON file."""
        with open(self.registry_path, 'w', encoding='utf-8') as f:
            json.dump(self.registry, f, indent=2, ensure_ascii=False)

    def get_download_commands(self, result: ModelLookupResult) -> list[str]:
        """
        Generate Docker RUN commands for downloading models.

        Args:
            result: ModelLookupResult from lookup()

        Returns:
            List of RUN commands for Dockerfile
        """
        commands = []

        for filename, model in result.resolved.items():
            url = model.url

            # Use comfy model download for HuggingFace models
            if model.source == "huggingface" or "huggingface.co" in url:
                cmd = (
                    f"RUN comfy model download "
                    f"--url {url} "
                    f"--relative-path {model.relative_path} "
                    f"--filename {filename}"
                )
            elif model.source == "github" or "github.com" in url:
                # For GitHub releases, use wget
                cmd = (
                    f"RUN wget -q -O /comfyui/{model.relative_path}/{filename} {url}"
                )
            else:
                # Default to comfy model download
                cmd = (
                    f"RUN comfy model download "
                    f"--url {url} "
                    f"--relative-path {model.relative_path} "
                    f"--filename {filename}"
                )

            commands.append(cmd)

        # Add comments for unresolved models
        for filename in result.unresolved:
            commands.append(f"# RUN # Could not find URL for {filename}")

        return commands

    def search_huggingface(self, query: str) -> list[dict]:
        """
        Search HuggingFace for model files.

        Note: This is a placeholder for future implementation.
        Currently returns empty list.

        Args:
            query: Search query

        Returns:
            List of potential matches
        """
        # Future implementation could use HuggingFace API
        # For now, return empty list
        return []


def main():
    """CLI entry point for testing."""
    import sys

    finder = ModelFinder()

    if len(sys.argv) < 2:
        print("Usage: python model_finder.py <model_filename1> [model_filename2] ...")
        print("\nExample: python model_finder.py Wan2.1_VAE.pth umt5-xxl-enc-bf16.safetensors")
        sys.exit(1)

    filenames = sys.argv[1:]
    result = finder.lookup(filenames)

    print(f"\n=== Model Lookup Results ===\n")

    if result.resolved:
        print(f"Resolved models ({len(result.resolved)}):")
        for filename, model in result.resolved.items():
            print(f"\n  {filename}")
            print(f"    URL: {model.url}")
            print(f"    Path: {model.relative_path}")
            print(f"    Size: {model.size_gb:.2f} GB")
            if model.description:
                print(f"    Description: {model.description}")

    if result.unresolved:
        print(f"\nUnresolved models ({len(result.unresolved)}):")
        for filename in result.unresolved:
            print(f"  - {filename}")

    print(f"\nTotal size: {result.total_size_gb:.2f} GB")


if __name__ == "__main__":
    main()
