import os
import time
from selenium import webdriver

REPEAT_OFF = 0
REPEAT = 1
REPEAT_ONCE = 2

class SpotifyDriver():
    def __init__(self):
        appdata = os.getenv('APPDATA')
        self.spotify_exe = os.path.join(appdata, "Spotify" + os.sep + "Spotify.exe")
        self.spotify = None

    def open_spotify(self):
        options = webdriver.chrome.options.Options()
        options.binary_location = self.spotify_exe

        retries = 0
        while retries < 3:
            try:
                self.spotify = webdriver.Chrome(chrome_options=options)
                break
            except WindowsError:
                retries += 1
                time.sleep(1)
                continue

        time.sleep(2)

    def close_spotify(self):
        if self.spotify:
            self.spotify.close()
        else:
            os.system("taskkill /f /im Spotify.exe")

    def click(self, id):
        if self.spotify is None:
            return
        self.spotify.execute_script("document.getElementById('" + id + "').click()")

    def is_shuffle_enabled(self):
        if self.spotify is None:
            return False
        return "active" in self.spotify.find_element_by_id("player-button-shuffle").get_attribute("class")

    def star(self):
        self.click("nowplaying-add-icon")

    def is_starred(self):
        if self.spotify is None:
            return False
        return "added" in self.spotify.find_element_by_id("nowplaying-add-icon").get_attribute("class")

    def shuffle(self, shuffle_enable=None):
        if self.spotify is None:
            return
        if shuffle_enable is None:
            self.click("player-button-shuffle")
        elif (self.is_shuffle_enabled() != shuffle_enable):
            self.click("player-button-shuffle")
            time.sleep(0.1)

    def repeat(self, repeat_mode=None):
        if self.spotify is None:
            return
        if repeat_mode is None:
            self.click("player-button-repeat")
        else:
            if not repeat_mode in [REPEAT_OFF, REPEAT, REPEAT_ONCE]:
                raise ValueError("Invalid repeat mode: %d" % repeat_mode)

            while self.get_repeat_mode() != repeat_mode:
                self.click("player-button-repeat")
                time.sleep(0.1)

    def next(self):
        self.click("player-button-next")

    def prev(self):
        self.click("player-button-previous")

    def playpause(self):
        self.click("player-button-play")

    def get_repeat_mode(self):
        cl = self.spotify.find_element_by_id("player-button-repeat").get_attribute("class")
        if "spoticon-repeatonce" in cl:
            return REPEAT_ONCE
        elif "active" in cl:
            return REPEAT
        else:
            return REPEAT_OFF
