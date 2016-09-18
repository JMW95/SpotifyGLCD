import sys
import time
import threading
import atexit
from selenium.common.exceptions import WebDriverException
from PIL import Image, ImageFont, ImageDraw
from spotify_api import SpotifyLocal, SpotifyWeb
from spotify_driver import *
from menubutton import MenuButton
from spotify_poller import *
import glcd_api as GLCD

font = ImageFont.truetype("C:\\Windows\\Fonts\\Arial.ttf", 16)

ALBUMART_WIDTH = 140
ALBUMART_HEIGHT = 140
ALBUMART_BOTTOM = 240 - 28
ALBUMART_TOP = ALBUMART_BOTTOM-ALBUMART_HEIGHT
ALBUMART_LEFT = 10

PROGBAR_WIDTH = 300
PROGBAR_HEIGHT = 8
PROGBAR_LEFT = (320 - PROGBAR_WIDTH) / 2
PROGBAR_RIGHT = 320 - PROGBAR_LEFT
PROGBAR_BOTTOM = 240 - 10
PROGBAR_TOP = PROGBAR_BOTTOM - PROGBAR_HEIGHT

BACKCOLOR = (40,40,40)
TEXTCOLOR = (255,255,255)
PROGBARFG = (30,214,96)
CURSORCOLOR = (255,200,40)

spotify_local = None
driver = SpotifyDriver()
buttons = None
poller = None

def formattime(t):
    t = int(t)
    secs = t % 60
    mins = t / 60
    hours = t / 3600

    if hours > 0:
        return "{}:{:02}:{:02}".format(hours, mins, secs)
    else:
        return "{}:{:02}".format(mins, secs)


im_saved = Image.open("images/saved.png")
im_save = Image.open("images/save.png")
im_repeat_off = Image.open("images/repeat_off.png")
im_repeat_on = Image.open("images/repeat_on.png")
im_repeat_once = Image.open("images/repeat_once.png")
im_shuffle_off = Image.open("images/shuffle_off.png")
im_shuffle_on = Image.open("images/shuffle_on.png")
im_pause = Image.open("images/pause.png")
im_play = Image.open("images/play.png")
im_prev = Image.open("images/prev.png")
im_next = Image.open("images/next.png")

background = Image.open("images/back.png")

def buttonclick(btn):
    if btn == btn_save:
        driver.star()
    elif btn == btn_shuffle:
        driver.shuffle()
    elif btn == btn_repeat:
        driver.repeat()
    elif btn == btn_prev:
        driver.prev()
    elif btn == btn_playpause:
        driver.playpause()
    elif btn == btn_next:
        driver.next()

menupos = [1,1]
btn_save = MenuButton((0,0), (190,106), buttonclick, im_save)
btn_shuffle = MenuButton((1,0), (222,106), buttonclick, im_shuffle_off)
btn_repeat = MenuButton((2,0), (254,106), buttonclick, im_repeat_off)
btn_prev = MenuButton((0,1), (173,142), buttonclick, im_prev)
btn_playpause = MenuButton((1,1), (206,130), buttonclick, im_play)
btn_next = MenuButton((2,1), (265,142), buttonclick, im_next)
menubuttons = [btn_save, btn_shuffle, btn_repeat, btn_prev, btn_playpause, btn_next]

commandlock = threading.Lock()
pendingcommands = []

def render_mono():
    # TODO: implement me
    if poller.track is not None:
        GLCD.LogiLcdMonoSetText(0, poller.track['name'])
    if poller.album is not None:
        GLCD.LogiLcdMonoSetText(1, poller.album['name'])


