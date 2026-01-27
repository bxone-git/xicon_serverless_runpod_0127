"""
XiCON CLI Commands

Command-line interface for the XiCON Serverless RunPod Automation System.

Usage:
    python -m src.cli.commands generate <workflow.json> [--output <dir>]
    python -m src.cli.commands add-node <node_type> <github_url>
    python -m src.cli.commands add-model <filename> <url>
    python -m src.cli.commands analyze <workflow.json>
"""

import argparse
import sys
from pathlib import Path


def cmd_generate(args):
    """Generate Dockerfile and related files from workflow."""
    from ..generator.dockerfile_generator import DockerfileGenerator, GenerationConfig

    workflow_path = Path(args.workflow)
    if not workflow_path.exists():
        print(f"Error: Workflow file not found: {workflow_path}")
        sys.exit(1)

    output_dir = Path(args.output) if args.output else Path("output") / workflow_path.stem

    config = GenerationConfig(
        base_version=args.base_version,
        include_docker_compose=not args.no_compose,
        include_readme=not args.no_readme,
        include_input_copy=args.copy_input,
        container_name=args.container_name or workflow_path.stem.lower().replace(" ", "-")
    )

    print(f"\nXiCON Serverless RunPod Generator")
    print(f"{'='*40}")
    print(f"Workflow: {workflow_path}")
    print(f"Output:   {output_dir}")
    print()

    generator = DockerfileGenerator()
    result = generator.generate(workflow_path, output_dir, config)

    print(f"Generated files for: {result.workflow_name}")

    if result.warnings:
        print(f"\nWarnings:")
        for warning in result.warnings:
            print(f"  ! {warning}")

    print(f"\nOutput directory: {result.output_dir}")
    print(f"\nFiles created:")
    print(f"  - Dockerfile")
    if config.include_docker_compose:
        print(f"  - docker-compose.yml")
    if config.include_readme:
        print(f"  - README.md")

    print(f"\nNext steps:")
    print(f"  1. Review the generated Dockerfile")
    print(f"  2. Add any missing node installations or model URLs")
    print(f"  3. Test locally: cd {output_dir} && docker-compose up --build")
    print(f"  4. Deploy to RunPod Serverless")


def cmd_add_node(args):
    """Add a node mapping to the registry."""
    from ..mapper.node_mapper import NodeMapper

    mapper = NodeMapper()

    install_method = "comfy_cli" if args.comfy_cli else "git_clone"

    mapper.add_node_mapping(
        node_type=args.node_type,
        pack_name=args.pack_name or args.node_type.split("_")[0],
        repo=args.github_url,
        install_method=install_method,
        has_requirements=args.has_requirements,
        save=True
    )

    print(f"\nAdded node mapping:")
    print(f"  Node type: {args.node_type}")
    print(f"  Pack name: {args.pack_name or args.node_type.split('_')[0]}")
    print(f"  Repository: {args.github_url}")
    print(f"  Install method: {install_method}")
    print(f"\nRegistry updated successfully.")


def cmd_add_model(args):
    """Add a model URL to the registry."""
    from ..mapper.model_finder import ModelFinder

    finder = ModelFinder()

    finder.add_model(
        filename=args.filename,
        url=args.url,
        relative_path=args.path,
        size_gb=args.size or 0.0,
        description=args.description or "",
        source=args.source or "huggingface",
        save=True
    )

    print(f"\nAdded model mapping:")
    print(f"  Filename: {args.filename}")
    print(f"  URL: {args.url}")
    print(f"  Path: {args.path or '(auto-detected)'}")
    print(f"\nRegistry updated successfully.")


def cmd_analyze(args):
    """Analyze a workflow and show details."""
    from ..analyzer.workflow_analyzer import WorkflowAnalyzer
    from ..mapper.node_mapper import NodeMapper
    from ..mapper.model_finder import ModelFinder

    workflow_path = Path(args.workflow)
    if not workflow_path.exists():
        print(f"Error: Workflow file not found: {workflow_path}")
        sys.exit(1)

    print(f"\nXiCON Workflow Analyzer")
    print(f"{'='*40}")
    print(f"Workflow: {workflow_path}")
    print()

    # Analyze workflow
    analyzer = WorkflowAnalyzer()
    analysis = analyzer.analyze(workflow_path)

    print(f"Total nodes: {len(analysis.nodes)}")
    print(f"Unique node types: {len(analysis.node_types)}")
    print(f"Models referenced: {len(analysis.models)}")

    print(f"\nI/O Type:")
    print(f"  Video input:  {analysis.has_video_input}")
    print(f"  Video output: {analysis.has_video_output}")
    print(f"  Image input:  {analysis.has_image_input}")
    print(f"  Image output: {analysis.has_image_output}")

    # Map nodes
    node_mapper = NodeMapper()
    node_result = node_mapper.map_nodes(analysis.node_types)

    print(f"\n--- Node Mapping ---")
    print(f"Built-in nodes: {len(node_result.builtin)}")
    print(f"Resolved custom nodes: {len(node_result.resolved)}")
    print(f"Unresolved nodes: {len(node_result.unresolved)}")

    if node_result.required_packs:
        print(f"\nRequired node packs ({len(node_result.required_packs)}):")
        for pack in node_result.required_packs:
            print(f"  - {pack.name}")
            print(f"      {pack.repo}")

    if node_result.unresolved:
        print(f"\nUnresolved nodes ({len(node_result.unresolved)}):")
        for node in node_result.unresolved:
            print(f"  - {node}")

    # Lookup models
    model_finder = ModelFinder()
    model_filenames = [m.filename for m in analysis.models]
    model_result = model_finder.lookup(model_filenames)

    print(f"\n--- Model Lookup ---")
    print(f"Resolved models: {len(model_result.resolved)}")
    print(f"Unresolved models: {len(model_result.unresolved)}")
    print(f"Total size: {model_result.total_size_gb:.1f} GB")

    if model_result.unresolved:
        print(f"\nUnresolved models ({len(model_result.unresolved)}):")
        for model in model_result.unresolved:
            print(f"  - {model}")

    if args.verbose:
        print(f"\n--- All Node Types ---")
        for node_type in sorted(analysis.node_types):
            status = "builtin" if node_type in node_result.builtin else \
                     "resolved" if node_type in node_result.resolved else \
                     "UNRESOLVED"
            print(f"  [{status}] {node_type}")

        print(f"\n--- All Models ---")
        for model in sorted(analysis.models, key=lambda m: m.filename):
            status = "resolved" if model.filename in model_result.resolved else "UNRESOLVED"
            print(f"  [{status}] {model.filename}")


