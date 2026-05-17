"""
launcher.py - place this at /var/www/launcher.py (NOT inside your repo)

Starts server.py and automatically restarts it whenever it exits,
which server.py does after a successful git pull from GitHub.
"""

import subprocess
import time
import os

REPO_DIR = "/var/www/yourrepo" #replace with your repos direcory 
SERVER_SCRIPT = "/var/www/yourrepo/server.py" #replace with your repos direcory 

print(f"[launcher] Starting. Repo: {REPO_DIR}")

while True:
    print("[launcher] Starting server.py...")
    result = subprocess.run(["python3", SERVER_SCRIPT])
    code = result.returncode
    print(f"[launcher] server.py exited with code {code}. Restarting in 2s...")
    time.sleep(2)
