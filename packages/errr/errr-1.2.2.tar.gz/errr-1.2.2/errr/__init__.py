"""
Elegant detailed Python exceptions.
"""

from .exception import DetailedException
from .tree import make_tree, exception

__version__ = "1.2.2"

def wrap(err_type, *args, **kwargs):
    return err_type.wrap(*args, **kwargs)


def quotejoin(itr, delim=", ", quote="'", f=str):
    return delim.join(f"{quote}{f(o)}{quote}" for o in itr)
