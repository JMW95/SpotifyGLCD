import time
import threading
import requests
from PIL import Image
from StringIO import StringIO

#FIX FOR SSLError after py2exe conversion
import os
os.environ["REQUESTS_CA_BUNDLE"] = os.path.join(os.getcwd(), "cacert.pem")

PAUSED = 0
PLAYING = 1

class Poller(threading.Thread):
    def __init__(self, spotify_local, spotify_web):
        threading.Thread.__init__(self)

        self.spotify_local = spotify_local
        self.spotify_web = spotify_web

        self.track = None
        self.artist = None
        self.album = None
        self.state = None
        self.offset = 0
        self.pausedat = 0
        self.tracklen = 0
        self.albumart = None

        self.running = True

    def run(self):
        while self.running:
            if self.spotify_local is None or not self.spotify_local.connected:
                time.sleep(1)
                continue

            try:
                j = self.spotify_local.get_status(return_after=1)
            except: # if this fails, try again after a short delay
                print "Poll failed..."
                time.sleep(2)
                continue

            try:
                meta = j['track']
                tracktype = meta['track_type']

                if 'track_resource' in meta: newtrack = meta['track_resource']
                if 'album_resource' in meta: newalbum = meta['album_resource']
                if 'artist_resource' in meta: newartist = meta['artist_resource']

                self.state = PLAYING if j['playing'] else PAUSED

                self.tracklen = meta['length']
                self.offset = time.time() - j['playing_position']

                if self.state == PAUSED:
                    self.pausedat = j['playing_position']
            except KeyError: # Something was missing from the poll data
                continue

            if tracktype not in ["normal", "explicit"]:
                # It's an advert
                self.album = None
                self.artist = None
                self.track = {'name': "Advert", 'uri': ""}
                self.albumart = None
            else:
                # It's not an advert

                fetch_art = False
                if self.album is None or newalbum['uri'] != self.album['uri']: # fetch new album art
                    fetch_art = True

                fetch_info = False
                if self.track is None or newtrack['uri'] != self.track['uri']: # fetch artists
                    fetch_info = True

                self.track = newtrack
                self.album = newalbum

                if fetch_info:
                    def get_artist():
                        retries = 0
                        while retries < 3:
                            try:
                                j = self.spotify_web.get_track_info(self.track['uri'])
                                self.artist['name'] = ", ".join([v['name'] for v in j['artists']])
                                break
                            except Exception as e:
                                print e
                                retries += 1
                                continue

                    self.artist = newartist

                    threading.Thread(target=get_artist).start()

                if fetch_art:
                    def get_art():
                        retries = 0
                        while retries < 3:
                            try:
                                j = self.spotify_web.get_track_info(self.track['uri'])
                                im = j['album']['images'][0]

                                response = requests.get(im['url'])
                                self.albumart = Image.open(StringIO(response.content))
                                break
                            except Exception as e:
                                print e
                                retries += 1
                                continue

                    threading.Thread(target=get_art).start()
