"""
# Module `cleaning`
Implements the class `Cleaner` to keep track of the references and erase it easily.
## Overview
Initialize a `Cleaner` object:
```
# Default arguments' values
cleaner=Cleaner(
    not_delete:list[str]=list(vars(modules["main"])), # List of global variables at that moment (modules comes from sys library)
    excluded:list[str]=[], # Empty list to be modified later if you need
    flagged:list[str]=[] # List of references to undo
)
```
Now `cleaner` has the following attributes:
```
cleaner._not_delete=list(vars(modules["main"])) # At initialization moment
cleaner._excluded=[] # Wasn't asked to exclude any reference.
cleaner._flagged=[] # Wasn't asked to include any reference.
```
To automatically include all the new references, use the `.update()` method:
```
x=10
y="Hello world"
z=f"Hello Python for time number {x}"
# Default arguments' values
cleaner.update(
    exclude:str|list[str]|tuple[str]|None=None, # Excludes flagged or yet not created references from the process
    include:str|list[str]|tuple[str]|None=None # Includes references into the process
)
print(cleaner)
```
The cell above prints (via `__str__` method):
```
Flagged: ["x","y","z"]

Excluded: []

Not delete: <list(vars(modules["main"]))> # Unchanged since initialization
"""
# Imports
from .core import Cleaner