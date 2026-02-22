import os
import shutil
import subprocess
import sys

DB_NAME = "accessories.db"
BACKUP_NAME = "accessories.db.test_backup"

def run_tests():
    # 1. Backup production DB if it exists
    if os.path.exists(DB_NAME):
        print(f"--- Safety: Backing up {DB_NAME} to {BACKUP_NAME} ---")
        shutil.copy2(DB_NAME, BACKUP_NAME)
    
    try:
        # 2. Run tests
        print("--- Running Tests ---")
        result = subprocess.run(
            ["./venv/bin/python3", "-m", "pytest"] + sys.argv[1:],
            capture_output=False
        )
        return result.returncode
    finally:
        # 3. Restore production DB
        if os.path.exists(BACKUP_NAME):
            print(f"--- Safety: Restoring {DB_NAME} from {BACKUP_NAME} ---")
            # Clear any temporary DB created by tests if it has the same name 
            # (though tests should ideally use separate names)
            if os.path.exists(DB_NAME):
                os.remove(DB_NAME)
            shutil.move(BACKUP_NAME, DB_NAME)
        print("--- Safety: Environment Restored ---")

if __name__ == "__main__":
    exit_code = run_tests()
    sys.exit(exit_code)
