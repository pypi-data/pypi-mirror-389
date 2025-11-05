"""
FlyConf Parser - A parser for fc configuration files.
"""

__version__ = "0.1.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

from .parser import FCConfigParser
from .model import FCConfig, FCBlock
from .transformer import ConfigTransformer

__all__ = ["FCConfigParser", "FCConfig", "FCBlock", "ConfigTransformer"]