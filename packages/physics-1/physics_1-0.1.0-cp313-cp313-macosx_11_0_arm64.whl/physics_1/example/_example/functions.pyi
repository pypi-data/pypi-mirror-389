"""
Some example functions demoing pybind11
"""
from __future__ import annotations
import typing
__all__: list[str] = ['add', 'div', 'mul', 'sub']
def add(i: typing.SupportsFloat, j: typing.SupportsFloat) -> float:
    """
            Add two numbers
    """
def div(i: typing.SupportsFloat, j: typing.SupportsFloat) -> float:
    """
            Divide two numbers
    """
def mul(i: typing.SupportsFloat, j: typing.SupportsFloat) -> float:
    """
            Multiply two numbers
    """
def sub(i: typing.SupportsFloat, j: typing.SupportsFloat) -> float:
    """
            Subtract two numbers
    """
