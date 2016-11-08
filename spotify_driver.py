import os
import time
import subprocess
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

    def is_spotify_running(self):
        p = subprocess.Popen(["tasklist", "/fi", "imagename eq Spotify.exe"], shell=True, stdout=subprocess.PIPE)
        out = p.communicate()[0].strip().split('\r\n')
        # if TASKLIST returns single line without processname: it's not running
        if len(out) > 1 and "Spotify.exe" in out[-1]:
            return True
        else:
            return False

    def quit(self):
        if self.spotify is not None:
            self.spotify.quit()

    def click(self, id=None, class_name=None):
        if self.spotify is None:
            return
        if class_name:
            self.spotify.execute_script("document.getElementsByClassName('" + class_name + "')[0].click()")
        else:
            self.spotify.execute_script("document.getElementById('" + id + "').click()")

    def is_shuffle_enabled(self):
        if self.spotify is None:
            return False
        el = self.spotify.find_element_by_id("player-button-shuffle")
        if el is not None:
            cl = el.get_attribute("class")
            if cl is not None:
                return "active" in cl
        return False

    def star(self):
        self.click(class_name="nowplaying-add-button")

    def is_starred(self):
        if self.spotify is None:
            return False
        el = self.spotify.find_elements_by_class_name("nowplaying-add-button")[0]
        if el is not None:
            cl = el.get_attribute("class")
            if cl is not None:
                return "added" in cl
        return False

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
        el = self.spotify.find_element_by_id("player-button-repeat")
        if el is not None:
            cl = el.get_attribute("class")
            if cl is not None:
                if "spoticon-repeatonce" in cl:
                    return REPEAT_ONCE
                elif "active" in cl:
                    return REPEAT
        return REPEAT_OFF
