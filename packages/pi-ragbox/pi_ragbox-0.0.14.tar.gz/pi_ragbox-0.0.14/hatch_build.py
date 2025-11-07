"""Custom Hatchling build hook to resolve workspace dependencies.

This hook replaces workspace member dependencies (clients, data-model, indexer,
search-service) with their transitive dependencies in the wheel metadata.
It also generates and bundles type stubs for search-service and data-model.
"""

import shutil
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Set

import tomli
from hatchling.builders.hooks.plugin.interface import BuildHookInterface
from hatchling.metadata.plugin.interface import MetadataHookInterface

# Workspace members to bundle (includes search-service for dependency resolution)
ALL_WORKSPACE_MEMBERS = {
    "clients",
    "data-model",
    "indexer",
    "indexing-client",
    "indexing-model",
    "pi-ragbox",
    "retrieval-service",
    "search-service",
}

class CustomBuildHook(BuildHookInterface):
    """Build hook that conditionally includes workspace dependencies in wheels.

    For regular wheel builds, this hook force-includes workspace member source code
    into the wheel. For editable installs, it skips force-include to allow Python
    to use the editable source directories instead.
    """

    PLUGIN_NAME = "custom"

    # Workspace members to bundle
    WORKSPACE_MEMBERS_TO_BUNDLE = {
        "indexing-client": "../indexing-client/src/pilabs/indexing_client",
        "indexer": "../indexer/src/pilabs/indexer",
        "indexing-model": "../indexing-model/src/pilabs/indexing_model",
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

        for member_name, source_path in self.WORKSPACE_MEMBERS_TO_BUNDLE.items():
            # Convert relative path to absolute
            member_dir = Path(self.root) / source_path

            if member_dir.exists():
                # Map source path to target path in wheel
                target_name = member_name.replace("-", "_")
                target_path = f"pilabs/{target_name}"
                build_data["force_include"][str(member_dir)] = target_path

        # Generate and bundle type stubs for workspace packages
        self._bundle_search_service_stubs_and_templates(build_data)
        self._bundle_data_model_stubs(build_data)

    def _generate_package_stubs(
        self,
        package_name: str,
        source_dir: Path,
        exclude_patterns: List[str] = None,
    ) -> Path | None:
        """Generate type stubs for a Python package.

        Args:
            package_name: Name of the package (e.g., "search_service", "data_model")
            source_dir: Path to the package source directory
            exclude_patterns: Optional list of path patterns to exclude from stub generation

        Returns:
            Path to the bundle directory containing generated stubs, or None if generation failed
        """
        if not source_dir.exists():
            print(f"Warning: {package_name} directory not found at {source_dir}")
            return None

        # Create temporary directory for generated stubs
        temp_dir = Path(tempfile.mkdtemp())
        stub_bundle_dir = temp_dir / "stub_bundle"
        stub_bundle_dir.mkdir(parents=True)

        try:
            print(f"Generating type stubs for {package_name}...")

            from mypy import stubgen

            # Find all Python files in the package
            py_files = []
            for py_file in source_dir.rglob("*.py"):
                # Skip test files
                if py_file.name.startswith("test_"):
                    continue
                # Check if file matches any exclude pattern
                if exclude_patterns:
                    if any(pattern in str(py_file) for pattern in exclude_patterns):
                        continue
                py_files.append(str(py_file))

            if not py_files:
                print(f"Warning: No Python files found in {source_dir}")
                return None

            # Generate stubs into a subdirectory
            stubs_temp_dir = temp_dir / "generated_stubs"
            options = stubgen.parse_options(
                py_files + ["-o", str(stubs_temp_dir), "--include-private"]
            )
            stubgen.generate_stubs(options)

            # stubgen creates stubs based on module name (e.g., search_service/ or data_model/)
            # Copy them to pilabs/{package_name} structure
            generated_dir = stubs_temp_dir / package_name
            if generated_dir.exists():
                target_dir = temp_dir / "pilabs" / package_name
                target_dir.parent.mkdir(parents=True, exist_ok=True)
                shutil.copytree(generated_dir, target_dir)
                print(f"✓ Generated {len(list(target_dir.rglob('*.pyi')))} stub files")

            # The stubgen creates pilabs/{package_name}/*.pyi structure
            generated_stubs_dir = temp_dir / "pilabs" / package_name

            if not generated_stubs_dir.exists():
                print(f"Warning: Generated stubs not found for {package_name}")
                return None

            # Copy all .pyi files to bundle directory
            for pyi_file in generated_stubs_dir.rglob("*.pyi"):
                relative_path = pyi_file.relative_to(generated_stubs_dir)
                target_file = stub_bundle_dir / relative_path
                target_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(pyi_file, target_file)

            # Copy py.typed marker if it exists
            py_typed_source = source_dir / "py.typed"
            if py_typed_source.exists():
                shutil.copy2(py_typed_source, stub_bundle_dir / "py.typed")

            print(f"✓ Generated type stubs for {package_name}")
            return stub_bundle_dir

        except Exception as e:
            print(f"Warning: Error generating stubs for {package_name}: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _bundle_extra_files(
        self,
        source_dir: Path,
        target_dir: Path,
        subdirs_to_copy: List[str],
        file_filters: Dict[str, List[str]] = None,
    ) -> None:
        """Bundle extra files/directories (like templates) into the target directory.

        Args:
            source_dir: Source package directory
            target_dir: Target bundle directory
            subdirs_to_copy: List of subdirectory names to copy from source to target
            file_filters: Optional dict mapping subdirectory names to lists of specific files to copy.
                         Files are specified as relative paths from the subdirectory.
                         If not provided for a subdir, the entire subdirectory is copied.
        """
        for subdir_name in subdirs_to_copy:
            subdir_path = source_dir / subdir_name
            if not subdir_path.exists():
                continue

            target_path = target_dir / subdir_name

            # Check if this subdirectory has file filters
            if file_filters and subdir_name in file_filters:
                # Copy only specific files
                files_to_copy = file_filters[subdir_name]
                for file_rel_path in files_to_copy:
                    source_file = subdir_path / file_rel_path
                    if source_file.exists():
                        target_file = target_path / file_rel_path
                        target_file.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(source_file, target_file)
                print(f"✓ Bundled {len(files_to_copy)} files from {subdir_name}")
            else:
                # Copy entire subdirectory
                shutil.copytree(subdir_path, target_path)
                print(f"✓ Bundled extra files from {subdir_name}")

    def _bundle_search_service_stubs_and_templates(self, build_data: Dict[str, Any]) -> None:
        """Generate type stubs for search-service and bundle stubs + templates.

        Args:
            build_data: Mutable dictionary containing build metadata.
        """
        backend_dir = Path(self.root).parent
        search_service_dir = backend_dir / "search-service" / "src" / "pilabs" / "search_service"

        # Generate stubs (excluding builtin_flows from stub generation)
        stub_bundle_dir = self._generate_package_stubs(
            package_name="search_service",
            source_dir=search_service_dir,
            exclude_patterns=["builtin_flows"],
        )

        if stub_bundle_dir is None:
            return

        try:
            # Bundle template files (needed by pi-ragbox init command)
            # Only bundle the 3 files that init command actually uses
            self._bundle_extra_files(
                source_dir=search_service_dir,
                target_dir=stub_bundle_dir,
                subdirs_to_copy=["builtin_flows"],
                file_filters={
                    "builtin_flows": [
                        "pi_flows/__init__.py",
                        "pi_flows/search_simple.py",
                        "pi_flows/requirements.txt",
                    ]
                },
            )

            # Bundle everything (stubs + templates) into the wheel
            build_data["force_include"][str(stub_bundle_dir)] = "pilabs/search_service"

        except Exception as e:
            print(f"Warning: Error bundling search-service stubs: {e}")

    def _bundle_data_model_stubs(self, build_data: Dict[str, Any]) -> None:
        """Generate type stubs for data-model package.

        Args:
            build_data: Mutable dictionary containing build metadata.
        """
        backend_dir = Path(self.root).parent
        data_model_dir = backend_dir / "data-model" / "src" / "pilabs" / "data_model"

        # Generate stubs (no exclusions needed for data-model)
        stub_bundle_dir = self._generate_package_stubs(
            package_name="data_model",
            source_dir=data_model_dir,
            exclude_patterns=None,
        )

        if stub_bundle_dir is None:
            return

        try:
            # Bundle stubs into the wheel
            build_data["force_include"][str(stub_bundle_dir)] = "pilabs/data_model"

        except Exception as e:
            print(f"Warning: Error bundling data-model stubs: {e}")


class CustomMetadataHook(MetadataHookInterface):
    """Metadata hook that resolves workspace dependencies to their transitive deps."""

    PLUGIN_NAME = "custom"

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

            if pkg_name in ALL_WORKSPACE_MEMBERS:
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

                if pkg_name in ALL_WORKSPACE_MEMBERS:
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
        # Get the backend directory (parent of pi-ragbox)
        backend_dir = Path(self.root).parent
        member_dir = backend_dir / member_name

        return member_dir if member_dir.exists() else None
