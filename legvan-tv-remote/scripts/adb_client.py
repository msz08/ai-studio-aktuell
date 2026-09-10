"""ADB connection wrapper for Android TV / Google TV.

Reads host, port, and display name from config.json at the project root.
All values fall back to sensible defaults if config.json is absent, and
importing this module never aborts: the setup wizard connects to the TV to
read its model *before* it writes config.json.  Entry points that do need a
configured TV call require_config() themselves.
"""
import json
import sys
import time
from pathlib import Path

_CONFIG_PATH = Path(__file__).resolve().parent.parent / 'config.json'


def _load_config() -> dict:
    if _CONFIG_PATH.exists():
        try:
            return json.loads(_CONFIG_PATH.read_text())
        except Exception:
            pass
    return {}


_cfg = _load_config()

TV_HOST = _cfg.get('host', '')
TV_PORT = _cfg.get('port', 5555)
TV_NAME = _cfg.get('name', 'Android TV')

KEY_PATH        = Path.home() / '.android' / 'adbkey'
CONNECT_TIMEOUT = 9.0
AUTH_TIMEOUT    = 10.0   # seconds to wait for the RSA-key prompt on the TV screen


def require_config() -> None:
    """Exit with a setup hint unless config.json names a TV host.

    Used by the CLI and the web GUI, which have no TV to talk to without it.
    install.py deliberately does not call this — it runs before config.json
    exists and passes the host explicitly to TVClient.
    """
    if TV_HOST:
        return
    if _CONFIG_PATH.exists():
        print(f"ERROR: no TV host in {_CONFIG_PATH}. Re-run './install' to set up your TV.")
    else:
        print("ERROR: config.json not found. Run './install' first to set up your TV.")
    sys.exit(1)


def load_signer():
    from adb_shell.auth.sign_pythonrsa import PythonRSASigner
    priv = KEY_PATH.read_text()
    pub  = KEY_PATH.with_suffix('.pub').read_text()
    return PythonRSASigner(pub, priv)


