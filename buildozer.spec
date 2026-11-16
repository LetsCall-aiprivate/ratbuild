name: Build RAT APK
on: [push, workflow_dispatch]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install Buildozer
        run: |
          pip install buildozer Cython==0.29.33
          sudo apt-get update && sudo apt-get install -y git zip unzip openjdk-17-jdk autoconf libtool pkg-config zlib1g-dev libncurses5-dev libncursesw5-dev libtinfo5 cmake libffi-dev libssl-dev
      - name: Build
        run: |
          buildozer android debug
      - name: Upload
        uses: actions/upload-artifact@v3
        with:
          name: rat-apk
          path: bin/*.apk
