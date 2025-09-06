import pyautogui
import time

# Interval between fake activity (every 5 minutes)
INTERVAL = 300  # 5 * 60 seconds

try:
    print("Anti-AFK script started. Press Ctrl+C to stop.")
    while True:
        pyautogui.moveRel(0, 10, duration=0.1)
        pyautogui.moveRel(0, -10, duration=0.1)
        time.sleep(INTERVAL)
except KeyboardInterrupt:
    print("Stopped.")
