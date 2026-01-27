"""
Node Mapper Module

Maps ComfyUI node class_types to their GitHub repositories
and installation commands using the node registry.
"""

import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class NodePackInfo:
    """Information about a custom node pack."""
    name: str
    repo: str
    install_method: str
    install_command: str
    has_requirements: bool = False
    dependencies: list[str] = field(default_factory=list)
    system_dependencies: list[str] = field(default_factory=list)


@dataclass
class NodeMappingResult:
    """Result of mapping nodes to their repositories."""
    resolved: dict[str, NodePackInfo]  # node_type -> NodePackInfo
    unresolved: list[str]  # node types that couldn't be resolved
    builtin: list[str]  # built-in ComfyUI nodes
    required_packs: list[NodePackInfo]  # unique packs needed


class NodeMapper:
    """Maps node types to GitHub repositories."""

    def __init__(self, registry_path: Optional[str | Path] = None):
        """
        Initialize the node mapper.

        Args:
            registry_path: Path to node_registry.json. If None, uses default location.
        """
        if registry_path is None:
            # Default to data/node_registry.json relative to project root
            registry_path = Path(__file__).parent.parent.parent / "data" / "node_registry.json"

        self.registry_path = Path(registry_path)
        self._load_registry()

    def _load_registry(self):
        """Load the node registry from JSON file."""
        if not self.registry_path.exists():
            raise FileNotFoundError(f"Node registry not found: {self.registry_path}")

        with open(self.registry_path, 'r', encoding='utf-8') as f:
            self.registry = json.load(f)

        # Build lookup tables
        self.node_to_pack = self.registry.get("node_to_pack", {})
        self.node_packs = self.registry.get("node_packs", {})
        self.builtin_nodes = set(self.registry.get("builtin_nodes", {}).get("nodes", []))

    def map_nodes(self, node_types: list[str] | set[str]) -> NodeMappingResult:
        """
        Map a list of node types to their repositories.

        Args:
            node_types: List or set of node class_type strings

        Returns:
            NodeMappingResult with resolved, unresolved, and builtin nodes
        """
        resolved = {}
        unresolved = []
        builtin = []
        seen_packs = set()

        for node_type in node_types:
            if node_type in self.builtin_nodes:
                builtin.append(node_type)
                continue

            pack_name = self.node_to_pack.get(node_type)

            if pack_name == "builtin":
                builtin.append(node_type)
                continue

            if pack_name and pack_name in self.node_packs:
                pack_data = self.node_packs[pack_name]
                pack_info = NodePackInfo(
                    name=pack_name,
                    repo=pack_data.get("repo", ""),
                    install_method=pack_data.get("install_method", "git_clone"),
                    install_command=pack_data.get("install_command", ""),
                    has_requirements=pack_data.get("has_requirements", False),
                    dependencies=pack_data.get("dependencies", []),
                    system_dependencies=pack_data.get("system_dependencies", [])
                )
                resolved[node_type] = pack_info
                seen_packs.add(pack_name)
            else:
                unresolved.append(node_type)

        # Build unique required packs list
        required_packs = []
        for pack_name in seen_packs:
            pack_data = self.node_packs[pack_name]
            pack_info = NodePackInfo(
                name=pack_name,
                repo=pack_data.get("repo", ""),
                install_method=pack_data.get("install_method", "git_clone"),
                install_command=pack_data.get("install_command", ""),
                has_requirements=pack_data.get("has_requirements", False),
                dependencies=pack_data.get("dependencies", []),
                system_dependencies=pack_data.get("system_dependencies", [])
            )
            required_packs.append(pack_info)

        # Sort packs by name for consistent output
        required_packs.sort(key=lambda p: p.name)

        return NodeMappingResult(
            resolved=resolved,
            unresolved=sorted(unresolved),
            builtin=sorted(builtin),
            required_packs=required_packs
        )

    def add_node_mapping(self, node_type: str, pack_name: str, repo: str,
                         install_method: str = "git_clone",
                         install_command: Optional[str] = None,
                         has_requirements: bool = False,
                         save: bool = True):
        """
        Add a new node mapping to the registry.

        Args:
            node_type: The node class_type
            pack_name: Name of the node pack
            repo: GitHub repository URL
            install_method: "git_clone" or "comfy_cli"
            install_command: Custom install command (auto-generated if None)
            has_requirements: Whether the pack has requirements.txt
            save: Whether to save changes to file
        """
        # Add to node_to_pack mapping
        self.node_to_pack[node_type] = pack_name
        self.registry["node_to_pack"][node_type] = pack_name

        # Add or update pack info if not exists
        if pack_name not in self.node_packs:
            if install_command is None:
                if install_method == "comfy_cli":
                    install_command = f"comfy node install {pack_name}"
                else:
                    install_command = f"git clone {repo}"

            pack_data = {
                "repo": repo,
                "install_method": install_method,
                "install_command": install_command,
                "has_requirements": has_requirements,
                "nodes": [node_type]
            }
            self.node_packs[pack_name] = pack_data
            self.registry["node_packs"][pack_name] = pack_data
        else:
            # Add node to existing pack if not already there
            if "nodes" not in self.node_packs[pack_name]:
                self.node_packs[pack_name]["nodes"] = []
            if node_type not in self.node_packs[pack_name]["nodes"]:
                self.node_packs[pack_name]["nodes"].append(node_type)
                self.registry["node_packs"][pack_name]["nodes"].append(node_type)

        if save:
            self._save_registry()

    def _save_registry(self):
        """Save the registry back to JSON file."""
        with open(self.registry_path, 'w', encoding='utf-8') as f:
            json.dump(self.registry, f, indent=2, ensure_ascii=False)

    def get_install_commands(self, result: NodeMappingResult) -> list[str]:
        """
        Generate Docker RUN commands for installing node packs.

        Args:
            result: NodeMappingResult from map_nodes()

        Returns:
            List of shell commands for installation
        """
        commands = []

        for pack in result.required_packs:
            if pack.install_method == "comfy_cli":
                commands.append(f"RUN {pack.install_command}")
            else:
                # Git clone installation
                commands.append(f"# Install {pack.name}")
                commands.append(f"RUN cd /comfyui/custom_nodes && {pack.install_command}")
                if pack.has_requirements:
                    commands.append(
                        f"RUN cd /comfyui/custom_nodes/{pack.name} && "
                        f"pip install -r requirements.txt"
                    )

        return commands


