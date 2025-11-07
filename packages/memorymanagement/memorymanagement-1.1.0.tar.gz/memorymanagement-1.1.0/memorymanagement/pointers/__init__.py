"""
# Module `pointers`
A safe implementation of pointers written in pure Python.

It is safe beacause it doesn't imitate the internal behaviour of C pointers because it could break the memory.
It only replicates the visible effects and behaviour of C pointers.
## Class `Pointer`
This is the core of the module. The class `Pointer` points to a specific reference,
which will be syncrhonized with the pointer's value since the moment of the pointer's creation.
## Decorator `pointerize`
This decorator makes any function able to receive `Pointer` objects instead of the originally expected.
"""
# Import from modules
from .core import Pointer # Class "Pointer"
from .decorators import pointerize # Decorator "pointerize"