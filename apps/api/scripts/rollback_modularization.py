#!/usr/bin/env python3
"""
Rollback script for backend modularization.

This script reverts the modularized domain structure back to the original
monolithic structure. Use with caution in production environments.

Usage:
    python scripts/rollback_modularization.py [--dry-run] [--backup]
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


class ModularizationRollback:
    """Handles rollback of backend modularization."""

    def __init__(self, dry_run: bool = False, create_backup: bool = True):
        self.dry_run = dry_run
        self.create_backup = create_backup
        self.backend_path = Path(__file__).parent.parent
        self.backup_path = self.backend_path / "backup_before_rollback"

        # Files/directories created during modularization
        self.modularization_artifacts = [
            "src/domains",
            "src/infrastructure",
            "tests/contracts",
            "tests/integration",
            "tests/domains",
            "tests/performance",
        ]

        # Files that need import path restoration
        self.files_to_restore_imports = [
            "src/api/deps.py",
            "src/api/middleware/auth.py",
            "src/main.py",
        ]

    def log(self, message: str, level: str = "INFO") -> None:
        """Log a message with level."""
        prefix = "[DRY-RUN] " if self.dry_run else ""
        print(f"{prefix}[{level}] {message}")  # noqa: T201

    def create_backup_if_requested(self) -> None:
        """Create backup of current state before rollback."""
        if not self.create_backup:
            return

        if self.backup_path.exists():
            self.log(f"Removing existing backup at {self.backup_path}")
            if not self.dry_run:
                shutil.rmtree(self.backup_path)

        self.log(f"Creating backup at {self.backup_path}")
        if not self.dry_run:
            shutil.copytree(
                self.backend_path,
                self.backup_path,
                ignore=shutil.ignore_patterns(".git", "__pycache__", "*.pyc", ".venv"),
            )

    def restore_from_git_history(self) -> bool:
        """Attempt to restore files from git history before modularization."""
        try:
            # Find the commit before modularization started
            self.log("Looking for pre-modularization commit...")
            result = subprocess.run(
                ["git", "log", "--oneline", "--grep=modular", "-n", "20"],  # noqa: S607
                check=False,
                capture_output=True,
                text=True,
                cwd=self.backend_path,
            )

            if result.returncode != 0:
                self.log("Could not access git history", "WARNING")
                return False

            commits = result.stdout.strip().split("\n")
            if not commits:
                self.log("No modularization commits found in recent history", "WARNING")
                return False

            # Get the commit before the first modularization commit
            first_modular_commit = commits[-1].split()[0]
            self.log(f"Found first modularization commit: {first_modular_commit}")

            pre_modular_commit = f"{first_modular_commit}~1"

            # Restore key files from before modularization
            files_to_restore = [
                "src/main.py",
                "src/services/",
                "src/api/",
            ]

            for file_path in files_to_restore:
                self.log(f"Restoring {file_path} from {pre_modular_commit}")
                if not self.dry_run:
                    try:
                        subprocess.run(  # noqa: S603
                            [  # noqa: S607
                                "git",
                                "checkout",
                                pre_modular_commit,
                                "--",
                                file_path,
                            ],
                            cwd=self.backend_path,
                            check=True,
                        )
                    except subprocess.CalledProcessError:
                        self.log(f"Could not restore {file_path}", "WARNING")

            return True

        except Exception as e:
            self.log(f"Git history restoration failed: {e}", "ERROR")
            return False

    def remove_modularization_artifacts(self) -> None:
        """Remove directories and files created during modularization."""
        for artifact in self.modularization_artifacts:
            artifact_path = self.backend_path / artifact
            if artifact_path.exists():
                self.log(f"Removing modularization artifact: {artifact}")
                if not self.dry_run:
                    if artifact_path.is_dir():
                        shutil.rmtree(artifact_path)
                    else:
                        artifact_path.unlink()

    def restore_original_imports(self) -> None:
        """Restore import statements to pre-modularization state."""
        import_replacements = {
            "from domains.": "from services.",
            "from infrastructure.": "from services.",
            # Add more replacements as needed
        }

        for file_path in self.files_to_restore_imports:
            full_path = self.backend_path / file_path
            if not full_path.exists():
                continue

            self.log(f"Restoring imports in {file_path}")
            if not self.dry_run:
                try:
                    with open(full_path) as f:
                        content = f.read()

                    # Apply import replacements
                    original_content = content
                    for old_import, new_import in import_replacements.items():
                        content = content.replace(old_import, new_import)

                    if content != original_content:
                        with open(full_path, "w") as f:
                            f.write(content)
                        self.log(f"Updated imports in {file_path}")

                except Exception as e:
                    self.log(f"Error updating imports in {file_path}: {e}", "ERROR")

    def restore_models_structure(self) -> None:
        """Restore models to original structure."""
        # Check if models were moved to domains
        original_models_path = self.backend_path / "src" / "models"

        if not original_models_path.exists():
            self.log("Creating original models directory")
            if not self.dry_run:
                original_models_path.mkdir(parents=True)

        # Move models back from domains if they exist
        domains_path = self.backend_path / "src" / "domains"
        if domains_path.exists():
            for domain_dir in domains_path.iterdir():
                if domain_dir.is_dir():
                    models_dir = domain_dir / "models"
                    if models_dir.exists():
                        self.log(
                            f"Moving models from {domain_dir.name} domain back to models/"
                        )
                        if not self.dry_run:
                            for model_file in models_dir.glob("*.py"):
                                if model_file.name != "__init__.py":
                                    target = original_models_path / model_file.name
                                    if not target.exists():
                                        shutil.copy2(model_file, target)

    def update_pyproject_toml(self) -> None:
        """Restore pyproject.toml to pre-modularization state."""
        pyproject_path = self.backend_path / "pyproject.toml"

        if not pyproject_path.exists():
            return

        self.log("Updating pyproject.toml")
        if not self.dry_run:
            try:
                with open(pyproject_path) as f:
                    content = f.read()

                # Remove modularization-specific dependencies if any were added
                # This is a placeholder - adjust based on actual changes made

                with open(pyproject_path, "w") as f:
                    f.write(content)

            except Exception as e:
                self.log(f"Error updating pyproject.toml: {e}", "ERROR")

    def run_rollback(self) -> bool:
        """Execute the complete rollback process."""
        self.log("Starting modularization rollback")

        if self.dry_run:
            self.log("DRY RUN MODE - No changes will be made")

        try:
            # Step 1: Create backup
            self.create_backup_if_requested()

            # Step 2: Try to restore from git history
            git_success = self.restore_from_git_history()

            # Step 3: Remove modularization artifacts
            self.remove_modularization_artifacts()

            # Step 4: Restore import statements (if git restore didn't work)
            if not git_success:
                self.restore_original_imports()
                self.restore_models_structure()

            # Step 5: Update configuration files
            self.update_pyproject_toml()

            self.log("Rollback completed successfully")

            if not self.dry_run:
                self.log("IMPORTANT: Run tests to verify the rollback worked correctly")
                self.log("IMPORTANT: You may need to manually adjust some imports")
                if self.create_backup:
                    self.log(f"Backup created at: {self.backup_path}")

            return True

        except Exception as e:
            self.log(f"Rollback failed: {e}", "ERROR")
            return False


def main() -> None:
    """Main entry point for rollback script."""
    parser = argparse.ArgumentParser(
        description="Rollback backend modularization changes"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without making changes",
    )
    parser.add_argument(
        "--no-backup", action="store_true", help="Skip creating backup before rollback"
    )

    args = parser.parse_args()

    rollback = ModularizationRollback(
        dry_run=args.dry_run, create_backup=not args.no_backup
    )

    success = rollback.run_rollback()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
