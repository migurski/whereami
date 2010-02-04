"""
Sanity-check locations in lat, lon or mercator forms.

Most output is on stderr, the URLs are on stdout so it's possible to use like this:
    % open `python whereami.py -13628177 4546770 -13627494 4546034`

Examples follow.

% python whereami.py 15/5241/12666
southwest:   37.76201938 -122.42064938
northeast:   37.77070423 -122.40966305
upper-left:  -13627804.35 4547084.46
lower-right: -13626581.36 4545861.47
http://pafciu17.dev.openstreetmap.org/?...

% python whereami.py 37.764897 -122.419453
mercator: -13627671.17 4546266.67
tile:     8/40/98
http://pafciu17.dev.openstreetmap.org/?...

% python whereami.py 37.764897 -122.419453 14
mercator: -13627671.17 4546266.67
tile:     14/2620/6333
http://pafciu17.dev.openstreetmap.org/?...

% python whereami.py -13627671 4546266
lat, lon: 37.76489221 -122.41945146
tile: 8/40/98
http://pafciu17.dev.openstreetmap.org/?...

% python whereami.py -13627671 4546266 12
lat, lon: 37.76489221 -122.41945146
tile: 12/655/1583
http://pafciu17.dev.openstreetmap.org/?...

% python whereami.py 37.763251 -122.424002 37.768476 -122.417865
southwest:   37.76325100 -122.42400200
northeast:   37.76847600 -122.41786500
upper-left:  -13628177.56 4546770.67
lower-right: -13627494.40 4546034.89
http://pafciu17.dev.openstreetmap.org/?...

% python whereami.py -13628177 4546770 -13627494 4546034
southwest:   37.76324465 -122.42399694
northeast:   37.76847126 -122.41786144
upper-left:  -13628177.00 4546770.00
lower-right: -13627494.00 4546034.00
http://pafciu17.dev.openstreetmap.org/?...

"""

import re
import sys
import ModestMaps
import subprocess
import commands
from urllib import urlencode

url = 'http://pafciu17.dev.openstreetmap.org/'
gym = '+proj=merc +lon_0=0 +k=1 +x_0=0 +y_0=0 +a=6378137 +b=6378137 +towgs84=0,0,0,0,0,0,0 +units=m +no_defs'

