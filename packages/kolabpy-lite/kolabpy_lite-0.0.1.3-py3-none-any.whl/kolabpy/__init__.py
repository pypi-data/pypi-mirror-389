# __init__.py
from .SASLogin import SASLogin
from .Kosispy import Kosispy

def setup_java_colab():
    from IPython import get_ipython
    ip = get_ipython()
    if ip is None:
        raise RuntimeError("Not in Colab/IPython; run this in a Colab cell.")
    ip.run_line_magic("bash", "apt-get -qq update && apt-get -qq install -y openjdk-11-jdk-headless")
    import os
    os.environ["JAVA_HOME"] = "/usr/bin/java"
    os.environ["PATH"] += os.pathsep + os.path.join(os.environ["JAVA_HOME"], "bin")