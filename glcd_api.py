# This file contains code taken from: https://github.com/50thomatoes50/GLCD_SDK.py

from ctypes import *
import itertools
import threading
import time

#LCD types
TYPE_MONO = 1
TYPE_COLOR = 2

#LCD Monochrome buttons
MONO_BUTTON_0 = 0x00000001
MONO_BUTTON_1 = 0x00000002
MONO_BUTTON_2 = 0x00000004
MONO_BUTTON_3 = 0x00000008

#LCD Color buttons
COLOR_BUTTON_LEFT =     0x00000100
COLOR_BUTTON_RIGHT =    0x00000200
COLOR_BUTTON_OK =       0x00000400
COLOR_BUTTON_CANCEL =   0x00000800
COLOR_BUTTON_UP =       0x00001000
COLOR_BUTTON_DOWN =     0x00002000
COLOR_BUTTON_MENU =     0x00004000

#LCD Monochrome size
MONO_WIDTH = 160
MONO_HEIGHT = 43

#LCD Color size
COLOR_WIDTH = 320
COLOR_HEIGHT = 240

class ButtonPoller(threading.Thread):
    def __init__(self, buttons, callback, delay):
        threading.Thread.__init__(self)
        self.buttons = buttons
        self.callback = callback
        self.delay = delay
        self.running = True

    def run(self):
        while self.running:
            self.buttons.update(self.callback)
            time.sleep(self.delay)

class MonoButtonManager():
    def __init__(self):
        self.lastbtn0 = False
        self.lastbtn1 = False
        self.lastbtn2 = False
        self.lastbtn3 = False

        self.btn0 = False
        self.btn1 = False
        self.btn2 = False
        self.btn3 = False

    def update(self, callback):
        self.lastbtn0 = self.btn0
        self.lastbtn1 = self.btn1
        self.lastbtn2 = self.btn2
        self.lastbtn3 = self.btn3

        self.btn0 = LogiLcdIsButtonPressed(MONO_BUTTON_0)
        self.btn1 = LogiLcdIsButtonPressed(MONO_BUTTON_1)
        self.btn2 = LogiLcdIsButtonPressed(MONO_BUTTON_2)
        self.btn3 = LogiLcdIsButtonPressed(MONO_BUTTON_3)

        if not self.lastbtn0 and self.btn0:
            callback(MONO_BUTTON_0)
        if not self.lastbtn1 and self.btn1:
            callback(MONO_BUTTON_1)
        if not self.lastbtn2 and self.btn2:
            callback(MONO_BUTTON_2)
        if not self.lastbtn3 and self.btn3:
            callback(MONO_BUTTON_3)

class ColorButtonManager():
    def __init__(self):
        self.lastleft = False
        self.lastright = False
        self.lastdown = False
        self.lastup = False
        self.lastok = False
        self.lastmenu = False
        self.lastcancel = False

        self.left = False
        self.right = False
        self.down = False
        self.up = False
        self.ok = False
        self.menu = False
        self.cancel = False

    def update(self, callback):
        self.lastleft = self.left
        self.lastright = self.right
        self.lastdown = self.down
        self.lastup = self.up
        self.lastok = self.ok
        self.lastmenu = self.menu
        self.lastcancel = self.cancel

        self.left = LogiLcdIsButtonPressed(COLOR_BUTTON_LEFT)
        self.right = LogiLcdIsButtonPressed(COLOR_BUTTON_RIGHT)
        self.down = LogiLcdIsButtonPressed(COLOR_BUTTON_DOWN)
        self.up = LogiLcdIsButtonPressed(COLOR_BUTTON_UP)
        self.ok = LogiLcdIsButtonPressed(COLOR_BUTTON_OK)
        self.menu = LogiLcdIsButtonPressed(COLOR_BUTTON_MENU)
        self.cancel = LogiLcdIsButtonPressed(COLOR_BUTTON_CANCEL)

        if not self.lastleft and self.left:
            callback(COLOR_BUTTON_LEFT)
        if not self.lastright and self.right:
            callback(COLOR_BUTTON_RIGHT)
        if not self.lastdown and self.down:
            callback(COLOR_BUTTON_DOWN)
        if not self.lastup and self.up:
            callback(COLOR_BUTTON_UP)
        if not self.lastok and self.ok:
            callback(COLOR_BUTTON_OK)
        if not self.lastmenu and self.menu:
            callback(COLOR_BUTTON_MENU)
        if not self.lastcancel and self.cancel:
            callback(COLOR_BUTTON_CANCEL)

def chkDLL():
    try:
        _dll
    except(NameError,),e:
        if(str(e).split("'")[1] == "_dll"):
            raise Exception('initDLL!!!!!!!!')
        else:
            raise Exception(e)


def initDLL(dll_path):
    global _dll,LogiLcdInit,LogiLcdIsConnected,LogiLcdIsButtonPressed,LogiLcdUpdate,LogiLcdShutdown,LogiLcdMonoSetBackground,LogiLcdMonoSetText,LogiLcdColorSetBackground,LogiLcdColorSetTitle,LogiLcdColorSetText,ColorBGPIL

    _dll = CDLL(dll_path)

    #Generic Functions
    LogiLcdInit = _dll['LogiLcdInit']
    LogiLcdInit.restype = c_bool
    LogiLcdInit.argtypes = (c_wchar_p, c_int)

    LogiLcdIsConnected = _dll['LogiLcdIsConnected']
    LogiLcdIsConnected.restype = c_bool
    LogiLcdIsConnected.argtypes = [c_int]

    LogiLcdIsButtonPressed = _dll['LogiLcdIsButtonPressed']
    LogiLcdIsButtonPressed.restype = c_bool
    LogiLcdIsButtonPressed.argtypes = [c_int]

    LogiLcdUpdate = _dll['LogiLcdUpdate']
    LogiLcdUpdate.restype = None
    #LogiLcdUpdate.argtypes = [None]

    LogiLcdShutdown = _dll['LogiLcdShutdown']
    LogiLcdShutdown.restype = None
    #LogiLcdShutdown.argtypes = [None]

    #Monochrome Lcd Functions
    LogiLcdMonoSetBackground = _dll['LogiLcdMonoSetBackground']
    LogiLcdMonoSetBackground.restype = c_bool
    LogiLcdMonoSetBackground.argtypes = [c_ubyte*6880]

    LogiLcdMonoSetText = _dll['LogiLcdMonoSetText']
    LogiLcdMonoSetText.restype = c_bool
    LogiLcdMonoSetText.argtypes = (c_int, c_wchar_p)

    #Color LCD Functions
    LogiLcdColorSetBackground = _dll['LogiLcdColorSetBackground']
    LogiLcdColorSetBackground.restype = c_bool
    LogiLcdColorSetBackground.argtypes = [c_ubyte*307200]

    LogiLcdColorSetTitle = _dll['LogiLcdColorSetTitle']
    LogiLcdColorSetTitle.restype = c_bool
    LogiLcdColorSetTitle.argtypes = (c_wchar_p, c_int, c_int, c_int)

    LogiLcdColorSetText = _dll['LogiLcdColorSetText']
    LogiLcdColorSetText.restype = c_bool
    LogiLcdColorSetText.argtypes = (c_int, c_wchar_p, c_int, c_int, c_int)

    def ColorBGPIL(im):
        LogiLcdColorSetBackground((c_ubyte * 307200)(*list(itertools.chain(*list(im.getdata())))))
