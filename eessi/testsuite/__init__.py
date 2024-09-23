# WARNING: this file is imported in setup.py
# To make sure this works, we should avoid using imports other than from the Python standard library
try:
    # If this is an installed package, setuptools_scm will have written the _version.py file in the current directory
    from ._version import __version__
except ImportError:
    # Fallback for when the package is not installed, but git cloned. Note that this requires setuptools_scm to be
    # available as a runtime dependency
    # The advantage here is that it will generate development versions if not on a tagged release version
    try:
        from setuptools_scm import get_version
        # Using a relative path for relative_to doesn't work, because it will be relative to the current working
        # directory (which could be anywhere)
        # __file__ is the location of this init file (a full path), and this gives us a predictable path to the root
        # (namely: two levels up)
        # Note that if we ever move this __init__ file relative to the root of the git tree, we'll need to adjust this
        __version__ = get_version(root='../..', relative_to=__file__)
    except ImportError:
        # If running from a tarball (e.g. release tarball) downloaded from github, we will not have the .git
        # folder available. Thus, setuptools_scm cannot determine the version in any way. Thus, use the
        # fallback_version from the pyproject.toml file (which doesn't exist when this is installed as a package,
        # but SHOULD exist when this is run from a downloaded tarball from git)

        # Pyproject.toml should be two levels up from this file
        pyproject_toml = "%s/../../pyproject.toml" % os.path.dirname(__file__)

        # Variables to track if we're in the right section and to store the fallback_version
        in_setuptools_scm_section = False
        fallback_version = None

        try:
            file = open(pyproject_toml, 'r')
        except FileNotFoundError:
            msg = "File %s not found when trying to extract the EESSI test suite version from pyproject.toml."
            msg += "This should never happen. Please report an issue on GitHub, including information on how you"
            msg += " installed the EESSI test suite. Defaulting to version 0.0.0"
            print(msg)
            __version__ = "0.0.0"

        # Open the file and parse it manually
        __version__ = None
        with file:
            for line in file:
                stripped_line = line.strip()

                # Check if we're entering the [tool.setuptools_scm] section
                if stripped_line == "[tool.setuptools_scm]":
                    in_setuptools_scm_section = True
                elif stripped_line.startswith("[") and in_setuptools_scm_section:
                    # We've reached a new section, so stop searching
                    break

                # If we're in the right section, look for the fallback_version key
                if in_setuptools_scm_section and stripped_line.startswith("fallback_version"):
                    # Extract the value after the '=' sign and strip any surrounding quotes or whitespace
                    __version__ = stripped_line.split('=', 1)[1].strip().strip('"').strip("'")
                    break
        # Account for the possibility that we failed to extract the fallback_version field from pyproject.toml
        if not __version__:
            msg = "fallback_version not found in file %s" % pyproject_toml
            msg += " when trying the get the EESSI test suite version. This should never happen."
            msg += " Please report an issue on Github, including information on how you installed"
            msg += " the EESSI test suite. Defaulting to version 0.0.0"
            print(msg)
            __version__ = "0.0.0"
