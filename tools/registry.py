"""Safe local tools. No model-generated shell or arbitrary code execution."""
import platform
import subprocess
from collections.abc import Callable
from pathlib import Path
from typing import Any, ClassVar
