try:
    from setuptools_scm import get_version
    # Using a relative path for relative_to doesn't work, because it will be relative to the current working
    # directory (which could be anywhere)
    # __file__ is the location of this init file (a full path), and this gives us a predictable path to the root
    # (namely: two levels up)
    # Note that if we ever move this __init__ file relative to the root of the git tree, we'll need to adjust this
    __version__ = get_version(root='../..', relative_to=__file__)
except ImportError:
    __version__ = "0.0.0"  # fallback version if setuptools_scm is not available
