# WARNING: this file is imported in setup.py
# To make sure this works, we should avoid using imports other than from the Python standard library

try:
    # If this is an installed package, setuptools_scm will have written the _version.py file in the current directory
    from ._version import __version__
except ImportError:
    try:
        # Setuptools_scm 4.1.2 (compatible with setuptools 39.2.0) write version instead of __version__
        # This can be removed once we no longer care about python 3.6 with setuptools 39.2.0
        from ._version import version
        __version__ = version
    except ImportError:
        # Fallback for when the package is not installed, but git cloned. Note that this requires setuptools_scm to be
        # available as a runtime dependency
        # The advantage here is that it will generate development versions if not on a tagged release version
        try:
            from setuptools_scm import get_version
            # Using a relative path for relative_to doesn't work, because it will be relative to the current working
            # directory (which could be anywhere)
            # __file__ is the location of this init file (a full path), and this gives us a predictable path to the root
            # (namely: two levels up). Note that if we ever move this __init__ file relative to the root of the git
            # tree, we'll need to adjust this
            __version__ = get_version(root='../..', relative_to=__file__)
        except (ImportError, LookupError):
            # If running from a tarball (e.g. release tarball) downloaded from github, we will not have the .git
            # folder available. Thus, setuptools_scm cannot determine the version in any way. Thus, use the
            # fallback_version from the pyproject.toml file (which doesn't exist when this is installed as a package,
            # but SHOULD exist when this is run from a downloaded tarball from git)

            # Pyproject.toml should be two levels up from this file
            import os.path
            pyproject_toml = "%s/../../pyproject.toml" % os.path.dirname(__file__)

            # Variables to track if we're in the right section and to store the fallback_version
            in_setuptools_scm_section = False
            fallback_version = None

            file = None
            try:
                file = open(pyproject_toml, 'r')
                # Open the file and parse it manually
                fallback_version = None
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
                            fallback_version = stripped_line.split('=', 1)[1].strip().strip('"').strip("'")
                            break
                # Account for the possibility that we failed to extract the fallback_version field from pyproject.toml
                if fallback_version:
                    __version__ = fallback_version
                else:
                    msg = "fallback_version not found in file %s" % pyproject_toml
                    msg += " when trying the get the EESSI test suite version. This should never happen."
                    msg += " Please report an issue on Github, including information on how you installed"
                    msg += " the EESSI test suite."
                    print(msg)
            except FileNotFoundError:
                msg = "File %s not found when trying to extract the EESSI test suite version from" % pyproject_toml
                msg += " pyproject.toml. This should never happen. Please report an issue on GitHub,"
                msg += " including information on how you installed the EESSI test suite."
                print(msg)
            except Exception as e:
                print("When trying to open file %s, an exception was raised: %s." % (pyproject_toml, e))

# One of the above three methods to get __version__ defined SHOULD work in any situation.
# It's considered a bug you reach this point without having a __version__ set
if not __version__:
    msg = "__version__ should have been defined by now, but it is not."
    msg += " This is considered a bug, please report it in an issue on Github for the"
    msg += " EESSI test suite."
    raise ValueError(msg)
