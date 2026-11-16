name: Build RAT APK
on: [push, workflow_dispatch]
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Free up disk space
        run: |
          sudo rm -rf /usr/local/lib/android/sdk/ndk
          sudo rm -rf /usr/share/dotnet /opt/ghc /usr/local/.ghcup
          df -h

      - name: Wipe any stale buildozer state
        run: rm -rf ~/.buildozer

      - name: Install system dependencies
        run: |
          sudo apt-get update
          sudo apt-get install -y git zip unzip openjdk-17-jdk autoconf libtool pkg-config \
            zlib1g-dev libncurses-dev libtinfo6 cmake libffi-dev libssl-dev
          sudo apt-get install -y libncurses5-dev libtinfo5 || true

      - name: Force Java 17
        run: |
          echo "JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64" >> $GITHUB_ENV
          echo "/usr/lib/jvm/java-17-openjdk-amd64/bin" >> $GITHUB_PATH

      - name: Install Buildozer
        run: |
          pip install buildozer Cython==0.29.33

      - name: Link runner SDK into Buildozer's expected path
        run: |
          mkdir -p /home/runner/.buildozer/android/platform
          ln -s /usr/local/lib/android/sdk /home/runner/.buildozer/android/platform/android-sdk

      - name: Install SDK components + accept licenses
        run: |
          SDKMANAGER=/usr/local/lib/android/sdk/cmdline-tools/latest/bin/sdkmanager
          yes | $SDKMANAGER --licenses > /dev/null || true
          $SDKMANAGER --install "build-tools;34.0.0" "platform-tools" "platforms;android-33" > /dev/null
          ls /usr/local/lib/android/sdk/build-tools

      - name: Build APK
        run: buildozer android debug

      - name: Upload APK
        uses: actions/upload-artifact@v4
        with:
          name: rat-apk
          path: bin/*.apk
