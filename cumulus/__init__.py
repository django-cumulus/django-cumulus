"""
An interface to the python-swiftclient api through Django.
"""
__version_info__ = {
    'major': 1,
    'minor': 0,
    'micro': 11,
    'releaselevel': 'final',
    'serial': 1
}


def get_version():
    vers = ["{major}.{minor}".format(**__version_info__)]

    if __version_info__["micro"]:
        vers.append(".{micro}".format(**__version_info__))
    if __version_info__["releaselevel"] != "final":
        vers.append("{releaselevel}{serial}".format(**__version_info__))
    return "".join(vers)

__version__ = get_version()
