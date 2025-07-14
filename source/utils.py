"""
Some random utility classes
"""


class DotDict(dict):
    """
    dot.notation access to dictionary attributes
    """

    def __getattr__(self, item):
        val = super().__getitem__(item)
        if isinstance(val, dict):
            return DotDict(val)
        elif isinstance(val, list):
            return [DotDict(x) for x in val]
        else:
            return val

    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__
