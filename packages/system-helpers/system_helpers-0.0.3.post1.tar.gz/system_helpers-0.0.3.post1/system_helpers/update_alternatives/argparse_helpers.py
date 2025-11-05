import argparse

import typeguard

class ParseKwargs(argparse.Action):
    """
    Parse dictionary-like key-value pairs.

    References:
        * https://sumit-ghosh.com/posts/parsing-dictionary-key-value-pairs-kwargs-argparse-python/
    """
    @typeguard.typechecked
    def __call__(self, parser : argparse.ArgumentParser, namespace : argparse.Namespace, values : list, *args, **kwargs):
        setattr(namespace, self.dest, dict())
        for value in values:
            key, value = value.split('=', 2)
            getattr(namespace, self.dest)[key] = value