class TVClient:
    """ADB connection to an Android TV with auto-reconnect.

    Args:
        host:         Override the IP from config.json.
        port:         Override the port from config.json.
        auth_timeout: Seconds to wait for RSA-key acceptance on the TV.
                      Increase to 30+ during first-time setup.
    """

    def __init__(self, host: str = None, port: int = None, auth_timeout: float = None):
        from adb_shell.adb_device import AdbDeviceTcp
        self._host         = host or TV_HOST
        self._port         = port or TV_PORT
        self._auth_timeout = auth_timeout if auth_timeout is not None else AUTH_TIMEOUT
        self._signer       = load_signer()
        self._device       = AdbDeviceTcp(
            self._host, self._port, default_transport_timeout_s=CONNECT_TIMEOUT
        )
        self._connected = False

    def connect(self):
        self._device.connect(rsa_keys=[self._signer], auth_timeout_s=self._auth_timeout)
        self._connected = True
        print(f"Connected to {self._host}:{self._port}")

    def shell(self, cmd: str, retries: int = 2) -> str:
        for attempt in range(retries + 1):
            try:
                return self._device.shell(cmd) or ''
            except Exception as e:
                if attempt == retries:
                    raise
                print(f"Connection lost ({e}), reconnecting…")
                self._device.close()
                time.sleep(1)
                self._device.connect(rsa_keys=[self._signer], auth_timeout_s=self._auth_timeout)

    def key(self, code) -> None:
        """Send a keyevent. Accepts int code or KEYCODE_NAME string."""
        self.shell(f'input keyevent {code}')

    def launch_app(self, activity: str) -> None:
        """Launch an app by package/activity string like 'com.netflix.ninja/.MainActivity'."""
        self.shell(f'am start -n {activity}')

    def go_home(self) -> None:
        self.shell('am start -a android.intent.action.MAIN -c android.intent.category.HOME')

    def screen_state(self) -> str:
        """Returns 'ON' or 'OFF'."""
        result = self.shell("dumpsys power | grep 'Display Power'")
        return 'ON' if 'state=ON' in result else 'OFF'

    def wakefulness(self) -> str:
        """Returns 'Awake', 'Asleep', or 'Dreaming'."""
        result = self.shell("dumpsys power | grep mWakefulness=")
        for word in ('Awake', 'Asleep', 'Dreaming'):
            if word in result:
                return word
        return result.strip()

    def current_app(self) -> str:
        """Returns the package name of the currently focused app."""
        result = self.shell("dumpsys window | grep mCurrentFocus")
        if not result.strip() or 'mCurrentFocus=null' in result:
            result = self.shell("dumpsys activity activities | grep mResumedActivity")
        try:
            part = result.split('u0 ')[-1].strip()
            pkg = part.split('/')[0].replace('}', '')
            return pkg if pkg else result.strip()
        except Exception:
            return result.strip()

    def device_info(self) -> dict:
        """Return {manufacturer, model, android} from getprop."""
        return {
            'manufacturer': self.shell('getprop ro.product.manufacturer').strip(),
            'model':        self.shell('getprop ro.product.model').strip(),
            'android':      self.shell('getprop ro.build.version.release').strip(),
        }

    def launch_assistant(self) -> None:
        """Launch Google Assistant via am start (most reliable on Google TV).

        Falls back to KEYCODE_VOICE_ASSIST (231) if the intent fails.
        KEYCODE_SEARCH (84) is NOT used — it is a voice-streaming protocol
        trigger, not a UI launcher.
        """
        try:
            result = self.shell(
                'am start -n com.google.android.googlequicksearchbox'
                '/com.google.android.googlequicksearchbox.VoiceSearchActivity'
            )
            if 'Error' in result or 'Exception' in result:
                raise RuntimeError(result.strip())
        except Exception:
            self.key(231)

    def send_text(self, text: str) -> None:
        """Send text to the focused input field via the Accessibility Service."""
        import shlex
        escaped = shlex.quote(text)
        self.shell(f'am broadcast -a com.porter.tvremote.action.INJECT_TEXT -e msg {escaped}')

    def text_action(self, action: str) -> None:
        """Send a text action (clear, backspace, enter) via the Accessibility Service."""
        self.shell(f'am broadcast -a com.porter.tvremote.action.INJECT_TEXT -e action {action}')

    def close(self) -> None:
        self._device.close()
        self._connected = False

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *_):
        self.close()

    def push_file(self, local_path: str, remote_path: str) -> None:
        original_timeout = self._device._transport._default_transport_timeout_s
        try:
            self._device._transport._default_transport_timeout_s = 600.0
            self._device.push(local_path, remote_path)
        finally:
            self._device._transport._default_transport_timeout_s = original_timeout

    def install_apk(self, local_path: str) -> str:
        import time
        remote_tmp = f"/data/local/tmp/temp_install_{int(time.time())}.apk"
        self.push_file(local_path, remote_tmp)
        
        original_timeout = self._device._transport._default_transport_timeout_s
        try:
            self._device._transport._default_transport_timeout_s = 300.0
            res = self.shell(f"pm install -r {remote_tmp}")
        finally:
            self._device._transport._default_transport_timeout_s = original_timeout
            
        self.shell(f"rm {remote_tmp}")
        return res

    def take_screenshot(self) -> bytes:
        import tempfile, os
        remote_tmp = "/data/local/tmp/screencap.png"
        self.shell(f"screencap -p {remote_tmp}")
        fd, local_path = tempfile.mkstemp(suffix=".png")
        os.close(fd)
        try:
            self._device.pull(remote_tmp, local_path)
            self.shell(f"rm {remote_tmp}")
            with open(local_path, "rb") as f:
                return f.read()
        finally:
            if os.path.exists(local_path):
                os.remove(local_path)

    def reboot(self) -> None:
        self.shell("reboot")

    def get_storage(self) -> str:
        res = self.shell("df -h /data")
        lines = res.strip().splitlines()
        if len(lines) > 1:
            parts = lines[1].split()
            if len(parts) >= 4:
                return f"Free: {parts[3]} / Total: {parts[1]}"
        return "Unknown"

    def clear_cache(self) -> str:
        self.shell("am kill-all")
        return "Background apps cleared"

    def get_installed_apps(self) -> list:
        res = self.shell("pm list packages -3")
        pkgs = set(line.replace("package:", "").strip() for line in res.splitlines() if line.startswith("package:"))
        common = ["com.google.android.youtube.tv", "com.netflix.ninja", "com.amazon.amazonvideo.livingroom", "com.disney.disneyplus", "org.xbmc.kodi", "com.spotify.tv.android", "com.tcl.initsetup"]
        res_sys = self.shell("pm list packages -s")
        sys_pkgs = set(line.replace("package:", "").strip() for line in res.splitlines() if line.startswith("package:"))
        for c in common:
            if c in sys_pkgs:
                pkgs.add(c)
        return sorted(list(pkgs))
