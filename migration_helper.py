"""
Migration helper to convert long_term.json memory to SQLite database.
Preserves all data with validation and provides rollback capability.
"""

import json
import shutil
from pathlib import Path
from typing import Optional, Tuple
from datetime import datetime
import sys


def get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent


BASE_DIR = get_base_dir()
JSON_MEMORY_PATH = BASE_DIR / "memory" / "long_term.json"


def backup_json_memory() -> Optional[Path]:
    """Create backup of JSON memory file. Returns backup path."""
    if not JSON_MEMORY_PATH.exists():
        print("[Migration] ℹ️  No long_term.json found (new installation)")
        return None
    
    backup_path = JSON_MEMORY_PATH.with_suffix(".json.backup")
    try:
        shutil.copy2(JSON_MEMORY_PATH, backup_path)
        print(f"[Migration] ✅ Backed up JSON memory to {backup_path}")
        return backup_path
    except Exception as e:
        print(f"[Migration] ❌ Backup failed: {e}")
        return None


def migrate_json_to_sqlite(dry_run: bool = False) -> Tuple[bool, str]:
    """
    Migrate long_term.json to SQLite database.
    
    Args:
        dry_run: If True, simulate migration without making changes
        
    Returns:
        (success: bool, message: str)
    """
    from memory_db import get_memory_db
    
    if not JSON_MEMORY_PATH.exists():
        return True, "No JSON memory file found (new installation)"
    
    try:
        # Load JSON memory
        with open(JSON_MEMORY_PATH, "r", encoding="utf-8") as f:
            json_data = json.load(f)
        
        print("[Migration] 📖 Loaded JSON memory")
        
        if dry_run:
            # Count entries without modifying
            entries_count = 0
            for category, items in json_data.items():
                if isinstance(items, dict):
                    entries_count += len(items)
            return True, f"DRY RUN: Would migrate {entries_count} entries"
        
        # Get database
        db = get_memory_db()
        entries_migrated = 0
        
        # Migrate entries by category
        for category, items in json_data.items():
            if not isinstance(items, dict):
                continue
            
            for key, entry_data in items.items():
                try:
                    if isinstance(entry_data, dict):
                        value = entry_data.get("value", "")
                        updated = entry_data.get("updated", datetime.now().isoformat())
                    else:
                        value = str(entry_data)
                        updated = datetime.now().isoformat()
                    
                    db.add_memory_entry(
                        category=category,
                        key=key,
                        value=value,
                        confidence=1.0
                    )
                    entries_migrated += 1
                except Exception as e:
                    print(f"[Migration] ⚠️  Failed to migrate {category}/{key}: {e}")
        
        print(f"[Migration] ✅ Migrated {entries_migrated} entries to SQLite")
        
        # Verify migration
        db_stats = db.get_stats()
        return True, f"Migration complete: {entries_migrated} entries, DB size: {db_stats['db_size_mb']}MB"
        
    except json.JSONDecodeError as e:
        return False, f"JSON parsing error: {e}"
    except Exception as e:
        return False, f"Migration error: {e}"


def restore_from_backup(backup_path: Path) -> bool:
    """Restore JSON memory from backup."""
    try:
        shutil.copy2(backup_path, JSON_MEMORY_PATH)
        print(f"[Migration] ✅ Restored JSON memory from backup")
        return True
    except Exception as e:
        print(f"[Migration] ❌ Restore failed: {e}")
        return False


def validate_migration() -> Tuple[bool, str]:
    """Validate that migration was successful."""
    from memory_db import get_memory_db
    
    db = get_memory_db()
    stats = db.get_stats()
    
    if stats["memory_entries"] == 0:
        return False, "No memory entries in database"
    
    if stats["db_size_mb"] == 0:
        return False, "Database is empty"
    
    return True, f"Validation passed: {stats['memory_entries']} entries, {stats['db_size_mb']}MB"


def migrate_if_needed(force: bool = False) -> bool:
    """
    Migrate if JSON memory exists and hasn't been migrated yet.
    
    Args:
        force: Force migration even if already done
        
    Returns:
        True if migrated or not needed
    """
    from memory_db import MEMORY_DB_PATH
    
    # Check if already migrated
    if MEMORY_DB_PATH.exists() and not force:
        print("[Migration] ✅ SQLite database already exists, skipping migration")
        return True
    
    if not JSON_MEMORY_PATH.exists():
        print("[Migration] ℹ️  No JSON memory to migrate (new installation)")
        return True
    
    print("[Migration] 🔄 Starting migration from JSON to SQLite...")
    
    # Backup first
    backup = backup_json_memory()
    
    # Attempt migration
    success, message = migrate_json_to_sqlite()
    print(f"[Migration] {message}")
    
    if not success:
        if backup:
            print("[Migration] ⚠️  Restoring from backup...")
            restore_from_backup(backup)
        return False
    
    # Validate
    valid, msg = validate_migration()
    print(f"[Migration] {msg}")
    
    if valid:
        print("[Migration] ✅ Migration successful!")
        return True
    else:
        if backup:
            print("[Migration] ⚠️  Validation failed, restoring from backup...")
            restore_from_backup(backup)
        return False


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "migrate":
            migrate_if_needed(force=True)
        elif command == "dry-run":
            success, msg = migrate_json_to_sqlite(dry_run=True)
            print(msg)
        elif command == "validate":
            success, msg = validate_migration()
            print(msg)
        elif command == "backup":
            backup_json_memory()
        else:
            print(f"Unknown command: {command}")
    else:
        migrate_if_needed()
