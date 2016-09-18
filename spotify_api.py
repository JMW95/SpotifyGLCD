# The class SpotifyLocal is a derived version of the client found here: https://github.com/cgbystrom/spotify-local-http-api

import ssl
from string import ascii_lowercase
from random import choice
import urllib
import urllib2
import requests
import json
import webbrowser
import BaseHTTPServer
import SocketServer
import threading
import urlparse
import base64

#FIX FOR SSLError after py2exe conversion
import os
os.environ["REQUESTS_CA_BUNDLE"] = os.path.join(os.getcwd(), "cacert.pem")

# FILL THESE OUT WITH SPOTIFY APP KEYS
# The app needs to have 'http://localhost:48125/callback' as a callback URL
CLIENT_ID = "***"
CLIENT_SECRET = "***"

class SpotifyLocal():
    # Default port that Spotify Web Helper binds to.
    DEFAULT_RETURN_ON = ['login', 'logout', 'play', 'pause', 'error', 'ap']
    ORIGIN_HEADER = {'Origin': 'https://open.spotify.com'}

    def __init__(self, port=None):
        self.port = port or 4730
        self.loaded = False
        self.connected = False

    def connect(self):
        try:
            self.find_port()
            self.oauth_token = self.get_oauth_token()
            self.csrf_token = self.get_csrf_token()
        except Exception as e:
            if e.message == "Spotify not running!":
                pass # Failed to connect to spotify
            else:
                raise
        else:
            self.connected = True
        self.loaded = True

    # I had some troubles with the version of Spotify's SSL cert and Python 2.7 on Mac.
    # Did this monkey dirty patch to fix it. Your milage may vary.
    def new_wrap_socket(*args, **kwargs):
        kwargs['ssl_version'] = ssl.PROTOCOL_SSLv3
        return orig_wrap_socket(*args, **kwargs)
    orig_wrap_socket, ssl.wrap_socket = ssl.wrap_socket, new_wrap_socket

    def get_json(self, url, params={}, headers={}):
        if params:
            url += "?" + urllib.urlencode(params)
        request = urllib2.Request(url, headers=headers)
        return json.loads(urllib2.urlopen(request).read())

    def generate_local_hostname(self):
        """Generate a random hostname under the .spotilocal.com domain"""
        subdomain = ''.join(choice(ascii_lowercase) for x in range(10))
        return subdomain + '.spotilocal.com'

    def get_url(self, url):
        return "https://%s:%d%s" % (self.generate_local_hostname(), self.port, url)

    def get_version(self):
        return self.get_json(self.get_url('/service/version.json'), params={'service': 'remote'}, headers=self.ORIGIN_HEADER)

    def find_port(self):
        self.port = 4370
        while self.port < 4381:
            try:
                self.get_version()
                break
            except urllib2.URLError:
                self.port += 1
        else:
            raise Exception("Spotify not running!")

        print "Using port %d" % (self.port,)

    def get_oauth_token(self):
        return self.get_json('http://open.spotify.com/token')['t']

    def get_csrf_token(self):
        # Requires Origin header to be set to generate the CSRF token.
        return self.get_json(self.get_url('/simplecsrf/token.json'), headers=self.ORIGIN_HEADER)['token']

    def get_status(self, return_after=59, return_on=None):
        if not return_on:
            return_on = self.DEFAULT_RETURN_ON
        params = {
            'oauth': self.oauth_token,
            'csrf': self.csrf_token,
            'returnafter': return_after,
            'returnon': ','.join(return_on)
        }
        return self.get_json(self.get_url('/remote/status.json'), params=params, headers=self.ORIGIN_HEADER)

    def pause(self, pause=True):
        params = {
            'oauth': self.oauth_token,
            'csrf': self.csrf_token,
            'pause': 'true' if pause else 'false'
        }
        self.get_json(self.get_url('/remote/pause.json'), params=params, headers=self.ORIGIN_HEADER)

    def unpause(self):
        self.pause(pause=False)

    def play(self, spotify_uri):
        params = {
            'oauth': self.oauth_token,
            'csrf': self.csrf_token,
            'uri': spotify_uri,
            'context': spotify_uri,
        }
        self.get_json(self.get_url('/remote/play.json'), params=params, headers=self.ORIGIN_HEADER)


