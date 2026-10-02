from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import math

OUT = Path(__file__).parent
W, H = 2400, 1800
im = Image.new('RGB', (W, H), '#0b1220')
d = ImageDraw.Draw(im)
fonts = 'C:/Windows/Fonts/'
def font(n, bold=False):
    return ImageFont.truetype(fonts + ('arialbd.ttf' if bold else 'arial.ttf'), n)
def text(x,y,s,n=25,c='#b8c7db',bold=False):
    d.text((x,y),s,font=font(n,bold),fill=c)
def box(x,y,w,h,title,lines,color='#56c8ed'):
    d.rounded_rectangle((x,y,x+w,y+h),radius=18,fill='#152237',outline=color,width=2)
    d.rounded_rectangle((x+18,y+22,x+24,y+58),radius=3,fill=color)
    text(x+40,y+22,title,30,'#f1f5fb',True)
    for i,l in enumerate(lines): text(x+28,y+75+i*34,l,24)
def arrow(points,color='#56c8ed',both=False):
    d.line(points,fill=color,width=4,joint='curve')
    def head(a,b):
        ang=math.atan2(b[1]-a[1],b[0]-a[0]); r=15
        d.polygon([b,(b[0]-r*math.cos(ang-.48),b[1]-r*math.sin(ang-.48)),(b[0]-r*math.cos(ang+.48),b[1]-r*math.sin(ang+.48))],fill=color)
    head(points[-2],points[-1])
    if both: head(points[1],points[0])

text(70,45,'HomeTheaterX',56,'#ffffff',True)
text(70,114,'PROJECT ARCHITECTURE  /  Windows desktop audio controller',30)
text(70,165,'Source-based component view  |  HTTP commands + live WebSocket feedback',25)

text(70,238,'01  CLIENT INTERFACE',23,'#56c8ed',True)
box(70,280,650,215,'Web frontend  /  web/',[
    'index.html + CSS + JavaScript ES modules',
    'app.js / state.js / api.js / ws.js',
    'Effects, calibration, meters, Bluetooth, updates'])
box(70,530,650,178,'Desktop + LAN access',[
    'PyWebview window: localhost HTTP',
    'Browser on LAN: same web interface'])
arrow([(395,530),(395,495)],both=True)

text(840,238,'02  PYTHON APPLICATION',23,'#a698ff',True)
box(840,280,720,215,'web_server.py  /  runtime coordinator',[
    'Creates one shared AudioBackend instance',
    'Injects backend into HTTP + WebSocket handlers',
    'Starts server, tray, GUI and startup Dolby check'],'#a698ff')
box(840,555,345,210,'HTTP API',[
    'api_handler.py',
    'ThreadingHTTPServer',
    'Static files + /api/*'],'#a698ff')
box(1215,555,345,210,'WebSocket',[
    'websocket_service.py',
    'asyncio + websockets',
    'Peaks, state, commands'],'#a698ff')
arrow([(1012,495),(1012,555)],'#a698ff')
arrow([(1388,495),(1388,555)],'#a698ff')
arrow([(720,360),(775,360),(775,635),(840,635)],both=True)
text(735,404,'HTTP',21,'#56c8ed')
arrow([(720,450),(800,450),(800,802),(1388,802),(1388,765)],both=True)
text(830,812,'WebSocket: live state + audio/media controls',22,'#56c8ed')
text(840,870,'Default HTTP :5000   |   WebSocket :5010   |   Ports retry when occupied',22)

text(1680,238,'03  SUPPORTING COMPONENTS',23,'#e7b765',True)
box(1680,280,650,180,'Local settings',[
    'config_manager.py  <->  config.json',
    'Preferences, profiles, calibration, access token'],'#e7b765')
box(1680,505,650,205,'Windows app lifecycle',[
    'ui_service.py: PyWebview, tray, splash',
    'startup_manager.py: startup registry',
    'notifier.py: Windows toast notifications'],'#e7b765')
box(1680,755,650,165,'Recovery + distribution',[
    'Watchdog supervisor + crash_log.txt',
    'PyInstaller .spec -> EXE; Inno Setup installer'],'#e7b765')
arrow([(1560,345),(1680,345)],'#e7b765',True)
arrow([(1560,430),(1620,430),(1620,605),(1680,605)],'#e7b765')

text(70,970,'04  BACKEND SERVICES AND EXTERNAL INTEGRATIONS',23,'#69d7a3',True)
d.line([(1012,915),(1012,1008),(2090,1008)],fill='#69d7a3',width=4)
d.line([(1012,1008),(290,1008)],fill='#69d7a3',width=4)
arrow([(1012,765),(1012,915)],'#69d7a3')
arrow([(1388,765),(1600,765),(1600,915),(1012,915)],'#69d7a3')
for x in (290,890,1490,2090): arrow([(x,1008),(x,1050)],'#69d7a3')
box(70,1050,500,240,'AudioBackend',[
    'audio_backend.py',
    'Device selection, volume, mute',
    'Per-channel control + peak meters',
    'tone_generator: WAV channel tests'],'#69d7a3')
box(650,1050,500,240,'DSP + Dolby services',[
    'apo_service.py: presets / calibration',
    'apo/ templates -> APO config files',
    'dolby_service.py: pywinauto',
    'Reads / toggles Dolby in Sound UI'],'#69d7a3')
box(1230,1050,500,240,'Media + Bluetooth',[
    'media_service.py: WinRT sessions',
    'Metadata + playback commands',
    'bluetooth_service.py',
    'Status / name via Windows tools'],'#69d7a3')
box(1810,1050,520,240,'Update service',[
    'update_service.py',
    'Check latest GitHub release',
    'Download installer + launch update',
    'HTTPS outbound connection'],'#69d7a3')
for x in (320,900,1480,2070): arrow([(x,1290),(x,1350)],'#69d7a3')
box(70,1350,500,160,'Windows audio + speakers',[
    'Core Audio: pycaw / comtypes',
    'sounddevice + NumPy for tests'],'#69d7a3')
box(650,1350,500,160,'Equalizer APO + Sound UI',[
    'APO processes Windows audio',
    'Effects, upmix, delays and gains'],'#69d7a3')
box(1230,1350,500,160,'Windows system APIs',[
    'Media transport / Bluetooth',
    'Registry + PowerShell integration'],'#69d7a3')
box(1810,1350,520,160,'GitHub Releases',[
    'Release metadata + installer assets',
    'External update source'],'#69d7a3')

d.line([(70,1570),(2330,1570)],fill='#2c3f57',width=2)
text(70,1605,'HOW AUDIO FLOWS',23,'#ffffff',True)
text(70,1650,'Windows playback  ->  Windows audio engine / Equalizer APO  ->  Selected output device / speakers',28)
text(70,1705,'Arrows above show control / state dependencies. Audio samples do not stream through HTTP or WebSocket.',24)
im.save(OUT/'HomeTheaterX-architecture.png')
print(OUT/'HomeTheaterX-architecture.png')
