"""

        Physics 1 Example Module
        -----------------------

        .. currentmodule:: physics_1

        .. autosummary::
           :toctree: _generate
    
"""
from __future__ import annotations
from physics_1.example._example import functions
from . import _example
__all__: list = ['__doc__', '__version__', 'functions']
__version__: str = '0.1.0'
