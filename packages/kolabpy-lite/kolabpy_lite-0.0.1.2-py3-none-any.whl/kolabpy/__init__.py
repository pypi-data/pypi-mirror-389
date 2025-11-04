# __init__.py
from .SASLogin import SASLogin
from .Kosispy import Kosispy
from IPython import get_ipython
import os

try:
    ipython = get_ipython()
    ipython.run_cell_magic(
    "bash", "",
    "apt-get -qq update && apt-get -qq install -y openjdk-11-jdk-headless"
)
    os.environ["JAVA_HOME"] = "/usr/bin/java"
except Exception as e:
    print(f"[WARN] Java installation failed : {e}")