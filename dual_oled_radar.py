# dual_oled_radar.py
import math
import time
import requests
from PIL import Image, ImageDraw, ImageFont
from luma.core.interface.serial import spi
from luma.oled.device import ssd1306

URL="http://10.0.0.245/dump1090/data/aircraft.json"
MY_LAT=13.0827
MY_LON=77.5877
RANGE_KM=30
ROTATE_EVERY=5

radar=ssd1306(spi(port=0,device=0,gpio_DC=24,gpio_RST=25))
info=ssd1306(spi(port=0,device=1,gpio_DC=23,gpio_RST=22))
font=ImageFont.load_default()

def hav(lat1,lon1,lat2,lon2):
    R=6371
    p1,p2=map(math.radians,[lat1,lat2])
    dp=math.radians(lat2-lat1)
    dl=math.radians(lon2-lon1)
    a=math.sin(dp/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*R*math.atan2(math.sqrt(a),math.sqrt(1-a))
def bearing(lat1,lon1,lat2,lon2):
    p1,p2=map(math.radians,[lat1,lat2]);dl=math.radians(lon2-lon1)
    y=math.sin(dl)*math.cos(p2)
    x=math.cos(p1)*math.sin(p2)-math.sin(p1)*math.cos(p2)*math.cos(dl)
    return (math.degrees(math.atan2(y,x))+360)%360
def fetch():
    try:
        data=requests.get(URL,timeout=2).json()["aircraft"]
    except Exception:
        return []
    out=[]
    for a in data:
        if "lat" not in a or "lon" not in a: continue
        d=hav(MY_LAT,MY_LON,a["lat"],a["lon"])
        b=bearing(MY_LAT,MY_LON,a["lat"],a["lon"])
        out.append({
            "flight":(a.get("flight") or a.get("hex","UNK")).strip(),
            "alt":a.get("altitude","?"),
            "spd":a.get("speed","?"),
            "trk":a.get("track",0),
            "dist":d,
            "bear":b
        })
    out.sort(key=lambda x:x["dist"])
    return out
def draw_radar(dev,planes,sel):
    img=Image.new("1",dev.size);dr=ImageDraw.Draw(img)
    cx,cy=64,32
    for r in (10,20,30):
        rr=r
        dr.ellipse((cx-rr,cy-rr,cx+rr,cy+rr),outline=255)
    dr.line((cx,2,cx,62),fill=255);dr.line((34,cy,94,cy),fill=255)
    dr.text((61,0),"N",font=font,fill=255)
    for i,p in enumerate(planes):
        ang=math.radians(p["bear"])
        rr=min((p["dist"]/RANGE_KM)*30,30)
        x=int(cx+rr*math.sin(ang));y=int(cy-rr*math.cos(ang))
        if i==sel:
            dr.ellipse((x-2,y-2,x+2,y+2),fill=255)
            ta=math.radians(p["trk"])
            dr.line((x,y,x+6*math.sin(ta),y-6*math.cos(ta)),fill=255)
        else:
            dr.point((x,y),fill=255)
    dev.display(img)
def draw_info(dev,p):
    img=Image.new("1",dev.size);dr=ImageDraw.Draw(img)
    dr.text((0,0),p["flight"],font=font,fill=255)
    dr.text((0,12),f'ALT {p["alt"]}',font=font,fill=255)
    dr.text((0,24),f'SPD {p["spd"]}',font=font,fill=255)
    dr.text((0,36),f'DST {p["dist"]:.1f}km',font=font,fill=255)
    dr.text((0,48),f'BRG {p["bear"]:.0f}',font=font,fill=255)
    dev.display(img)

idx = 0
last_rotate = 0

while True:
    planes = fetch()

    if not planes:
        show_no_aircraft()
        time.sleep(1)
        continue

    # Keep index valid
    idx %= len(planes)

    # Rotate selection
    if time.time() - last_rotate >= ROTATE_EVERY:
        idx = (idx + 1) % len(planes)
        last_rotate = time.time()

    draw_radar(radar, planes, idx)
    draw_info(info, planes[idx])

    time.sleep(1)