def render_color():
    if spotify_local is not None:
        if not spotify_local.loaded:
            image = Image.new("RGB", (320,240), BACKCOLOR)
            draw = ImageDraw.Draw(image)
            draw.text((5,5), "Waiting for Spotify...", TEXTCOLOR, font=font)
        else:
            if not spotify_local.connected:
                image = Image.new("RGB", (320,240), BACKCOLOR)
                draw = ImageDraw.Draw(image)
                draw.text((5,5), "Spotify not running.", TEXTCOLOR, font=font)
            else:
                image = background.copy()
                draw = ImageDraw.Draw(image)

                if poller.albumart is not None:
                    image.paste(poller.albumart.resize((ALBUMART_WIDTH,ALBUMART_HEIGHT), Image.ANTIALIAS), (ALBUMART_LEFT,ALBUMART_TOP))

                # Track / Artist / Album
                if poller.track is not None:
                    draw.text((26,2), poller.track['name'], TEXTCOLOR, font=font)
                if poller.artist is not None:
                    draw.text((26,22), poller.artist['name'], TEXTCOLOR, font=font)
                if poller.album is not None:
                    draw.text((26,42), poller.album['name'], TEXTCOLOR, font=font)

                # Play/pause and prev/next buttons
                if poller.state == PLAYING:
                    btn_playpause.image = im_pause
                    currtime = time.time() - poller.offset
                else:
                    btn_playpause.image = im_play
                    currtime = poller.pausedat

                image.paste(im_prev, (173,142))
                image.paste(im_next, (265,142))

                # Track time
                timestr = formattime(currtime) + " / " + formattime(poller.tracklen)
                w, h = font.getsize(timestr)
                draw.text((ALBUMART_WIDTH + 10 + (320-20-ALBUMART_WIDTH-w)/2 ,240-28-h), timestr, TEXTCOLOR, font=font)
                if poller.tracklen > 0:
                    perc = currtime / poller.tracklen
                    draw.rectangle([(PROGBAR_LEFT, PROGBAR_TOP),(PROGBAR_LEFT + (PROGBAR_WIDTH * perc), PROGBAR_BOTTOM)], fill=PROGBARFG, outline=PROGBARFG)

                # Starred status
                btn_save.image = im_saved if driver.is_starred() else im_save

                # Shuffle / Repeat status
                btn_shuffle.image = im_shuffle_on if driver.is_shuffle_enabled() else im_shuffle_off
                repeat_ims = [im_repeat_off, im_repeat_on, im_repeat_once]
                btn_repeat.image = repeat_ims[driver.get_repeat_mode()]

                # Draw buttons / menu cursor
                for button in menubuttons:
                    button.render(image)
                    if button.logicalpos[0] == menupos[0] and button.logicalpos[1] == menupos[1]:
                        draw.rectangle((button.pos[0]-2, button.pos[1]-2, button.pos[0]+button.image.size[0]+2, button.pos[1]+button.image.size[1]+2), fill=None, outline=CURSORCOLOR)

                commandlock.acquire()
                for command in pendingcommands:
                    try:
                        command()
                    except Exception as e:
                        print e
                pendingcommands[:] = [] # Clear the list
                commandlock.release()

        # GLCD needs BGRA, so swap it like this
        swapped = Image.frombytes("RGBX", (320,240), image.tobytes(), 'raw', 'BGR')

        # This call takes almost the whole time of this function
        GLCD.ColorBGPIL(swapped)

def buttoncallback(btn):
    if isinstance(buttons, GLCD.ColorButtonManager):
        if btn == GLCD.COLOR_BUTTON_LEFT:
            menupos[0] -= 1
            if menupos[0] < 0:
                menupos[0] = 2
        elif btn == GLCD.COLOR_BUTTON_RIGHT:
            menupos[0] += 1
            if menupos[0] > 2:
                menupos[0] = 0
        elif btn == GLCD.COLOR_BUTTON_DOWN:
            menupos[1] -= 1
            if menupos[1] < 0:
                menupos[1] = 1
        elif btn == GLCD.COLOR_BUTTON_UP:
            menupos[1] += 1
            if menupos[1] > 1:
                menupos[1] = 0
        elif btn == GLCD.COLOR_BUTTON_OK:
            for button in menubuttons:
                if button.logicalpos[0] == menupos[0] and button.logicalpos[1] == menupos[1]:
                    commandlock.acquire()
                    pendingcommands.append(button.click)
                    commandlock.release()

if __name__ == '__main__':
    # Load GLCD api: try 64-bit first, fallback to 32-bit
    try:
        GLCD.initDLL('LogitechLcdx64.dll')
    except WindowsError:
        GLCD.initDLL('LogitechLcdx86.dll')
    GLCD.chkDLL()

    lcd_type = 0

    if GLCD.LogiLcdInit("Spotify GLCD",GLCD.TYPE_COLOR):
        lcd_type = GLCD.TYPE_COLOR
        buttons = GLCD.ColorButtonManager()
    elif GLCD.LogiLcdInit("Spotify GLCD",GLCD.TYPE_MONO):
        lcd_type = GLCD.TYPE_MONO
        buttons = GLCD.MonoButtonManager()
    else:
        print "No Logitech LCD Device found!"
        sys.exit(1)

    buttonthread = GLCD.ButtonPoller(buttons, buttoncallback, 0.05)
    buttonthread.start()

    @atexit.register
    def shutdown():
        GLCD.LogiLcdShutdown()

    spotify_web = SpotifyWeb()

    #if not SpotifyWeb.authed:
    #    print "Waiting for auth..."
    #    while not SpotifyWeb.authed:
    #        time.sleep(1)

    #TODO: show list of playlists and select to play from them

    giveup = False

    def connect_to_spotify():
        global spotify_local, giveup
        spotify_local = SpotifyLocal()
        poller.spotify_local = spotify_local
        while not spotify_local.connected:
            try:
                spotify_local.connect()
                # If Spotify.exe is not running, give up
                if not driver.is_spotify_running():
                    print "NOT RUNNING"
                    giveup = True
                    break
                print "RUNNING"
            except:
                pass
            time.sleep(1)

    def close():
        if poller is not None: poller.running = False
        if buttonthread is not None: buttonthread.running = False
        if spotify_web is not None: spotify_web.shutdown()
        driver.quit()

    try:
        driver.close_spotify()
        driver.open_spotify()

        poller = Poller(spotify_local, spotify_web)
        poller.start()

        threading.Thread(target=connect_to_spotify).start()

        while True and not giveup:
            if lcd_type == GLCD.TYPE_COLOR:
                time.sleep(0.05)
                render_color()
            else:
                time.sleep(0.5)
                render_mono()

            GLCD.LogiLcdUpdate()

        close()
    except (KeyboardInterrupt, WebDriverException):
        close()
    except Exception:
        close()
        raise
