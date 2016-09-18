from distutils.core import setup
import glob
import py2exe

data_files = [("images", glob.glob("images/*.png")),
              ("", glob.glob("LogitechLcd*.dll")),
              ("", ["cacert.pem"]),
              ("", ["chromedriver.exe"]),
             ]

setup(
    windows=['spotify_glcd.py'],
    data_files = data_files
)
