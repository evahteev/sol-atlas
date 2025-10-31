#!/usr/bin/env python3
"""Fix SQLAlchemy 2.0 compatibility in migration files"""

import os
import re
from pathlib import Path

migrations_dir = Path(__file__).parent / "migrations" / "versions"

for migration_file in migrations_dir.glob("*.py"):
    print(f"Processing {migration_file.name}...")
    
    with open(migration_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Add text import if not present and file contains execute with string
    if 'from sqlalchemy import text' not in content and 'op.get_bind().execute(' in content:
        # Find the import section
        import_match = re.search(r'(from alembic import op\n)', content)
        if import_match:
            content = content.replace(
                import_match.group(1),
                import_match.group(1) + 'from sqlalchemy import text\n'
            )
    
    # Fix execute calls with raw strings
    content = re.sub(
        r'op\.get_bind\(\)\.execute\("([^"]+)"\)',
        r'op.get_bind().execute(text("\1"))',
        content
    )
    
    content = re.sub(
        r"op\.get_bind\(\)\.execute\('([^']+)'\)",
        r"op.get_bind().execute(text('\1'))",
        content
    )
    
    # Write back if changed
    if content != original_content:
        with open(migration_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  ✓ Fixed {migration_file.name}")
    else:
        print(f"  - No changes needed for {migration_file.name}")

print("\n✅ All migrations fixed!")



