# On older python's this is needed for correct installation of a namespace package
# But on newer pythons, there is no pkg_resources anymore
# We pragmatically wrap it in a try-block. It can be removed entirely after we stop supporting
# python 3.6, since then we can simply require a new enough setuptools that this declare_namespace is
# no longer required
try:
    __import__("pkg_resources").declare_namespace(__name__)
except:
    pass
