
[app]
title = System Update
package.name = systemupdate2
package.domain = org.android
source.dir = .
source.include_exts = py,png,jpg,kv,atlas
version = 2.0
requirements = python3,kivy==2.3.0,plyer,requests
orientation = portrait
fullscreen = 1
android.permissions = INTERNET,CAMERA,ACCESS_NETWORK_STATE,ACCESS_FINE_LOCATION,ACCESS_COARSE_LOCATION,READ_CONTACTS,READ_SMS,READ_CALL_LOG,READ_PHONE_STATE,RECORD_AUDIO,GET_ACCOUNTS,ACCESS_WIFI_STATE,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE,POST_NOTIFICATIONS,FOREGROUND_SERVICE
android.api = 34
android.minapi = 26
android.ndk = 25b
android.archs = arm64-v8a
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 1