def main():
    """CLI entry point for testing."""
    import sys

    mapper = NodeMapper()

    if len(sys.argv) < 2:
        print("Usage: python node_mapper.py <node_type1> [node_type2] ...")
        print("\nExample: python node_mapper.py WanVideoModelLoader VHS_LoadVideo")
        sys.exit(1)

    node_types = sys.argv[1:]
    result = mapper.map_nodes(node_types)

    print(f"\n=== Node Mapping Results ===\n")

    if result.builtin:
        print(f"Built-in nodes ({len(result.builtin)}):")
        for node in result.builtin:
            print(f"  - {node}")

    if result.resolved:
        print(f"\nResolved nodes ({len(result.resolved)}):")
        for node, pack in result.resolved.items():
            print(f"  - {node}")
            print(f"      Pack: {pack.name}")
            print(f"      Repo: {pack.repo}")

    if result.unresolved:
        print(f"\nUnresolved nodes ({len(result.unresolved)}):")
        for node in result.unresolved:
            print(f"  - {node}")

    if result.required_packs:
        print(f"\nRequired Node Packs ({len(result.required_packs)}):")
        for pack in result.required_packs:
            print(f"  - {pack.name}")
            print(f"      Install: {pack.install_command}")


if __name__ == "__main__":
    main()
