# __init__.py
from .SASLogin import SASLogin
from .Kosispy import Kosispy

import os
import subprocess

# --- Force install OpenJDK 11 quietly ---
try:
    subprocess.run(["apt-get", "update", "-qq"], check=True)
    subprocess.run(["apt-get", "install", "-y", "openjdk-11-jdk-headless", "-qq"], check=True)

    # Set environment variable as you specified
    os.environ["JAVA_HOME"] = "/usr/bin/java"
except Exception as e:
    print(f"[WARN] Java installation failed or skipped: {e}")