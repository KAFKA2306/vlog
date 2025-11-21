import os
import sys

# Add src to python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from unittest.mock import MagicMock

# Mock sounddevice before it gets imported by app code
sys.modules["sounddevice"] = MagicMock()
sys.modules["soundfile"] = MagicMock()
