"""
Some random utility classes
"""


class DotDict(dict):
    """
    dot.notation access to dictionary attributes
    """

    def __getattr__(self, item):
        val = super().__getitem__(item)
        return DotDict(val) if type(val) is dict else val

    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__
