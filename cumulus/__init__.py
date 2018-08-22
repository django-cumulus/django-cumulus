"""
An interface to the python-swiftclient api through Django.
"""


from ._version import get_versions
__version__ = get_versions()['version']
del get_versions
