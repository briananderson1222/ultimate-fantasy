#!/usr/bin/env python3

"""
Automatically update contract tests to use authenticated clients.
"""

import os
import re
from pathlib import Path

def update_test_file(file_path):
    """Update a single test file to use authenticated clients."""
    print(f"Updating {file_path}...")

    with open(file_path, 'r') as f:
        content = f.read()

    original_content = content

    # Remove setup_method that creates TestClient
    content = re.sub(
        r'    def setup_method\(self\):\s*\n        """Set up test client\."""\s*\n        self\.client = TestClient\(app\)\s*\n',
        '    # Removed setup_method - using authenticated_client fixture instead\n',
        content
    )

    # Update method signatures to include authenticated_client parameter
    content = re.sub(
        r'def (test_[^(]+)\(self\):',
        r'def \1(self, authenticated_client):',
        content
    )

    # Replace self.client.get/post/patch/etc with authenticated_client
    content = re.sub(r'self\.client\.(get|post|patch|put|delete)', r'authenticated_client.\1', content)

    # Handle special cases where methods don't need authentication (like 401 tests)
    # These should use unauthenticated_client instead
    auth_test_patterns = [
        'without_auth',
        'invalid_token',
        'unauthorized',
        'missing_auth',
        'no_auth'
    ]

    for pattern in auth_test_patterns:
        # Update methods that test auth failures to use unauthenticated_client
        content = re.sub(
            rf'def (test_[^(]*{pattern}[^(]*)\(self, authenticated_client\):',
            r'def \1(self, unauthenticated_client):',
            content,
            flags=re.IGNORECASE
        )
        # Update the client calls for auth tests
        content = re.sub(
            rf'(def test_[^(]*{pattern}[^:]*:.*?)authenticated_client\.(get|post|patch|put|delete)',
            r'\1unauthenticated_client.\2',
            content,
            flags=re.DOTALL | re.IGNORECASE
        )

    if content != original_content:
        with open(file_path, 'w') as f:
            f.write(content)
        print(f"✓ Updated {file_path}")
        return True
    else:
        print(f"- No changes needed for {file_path}")
        return False

def main():
    """Update all contract test files."""
    test_dir = Path("tests/contract")
    updated_files = []

    for test_file in test_dir.glob("test_*.py"):
        if update_test_file(test_file):
            updated_files.append(test_file)

    print(f"\n✅ Updated {len(updated_files)} files:")
    for file in updated_files:
        print(f"  - {file}")

    print(f"\n🔧 Next step: Test the updates with pytest")

if __name__ == "__main__":
    main()