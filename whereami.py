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

def latlon_point(lat, lon, zoom):
    """
    """
    provider = ModestMaps.OpenStreetMap.Provider()
    location = ModestMaps.Geo.Location(lat, lon)
    coord = provider.locationCoordinate(location).zoomTo(zoom)

    print >> sys.stderr, 'mercator: %.2f %.2f' % project(lat, lon)
    print >> sys.stderr, 'tile: %(zoom)d/%(column)d/%(row)d' % coord.__dict__
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

if __name__ == '__main__':
    args = map(float, sys.argv[1:])
    
    if len(args) in (2, 3):
        zoom = len(args) == 3 and args[2] or 8

        if is_latlon(*args[0:2]):
            lat, lon = args[0:2]
            latlon_point(lat, lon, zoom)
        else:
            x, y = args[0:2]
            merc_point(x, y, zoom)
