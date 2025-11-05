"""
Wrapper module for git-contrib-tree.

This wrapper allows us to keep the git-contrib-tree filename (with dash)
while providing a valid Python module for package entry points.
"""

import importlib.util
import sys
from pathlib import Path


def main():
    """Entry point that loads and executes git-contrib-tree."""
    # Find the script in the same directory as this wrapper
    script_path = Path(__file__).parent / "git-contrib-tree"
    
    if not script_path.exists():
        print(f"Error: Could not find git-contrib-tree at {script_path}", file=sys.stderr)
        sys.exit(1)
    
    # Use spec_from_loader with SourceFileLoader to load files without .py extension
    from importlib.machinery import SourceFileLoader
    loader = SourceFileLoader("git_contrib_tree_mod", str(script_path))
    spec = importlib.util.spec_from_loader("git_contrib_tree_mod", loader)
    
    if spec is None or spec.loader is None:
        print(f"Error: Could not create loader for git-contrib-tree from {script_path}", file=sys.stderr)
        sys.exit(1)
    
    module = importlib.util.module_from_spec(spec)
    sys.modules["git_contrib_tree_mod"] = module
    spec.loader.exec_module(module)
    
    # Execute the main function from the loaded module
    return module.main()


if __name__ == "__main__":
    sys.exit(main())
