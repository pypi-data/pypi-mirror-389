"""Custom Hatchling build hook to resolve workspace dependencies.

This hook replaces workspace member dependencies (clients, data-model, indexer,
search-service) with their transitive dependencies in the wheel metadata.
It also generates and bundles type stubs for search-service.
"""

import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Set

import tomli
from hatchling.builders.hooks.plugin.interface import BuildHookInterface
from hatchling.metadata.plugin.interface import MetadataHookInterface


class CustomBuildHook(BuildHookInterface):
    """Build hook that conditionally includes workspace dependencies in wheels.

    For regular wheel builds, this hook force-includes workspace member source code
    into the wheel. For editable installs, it skips force-include to allow Python
    to use the editable source directories instead.
    """

    PLUGIN_NAME = "custom"

    # Workspace members to bundle
    WORKSPACE_MEMBERS = {
        "clients": "../clients/src/pilabs/clients",
        "data-model": "../data-model/src/pilabs/data_model",
        "indexer": "../indexer/src/pilabs/indexer",
    }

    def initialize(self, version: str, build_data: Dict[str, Any]) -> None:
        """Initialize build hook before each build.

        Args:
            version: The version being built. Equals "editable" for editable installs.
            build_data: Mutable dictionary containing build metadata.
        """
        # Only apply force-include for regular wheel builds, not editable installs
        if version == "editable":
            # For editable installs, skip force-include to use source directories
            return

        # For regular wheel builds, force-include workspace members
        if "force_include" not in build_data:
            build_data["force_include"] = {}

        for member_name, source_path in self.WORKSPACE_MEMBERS.items():
            # Convert relative path to absolute
            member_dir = Path(self.root) / source_path

            if member_dir.exists():
                # Map source path to target path in wheel
                target_name = member_name.replace("-", "_")
                target_path = f"pilabs/{target_name}"
                build_data["force_include"][str(member_dir)] = target_path

        # Generate and bundle search-service type stubs and templates
        self._bundle_search_service_stubs_and_templates(build_data)

    def _bundle_search_service_stubs_and_templates(self, build_data: Dict[str, Any]) -> None:
        """Generate type stubs for search-service and bundle stubs + templates.

        Args:
            build_data: Mutable dictionary containing build metadata.
        """
        backend_dir = Path(self.root).parent
        search_service_dir = backend_dir / "search-service" / "src" / "pilabs" / "search_service"

        if not search_service_dir.exists():
            print(f"Warning: search-service directory not found at {search_service_dir}")
            return

        # Create temporary directory for generated stubs
        temp_dir = Path(tempfile.mkdtemp())
        stub_bundle_dir = temp_dir / "stub_bundle"
        stub_bundle_dir.mkdir(parents=True)

        try:
            # Generate stub files by parsing source (no imports needed)
            print("Generating type stubs for search-service...")

            try:
                from mypy import stubgen
                # Generate stubs by parsing source files directly (no imports needed)
                # Find all Python files in search-service
                py_files = []
                for py_file in search_service_dir.rglob("*.py"):
                    # Skip builtin_flows templates
                    if "builtin_flows" not in str(py_file):
                        py_files.append(str(py_file))

                if py_files:
                    # Generate stubs into a subdirectory
                    stubs_temp_dir = temp_dir / "generated_stubs"
                    options = stubgen.parse_options(
                        py_files + ["-o", str(stubs_temp_dir), "--include-private"]
                    )
                    stubgen.generate_stubs(options)

                    # stubgen creates stubs based on module name (search_service/)
                    # Copy them to pilabs/search_service structure
                    generated_dir = stubs_temp_dir / "search_service"
                    if generated_dir.exists():
                        target_dir = temp_dir / "pilabs" / "search_service"
                        target_dir.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copytree(generated_dir, target_dir)
                        print(f"✓ Generated {len(list(target_dir.rglob('*.pyi')))} stub files")
            except Exception as e:
                print(f"Warning: stubgen error: {e}")
                import traceback
                traceback.print_exc()

            # The stubgen creates pilabs/search_service/*.pyi structure
            generated_stubs_dir = temp_dir / "pilabs" / "search_service"

            if generated_stubs_dir.exists():
                # Copy all .pyi files
                for pyi_file in generated_stubs_dir.rglob("*.pyi"):
                    relative_path = pyi_file.relative_to(generated_stubs_dir)
                    target_file = stub_bundle_dir / relative_path
                    target_file.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(pyi_file, target_file)

                # Copy py.typed marker
                py_typed_source = search_service_dir / "py.typed"
                if py_typed_source.exists():
                    shutil.copy2(py_typed_source, stub_bundle_dir / "py.typed")

                print("✓ Generated type stubs for search-service")

            # Bundle template files (needed by pi-ragbox init command) into the same directory
            builtin_flows_dir = search_service_dir / "builtin_flows"
            if builtin_flows_dir.exists():
                # Copy template files into the stub bundle directory
                shutil.copytree(builtin_flows_dir, stub_bundle_dir / "builtin_flows")
                print("✓ Bundled template files from builtin_flows")

            # Bundle everything (stubs + templates) into the wheel
            build_data["force_include"][str(stub_bundle_dir)] = "pilabs/search_service"

        except subprocess.CalledProcessError as e:
            print(f"Warning: Failed to generate stubs for search-service: {e}")
            print(f"stdout: {e.stdout}")
            print(f"stderr: {e.stderr}")
        except Exception as e:
            print(f"Warning: Error bundling search-service stubs: {e}")
        finally:
            # Clean up temp directory after build (hatchling will copy files during build)
            # We don't delete immediately as build_data references these paths
            pass