class SpotifyWeb():
    #authed = False
    #oauth_token = ""
    httpd = None

    class AuthHandler(BaseHTTPServer.BaseHTTPRequestHandler):
        def do_GET(self):
            pars = urlparse.parse_qs(urlparse.urlparse(self.path).query)
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write("Successfully authed!")

            if 'code' in pars:
                SpotifyWeb._set_oauth_token(pars['code'])
            elif 'error' in pars:
                print pars['error']

    class HTTPDThread(threading.Thread):
        def __init__(self, port):
            threading.Thread.__init__(self)
            self.port = port

        def run(self):
            self.httpd = SocketServer.TCPServer(("", self.port), SpotifyWeb.AuthHandler)
            self.httpd.serve_forever()

        def stop(self):
            self.httpd.shutdown()

    def __init__(self):
        #TODO this auth isn't needed yet, but the handling is in place
        #self.get_oauth_token()
        pass

    @classmethod
    def shutdown(cls):
        if SpotifyWeb.httpd is not None:
            SpotifyWeb.httpd.stop()

    @classmethod
    def _set_oauth_token(cls, token, refresh=False):
        data = {
            'grant_type': "authorization_code",
            'code': token,
            'redirect_uri': "http://localhost:48125/callback",
        }
        headers = {
            'Authorization': 'Basic ' + base64.b64encode(CLIENT_ID + ":" + CLIENT_SECRET),
        }
        if refresh:
            data = {
                'grant_type': 'refresh_token',
                'refresh_token': token,
            }

        print "Setting OAUTH token"

        r = requests.post("https://accounts.spotify.com/api/token", data=data, headers=headers)

        if r.status_code == 200:
            j = json.loads(r.text)
            SpotifyWeb.oauth_token = j['access_token']
            SpotifyWeb.authed = True

            t = threading.Thread(target=SpotifyWeb.shutdown)
            t.start()

            if 'refresh_token' in j:
                # save the refresh token so we can quickly auth next time
                with open("key.dat", "w") as f:
                    f.write(j['refresh_token'])
                    f.write("\n")
        else:
            print r.status_code
            print r.text

    def get_oauth_token(self):
        try:
            with open("key.dat") as f:
                refresh_token = f.readline().strip()
        except IOError:
            pass
        else:
            print "Using existing key"

            SpotifyWeb._set_oauth_token(refresh_token, refresh=True)
            return

        SpotifyWeb.httpd = self.HTTPDThread(48125) # randomly picked port
        SpotifyWeb.httpd.start()

        data = {
            'client_id': CLIENT_ID,
            'response_type': "code",
            'redirect_uri': "http://localhost:48125/callback",
            'scope': 'user-library-modify user-library-read',
        }
        webbrowser.open("https://accounts.spotify.com/authorize/?" + urllib.urlencode(data))

    def star(self, uri):
        while ":" in uri:
            uri = uri[uri.find(":")+1:]
        url = "https://api.spotify.com/v1/me/tracks" + "?" + urllib.urlencode({'ids': uri})
        return requests.put(url, headers={'Authorization': "Bearer " + SpotifyWeb.oauth_token})

    def unstar(self, uri):
        while ":" in uri:
            uri = uri[uri.find(":")+1:]
        url = "https://api.spotify.com/v1/me/tracks" + "?" + urllib.urlencode({'ids': uri})
        return requests.delete(url, headers={'Authorization': "Bearer " + SpotifyWeb.oauth_token})

    def is_starred(self, uri):
        while ":" in uri:
            uri = uri[uri.find(":")+1:]
        url = "https://api.spotify.com/v1/me/tracks/contains" + "?" + urllib.urlencode({'ids': uri})
        r = requests.get(url, headers={'Authorization': "Bearer " + SpotifyWeb.oauth_token})
        if r.status_code == 200:
            j = json.loads(r.text)
            return j[0]

    def get_track_info(self, uri):
        while ":" in uri:
            uri = uri[uri.find(":")+1:]
        url = "https://api.spotify.com/v1/tracks/" + uri
        #r = requests.get(url, headers={'Authorization': "Bearer " + SpotifyWeb.oauth_token})
        r = requests.get(url)
        if r.status_code == 200:
            j = json.loads(r.text)
            return j
