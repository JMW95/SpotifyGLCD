# SpotifyGLCD

A Python app which uses the Logitech LCDSDK and Selenium WebDriver to report Spotify's current track information to Logitech LCD-equipped peripherals such as G19 and G13. Also allows control of basic Spotify functions from the device.

Currently Windows only.

## Usage
To run:
```shell
$ python spotify_glcd.py
```

To build an .exe:
```shell
$ python setup.py py2exe
```
The dist folder will contain all files needed to run it, including spotify_glcd.exe.

## Requirements
Requires python packages:
- selenium
- PIL / pillow
- requests

For building to an .exe, requires:
- py2exe

## Acknowledgements
This project would have taken much longer without the excellent **GLCD_SDK** (https://github.com/50thomatoes50/GLCD_SDK.py) and **spotify-local-http-api** (https://github.com/cgbystrom/spotify-local-http-api). Some of the code here comes directly from those projects.

Also uses chromedriver, which makes the task of probing Spotify incredibly straightfoward. (https://sites.google.com/a/chromium.org/chromedriver/)

## License
All code is distributed under the Mozilla Public License unless otherwise stated.

chromedriver.exe is packaged for ease of installation.
Logitech LCDSDK .dlls are packaged for ease of installation.
cacert.pem from the requests module is packaged to fix a bug when py2exe exports the project.
These extra files are not covered by the Mozilla Public License.