class CustomMetadataHook(MetadataHookInterface):
    """Metadata hook that resolves workspace dependencies to their transitive deps."""

    PLUGIN_NAME = "custom"

    # Workspace members to bundle (includes search-service for dependency resolution)
    WORKSPACE_MEMBERS = {"clients", "data-model", "indexer", "search-service"}

    def update(self, metadata: Dict[str, Any]) -> None:
        """Update metadata by replacing workspace deps with transitive deps."""
        if "dependencies" not in metadata:
            return

        original_deps = metadata["dependencies"]
        resolved_deps = self._resolve_dependencies(original_deps)
        metadata["dependencies"] = sorted(resolved_deps)

    def _resolve_dependencies(self, dependencies: List[str]) -> Set[str]:
        """Resolve workspace dependencies to their transitive dependencies.

        Args:
            dependencies: List of dependency specifications (e.g., ["clients", "httpx>=0.27.0"])

        Returns:
            Set of resolved dependency specifications with workspace deps replaced
        """
        # Collect all dependencies in a dict keyed by package name
        # This allows us to merge version constraints for duplicate packages
        dep_dict: Dict[str, List[str]] = {}

        for dep in dependencies:
            # Extract package name (everything before <, >, =, [, etc.)
            pkg_name = (
                dep.split("[")[0]
                .split("<")[0]
                .split(">")[0]
                .split("=")[0]
                .split("!")[0]
                .strip()
            )

            if pkg_name in self.WORKSPACE_MEMBERS:
                # Resolve workspace member to its transitive dependencies
                transitive_deps = self._get_transitive_deps(pkg_name)
                for tdep in transitive_deps:
                    tpkg_name = (
                        tdep.split("[")[0]
                        .split("<")[0]
                        .split(">")[0]
                        .split("=")[0]
                        .split("!")[0]
                        .strip()
                    )
                    if tpkg_name not in dep_dict:
                        dep_dict[tpkg_name] = []
                    dep_dict[tpkg_name].append(tdep)
            else:
                # Keep non-workspace dependencies
                if pkg_name not in dep_dict:
                    dep_dict[pkg_name] = []
                dep_dict[pkg_name].append(dep)

        # Merge duplicate dependencies by taking the most specific version constraint
        resolved = set()
        for pkg_name, specs in dep_dict.items():
            if len(specs) == 1:
                resolved.add(specs[0])
            else:
                # Multiple specs for same package - take the most restrictive
                resolved.add(self._merge_specs(specs))

        return resolved

    def _merge_specs(self, specs: List[str]) -> str:
        """Merge multiple dependency specifications for the same package.

        For now, we just take the first specification with a version constraint,
        or the last one if none have constraints. A more sophisticated approach
        would parse and merge the version constraints properly.

        Args:
            specs: List of dependency specs for the same package

        Returns:
            Merged dependency specification
        """
        # Prefer specs with extras or version constraints
        for spec in specs:
            if "[" in spec or any(op in spec for op in ["<", ">", "=", "!", "~"]):
                return spec
        return specs[-1]

    def _get_transitive_deps(self, workspace_member: str) -> Set[str]:
        """Get all transitive dependencies for a workspace member.

        Args:
            workspace_member: Name of the workspace member package

        Returns:
            Set of all transitive dependency specifications
        """
        visited = set()
        all_deps = set()

        def collect_deps(member_name: str) -> None:
            """Recursively collect dependencies."""
            if member_name in visited:
                return
            visited.add(member_name)

            # Read the workspace member's pyproject.toml
            member_dir = self._get_member_directory(member_name)
            if not member_dir:
                return

            pyproject_path = member_dir / "pyproject.toml"
            if not pyproject_path.exists():
                return

            with open(pyproject_path, "rb") as f:
                pyproject = tomli.load(f)

            # Get direct dependencies
            deps = pyproject.get("project", {}).get("dependencies", [])

            for dep in deps:
                # Extract package name
                pkg_name = (
                    dep.split("[")[0]
                    .split("<")[0]
                    .split(">")[0]
                    .split("=")[0]
                    .split("!")[0]
                    .strip()
                )

                if pkg_name in self.WORKSPACE_MEMBERS:
                    # Recursively resolve workspace dependencies
                    collect_deps(pkg_name)
                else:
                    # Add external dependency
                    all_deps.add(dep)

        collect_deps(workspace_member)
        return all_deps

    def _get_member_directory(self, member_name: str) -> Path | None:
        """Get the directory path for a workspace member.

        Args:
            member_name: Name of the workspace member package

        Returns:
            Path to the member directory, or None if not found
        """
        # Map package names to directory names
        name_map = {
            "clients": "clients",
            "data-model": "data-model",
            "indexer": "indexer",
            "search-service": "search-service",
        }

        dir_name = name_map.get(member_name)
        if not dir_name:
            return None

        # Get the backend directory (parent of pi-ragbox)
        backend_dir = Path(self.root).parent
        member_dir = backend_dir / dir_name

        return member_dir if member_dir.exists() else None