def cmd_list_registry(args):
    """List contents of registries."""
    from ..mapper.node_mapper import NodeMapper
    from ..mapper.model_finder import ModelFinder

    if args.type == "nodes" or args.type == "all":
        mapper = NodeMapper()
        print("\n=== Node Registry ===\n")

        print("Node Packs:")
        for pack_name, pack_data in mapper.node_packs.items():
            print(f"\n  {pack_name}")
            print(f"    Repo: {pack_data.get('repo', 'N/A')}")
            node_count = len(pack_data.get('nodes', []))
            print(f"    Nodes: {node_count}")

        print(f"\nBuilt-in nodes: {len(mapper.builtin_nodes)}")

    if args.type == "models" or args.type == "all":
        finder = ModelFinder()
        print("\n=== Model Registry ===\n")

        print("Models:")
        for filename, model_data in finder.models.items():
            print(f"\n  {filename}")
            print(f"    Path: {model_data.get('relative_path', 'N/A')}")
            print(f"    Size: {model_data.get('size_gb', 0):.1f} GB")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="XiCON Serverless RunPod Automation System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s generate workflow.json
  %(prog)s generate workflow.json --output ./my-project
  %(prog)s add-node WanVideoModelLoader https://github.com/kijai/ComfyUI-WanVideoWrapper
  %(prog)s add-model Wan2.1_VAE.pth https://huggingface.co/Wan-AI/Wan2.1-T2V-1.3B/resolve/main/Wan2.1_VAE.pth
  %(prog)s analyze workflow.json
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Generate command
    gen_parser = subparsers.add_parser("generate", help="Generate Dockerfile from workflow")
    gen_parser.add_argument("workflow", help="Path to ComfyUI workflow JSON file")
    gen_parser.add_argument("-o", "--output", help="Output directory (default: output/<workflow_name>)")
    gen_parser.add_argument("--base-version", default="5.5.1-base",
                           help="Base Docker image version (default: 5.5.1-base)")
    gen_parser.add_argument("--no-compose", action="store_true",
                           help="Skip docker-compose.yml generation")
    gen_parser.add_argument("--no-readme", action="store_true",
                           help="Skip README.md generation")
    gen_parser.add_argument("--copy-input", action="store_true",
                           help="Include COPY input/ command in Dockerfile")
    gen_parser.add_argument("--container-name", help="Docker container name")
    gen_parser.set_defaults(func=cmd_generate)

    # Add-node command
    node_parser = subparsers.add_parser("add-node", help="Add node mapping to registry")
    node_parser.add_argument("node_type", help="Node class_type (e.g., WanVideoModelLoader)")
    node_parser.add_argument("github_url", help="GitHub repository URL")
    node_parser.add_argument("--pack-name", help="Node pack name (default: derived from node_type)")
    node_parser.add_argument("--comfy-cli", action="store_true",
                            help="Use comfy-cli for installation instead of git clone")
    node_parser.add_argument("--has-requirements", action="store_true",
                            help="Node pack has requirements.txt")
    node_parser.set_defaults(func=cmd_add_node)

    # Add-model command
    model_parser = subparsers.add_parser("add-model", help="Add model URL to registry")
    model_parser.add_argument("filename", help="Model filename")
    model_parser.add_argument("url", help="Download URL (HuggingFace, GitHub, etc.)")
    model_parser.add_argument("--path", help="Relative path in ComfyUI (auto-detected if not specified)")
    model_parser.add_argument("--size", type=float, help="Model size in GB")
    model_parser.add_argument("--description", help="Model description")
    model_parser.add_argument("--source", choices=["huggingface", "github", "civitai"],
                             default="huggingface", help="Model source")
    model_parser.set_defaults(func=cmd_add_model)

    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze workflow without generating files")
    analyze_parser.add_argument("workflow", help="Path to ComfyUI workflow JSON file")
    analyze_parser.add_argument("-v", "--verbose", action="store_true",
                               help="Show all nodes and models")
    analyze_parser.set_defaults(func=cmd_analyze)

    # List command
    list_parser = subparsers.add_parser("list", help="List registry contents")
    list_parser.add_argument("type", choices=["nodes", "models", "all"],
                            default="all", nargs="?", help="Registry type to list")
    list_parser.set_defaults(func=cmd_list_registry)

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        sys.exit(0)

    args.func(args)


if __name__ == "__main__":
    main()