def project(lat, lon):
    """ Project latitude, longitude to mercator x, y.
    
        Shells out to proj so it will work if you lack pyproj.
    """
    status, proj = commands.getstatusoutput('which proj')
    assert status == 0, 'Expected to get a clean exit from `which proj`'

    pipe = subprocess.Popen([proj] + gym.split(), stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    pipe.stdin.write('%(lon).8f %(lat).8f\n' % locals())
    pipe.stdin.close()
    
    x, y = map(float, pipe.stdout.read().strip().split())
    
    return x, y

def unproject(x, y):
    """ Unproject mercator x, y to latitude, longitude.
    
        Shells out to proj so it will work if you lack pyproj.
    """
    status, proj = commands.getstatusoutput('which proj')
    assert status == 0, 'Expected to get a clean exit from `which proj`'

    pipe = subprocess.Popen([proj, '-I', '-f', '%.8f'] + gym.split(), stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    pipe.stdin.write('%(x).8f %(y).8f\n' % locals())
    pipe.stdin.close()
    
    lon, lat = map(float, pipe.stdout.read().strip().split())
    
    return lat, lon

def is_latlon(this, that):
    """ True is the arguments seem like a latitude, longitude
    """
    return -85 <= this and this <= 85 and -180 <= that and that <= 180

def point_map_url(lat, lon, zoom):
    """
    """
    q = {'module': 'map', 'width': 512, 'height': 384, 'zoom': zoom}
    q['lat'], q['lon'] = lat, lon
    q['points'] = '%.6f,%.6f' % (lon, lat)

    return url + '?' + urlencode(q)

def box_map_url(minlat, minlon, maxlat, maxlon):
    """
    """
    buflat = (maxlat - minlat) / 8
    buflon = (maxlon - minlon) / 8

    q = {'module': 'map', 'width': 512, 'height': 384}
    q['bbox'] = '%.6f,%.6f,%.6f,%.6f' % (minlon - buflon, maxlat + buflat, maxlon + buflon, minlat - buflat)
    q['polygons'] = '%.6f,%.6f,%.6f,%.6f,%.6f,%.6f,%.6f,%.6f,color:0:0:0' % (minlon, minlat, minlon, maxlat, maxlon, maxlat, maxlon, minlat)
    
    return url + '?' + urlencode(q)

def latlon_point(lat, lon, zoom):
    """
    """
    provider = ModestMaps.OpenStreetMap.Provider()
    location = ModestMaps.Geo.Location(lat, lon)
    coord = provider.locationCoordinate(location).zoomTo(zoom)

    print >> sys.stderr, 'mercator: %.2f %.2f' % project(lat, lon)
    print >> sys.stderr, 'tile:     %(zoom)d/%(column)d/%(row)d' % coord.__dict__
    print >> sys.stdout, point_map_url(lat, lon, zoom)

def merc_point(x, y, zoom):
    """
    """
    lat, lon = unproject(x, y)

    provider = ModestMaps.OpenStreetMap.Provider()
    location = ModestMaps.Geo.Location(lat, lon)
    coord = provider.locationCoordinate(location).zoomTo(zoom)

    print >> sys.stderr, 'lat, lon: %.8f %.8f' % (lat, lon)
    print >> sys.stderr, 'tile: %(zoom)d/%(column)d/%(row)d' % coord.__dict__
    print >> sys.stdout, point_map_url(lat, lon, zoom)

def latlon_box(minlat, minlon, maxlat, maxlon):
    """
    """
    print >> sys.stderr, 'southwest:   %.8f %.8f' % (minlat, minlon)
    print >> sys.stderr, 'northeast:   %.8f %.8f' % (maxlat, maxlon)
    print >> sys.stderr, 'upper-left:  %.2f %.2f' % project(maxlat, minlon)
    print >> sys.stderr, 'lower-right: %.2f %.2f' % project(minlat, maxlon)
    print >> sys.stdout, box_map_url(minlat, minlon, maxlat, maxlon)

def merc_box(xmin, ymin, xmax, ymax):
    """
    """
    minlat, minlon = unproject(xmin, ymin)
    maxlat, maxlon = unproject(xmax, ymax)
    
    print >> sys.stderr, 'southwest:   %.8f %.8f' % (minlat, minlon)
    print >> sys.stderr, 'northeast:   %.8f %.8f' % (maxlat, maxlon)
    print >> sys.stderr, 'upper-left:  %.2f %.2f' % (xmin, ymax)
    print >> sys.stderr, 'lower-right: %.2f %.2f' % (xmax, ymin)
    print >> sys.stdout, box_map_url(minlat, minlon, maxlat, maxlon)

def tile_box(row, column, zoom):
    """
    """
    provider = ModestMaps.OpenStreetMap.Provider()
    coord = ModestMaps.Core.Coordinate(row, column, zoom)
    southwest = provider.coordinateLocation(coord.down())
    northeast = provider.coordinateLocation(coord.right())
    
    latlon_box(southwest.lat, southwest.lon, northeast.lat, northeast.lon)

if __name__ == '__main__':

    args = sys.argv[1:]

    if len(args) is 1 and re.match(r'^\d+/\d+/\d+$', args[0]):
        zoom, column, row = map(int, args[0].split('/'))
        tile_box(row, column, zoom)
    
    elif len(args) in (2, 3):
        try:
            args = map(float, args)
        except ValueError:
            print >> sys.stderr, 'Two or three values are expected to be numeric: a point and optional zoom.', args
            sys.exit(1)

        zoom = len(args) == 3 and args[2] or 8

        if is_latlon(*args[0:2]):
            lat, lon = args[0:2]
            latlon_point(lat, lon, zoom)

        else:
            x, y = args[0:2]
            merc_point(x, y, zoom)

    elif len(args) is 4:
        try:
            args = map(float, args)
        except ValueError:
            print >> sys.stderr, 'Four values are expected to be numeric: two points.', args
            sys.exit(1)

        if is_latlon(*args[0:2]) and is_latlon(*args[2:4]):
            minlat, maxlat = min(args[0], args[2]), max(args[0], args[2])
            minlon, maxlon = min(args[1], args[3]), max(args[1], args[3])
            latlon_box(minlat, minlon, maxlat, maxlon)

        elif is_latlon(*args[0:2]) or is_latlon(*args[2:4]):
            raise Exception("Looks like you're mixing mercator and lat, lon?")

        else:
            xmin, xmax = min(args[0], args[2]), max(args[0], args[2])
            ymin, ymax = min(args[1], args[3]), max(args[1], args[3])
            merc_box(xmin, ymin, xmax, ymax)

    else:
        print >> sys.stderr, "Sorry I'm not sure what to do with this input.", args