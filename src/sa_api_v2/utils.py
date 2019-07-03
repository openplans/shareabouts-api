import re
import time
from django.conf import settings
if settings.USE_GEODB:
    from django.contrib.gis.geos import GEOSGeometry, Point
    from django.contrib.gis.measure import D
from functools import wraps

try:
    # Python 2
    from urlparse import urlparse, urljoin
except:
    # Python 3
    from urllib.parse import urlparse, urljoin

def isiterable(obj):
    try:
        iter(obj)
    except TypeError:
        return False
    else:
        return True

def to_distance(string):
    try:
        number = float(string)
        units = 'm'
    except ValueError:
        match = re.match(r'([+-]?\d*\.?\d+)\s*([A-Za-z_]+)', string)
        if not match:
            raise ValueError('%r is not a valid distance.')
        number = float(match.group(1))
        units = match.group(2)

    return D(**{units: number})

def to_geom(string):
    """
    Given a string, convert it to a geometry.
    """
    try:
        geom = GEOSGeometry(string)
    except ValueError:
        try:
            lat, lng = [float(coord.strip()) for coord in string.split(',')]
        except ValueError:
            raise ValueError(
                ('Argument must be a comma-separated pair of numbers or a '
                 'string that the GEOSGeometry constructor can handle: %r')
                % string
            )
        else:
            geom = Point(lng, lat)

    # Assume WGS84 (lat/lng) if no SRID is attached yet.
    if not geom.srid:
        geom.set_srid(4326)

    return geom

def memo(f):
    """
    A memoization decorator. Borrowed and modified from
    http://code.activestate.com/recipes/576563-cached-property/

    You can create a memoized property like:

        @property
        @memo
        def attr(self):
            ...

    """
    @wraps(f)
    def get(self, *args, **kwargs):
        key = (f.__name__, args, tuple(kwargs.items()))
        try:
            return self._method_memos[key]
        except AttributeError:
            self._method_memos = {}
            x = self._method_memos[key] = f(self, *args, **kwargs)
            return x
        except KeyError:
            x = self._method_memos[key] = f(self, *args, **kwargs)
            return x

    return get


def base62_time():
    """
    Convert the current epoch time in milliseconds to a base-64 encoded string.
    """
    ms = int(time.time() * 1000)
    return to_base(ms, 62)


def to_base(num, base):
    """
    Convert an integer to a string in the given base, up to 62.
    """
    alphabet = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"

    digits = []
    while num > 0:
        num, remainder = divmod(num, base)
        digits.insert(0, alphabet[remainder])

    return ''.join(digits)


def build_relative_url(original_url, relative_path):
    """
    Given a source URL, create a full URL for the relative path. For example:

    ('http://ex.co/pictures/silly/abc.png', '/home') --> 'http://ex.co/home'
    ('http://ex.co/p/index.html', 'about.html') --> 'http://ex.co/p/about.html'
    ('http://ex.co/', 'https://google.com/') --> 'https://google.com/'
    """
    # If we actually have a full URL, just return it.
    if (re.match('^[A-Za-z][A-Za-z0-9+-.]*://', relative_path)):
        return relative_path

    parsed_url = urlparse(original_url)

    if relative_path.startswith('/'):
        path_prefix = ''
    elif parsed_url.path.endswith('/') or relative_path == '':
        path_prefix = parsed_url.path
    else:
        path_prefix = parsed_url.path.rsplit('/', 1)[0] + '/'

    if path_prefix:
        full_path = path_prefix + relative_path
    else:
        full_path = relative_path

    return urljoin(parsed_url.scheme + '://' + parsed_url.netloc, full_path)
