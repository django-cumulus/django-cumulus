"""
An interface to Rackspace Cloud Files through Django.
"""
__version_info__ = {
    'major': 1,
    'minor': 0,
    'micro': 5,
    'releaselevel': 'final',
    'serial': 1
}

def get_version():
    vers = ["%(major)i.%(minor)i" % __version_info__, ]

    if __version_info__['micro']:
        vers.append(".%(micro)i" % __version_info__)
    if __version_info__['releaselevel'] != 'final':
        vers.append('%(releaselevel)s%(serial)i' % __version_info__)
    return ''.join(vers)

__version__ = get_version()
