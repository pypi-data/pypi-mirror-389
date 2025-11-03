import pyautogui
import random
import time
import threading
from pynput import mouse, keyboard

MOVE_INTERVAL_SECONDS = 3  
MIN_PIXELS_TO_MOVE = 1     
MAX_PIXELS_TO_MOVE = 15    
KEY_PRESS_INTERVAL = 20
USER_ACTIVITY_TIMEOUT = 5  # Seconds to wait after user stops activity before resuming

class UserActivityMonitor:
    def __init__(self, timeout_seconds=USER_ACTIVITY_TIMEOUT):
        self.timeout_seconds = timeout_seconds
        self.last_activity_time = 0
        self.is_user_active = False
        self.lock = threading.Lock()
        
    def on_mouse_move(self, x, y):
        with self.lock:
            self.last_activity_time = time.time()
            if not self.is_user_active:
                self.is_user_active = True
                print("🔴 User activity detected - pausing automation")
    
    def on_mouse_click(self, x, y, button, pressed):
        with self.lock:
            self.last_activity_time = time.time()
            if not self.is_user_active:
                self.is_user_active = True
                print("🔴 User activity detected - pausing automation")
    
    def on_mouse_scroll(self, x, y, dx, dy):
        with self.lock:
            self.last_activity_time = time.time()
            if not self.is_user_active:
                self.is_user_active = True
                print("🔴 User activity detected - pausing automation")
    
    def on_key_press(self, key):
        with self.lock:
            self.last_activity_time = time.time()
            if not self.is_user_active:
                self.is_user_active = True
                print("🔴 User activity detected - pausing automation")
    
    def should_pause(self):
        with self.lock:
            current_time = time.time()
            if self.is_user_active and (current_time - self.last_activity_time) > self.timeout_seconds:
                self.is_user_active = False
                print("🟢 User activity timeout - resuming automation")
            return self.is_user_active
    
    def start_monitoring(self):
        # Start mouse listener
        mouse_listener = mouse.Listener(
            on_move=self.on_mouse_move,
            on_click=self.on_mouse_click,
            on_scroll=self.on_mouse_scroll
        )
        mouse_listener.daemon = True
        mouse_listener.start()
        
        # Start keyboard listener
        keyboard_listener = keyboard.Listener(on_press=self.on_key_press)
        keyboard_listener.daemon = True
        keyboard_listener.start()

def main():
    pyautogui.FAILSAFE = False
    print("--- Workspace Monitor Started ---")
    print(f"Monitoring workspace activity every {MOVE_INTERVAL_SECONDS} seconds.")
    print(f"Safety feature: Will pause when user activity is detected (timeout: {USER_ACTIVITY_TIMEOUT}s)")
    print("Press Ctrl-C in the terminal to stop the program.")

    # Initialize user activity monitor
    activity_monitor = UserActivityMonitor()
    activity_monitor.start_monitoring()

    move_count = 0
    try:
        while True:
            time.sleep(MOVE_INTERVAL_SECONDS)
            
            # Check if we should pause due to user activity
            if activity_monitor.should_pause():
                continue  # Skip this iteration if user is active
            screenWidth, screenHeight = pyautogui.size()
            current_x, current_y = pyautogui.position()
            direction_x = random.choice([-1, 1])
            direction_y = random.choice([-1, 1])
            offset_x = direction_x * random.randint(MIN_PIXELS_TO_MOVE, MAX_PIXELS_TO_MOVE)
            offset_y = direction_y * random.randint(MIN_PIXELS_TO_MOVE, MAX_PIXELS_TO_MOVE)
            new_x = current_x + offset_x
            new_y = current_y + offset_y
            new_x = max(0, min(screenWidth - 1, new_x))
            new_y = max(0, min(screenHeight - 1, new_y))
            pyautogui.moveTo(new_x, new_y, duration=0.25)
            print(f"Cursor position updated: ({new_x}, {new_y})")
            
            move_count += 1
            if move_count % KEY_PRESS_INTERVAL == 0:
                pyautogui.press('shift')
                print("System refresh triggered.")
    except KeyboardInterrupt:
        print("\n--- Workspace Monitor Stopped ---")
    except Exception as e:
        print(f"\nAn error occurred: {e}")

if __name__ == "__main__":
    main()