# Launch the restricted bot using module path
import sys
import os
import subprocess

if __name__ == "__main__":
    # Ensure current directory is in Python path
    sys.path.append(os.path.abspath(os.path.dirname(__file__)))

    # Run the main module using python -m main
    print("Launching SaveRestrictedContentBot...")
    subprocess.run([sys.executable, "-m", "main"])
