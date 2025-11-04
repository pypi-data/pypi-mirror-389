import cv2
import os
import time
import numpy as np
import msvcrt
import shutil
from PIL import Image

class FullScreenColorVideoPlayer:
    def __init__(self, color_mode=True):
        self.color_mode = color_mode
        self.chars = "@%#*+=-:. "
        self.playing = False
        self.precompute_char_mapping()
        self.get_terminal_size()
        
    def get_terminal_size(self):
        """Get current terminal dimensions and try to maximize"""
        try:
            # Try to maximize terminal first
            self.maximize_terminal()
            time.sleep(0.5)  # Allow time for resize
            
            # Get actual terminal size
            size = shutil.get_terminal_size()
            self.terminal_width = size.columns
            self.terminal_height = size.lines - 4  # Reserve lines for info
            print(f"Terminal size: {self.terminal_width}x{self.terminal_height}")
        except Exception as e:
            print(f"Could not detect terminal size: {e}")
            self.terminal_width = 120
            self.terminal_height = 40
    
    def maximize_terminal(self):
        """Try to maximize terminal window"""
        try:
            if os.name == 'nt':  # Windows
                # Try to set maximum reasonable size for CMD
                os.system('mode con: cols=200 lines=60')
            else:  # Linux/Mac
                # Send resize escape sequences
                print("\033[8;60;200t")
        except:
            pass
    
    def clear_screen(self):
        """Clear entire screen"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def precompute_char_mapping(self):
        """Precompute character mappings for speed"""
        self.char_map = {}
        for pixel_value in range(256):
            scale = len(self.chars) - 1
            char_index = min(int(pixel_value / 255 * scale), scale)
            self.char_map[pixel_value] = self.chars[char_index]
    
    def rgb_to_ansi(self, r, g, b):
        """Convert RGB to ANSI color code"""
        if not self.color_mode:
            return ""
        return f"\033[38;2;{r};{g};{b}m"
    
    def reset_color(self):
        """Reset ANSI color"""
        return "\033[0m" if self.color_mode else ""
    
    def frame_to_fullscreen_color_ascii(self, frame):
        """Convert frame to full screen color ASCII art"""
        try:
            # Calculate dimensions to fill terminal while maintaining aspect ratio
            original_height, original_width = frame.shape[:2]
            aspect_ratio = original_height / original_width
            
            # Use full terminal width
            target_width = self.terminal_width
            target_height = int(target_width * aspect_ratio * 0.5)  # 0.5 for character aspect
            
            # If too tall for terminal, scale down
            if target_height > self.terminal_height:
                target_height = self.terminal_height
                target_width = int(target_height / aspect_ratio / 0.5)
            
            # Resize frame to calculated dimensions
            frame_resized = cv2.resize(frame, (target_width, target_height))
            frame_rgb = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
            frame_gray = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2GRAY)
            
            # Convert to color ASCII
            ascii_lines = []
            for y in range(target_height):
                line = ""
                last_color = None
                
                for x in range(target_width):
                    brightness = frame_gray[y, x]
                    char = self.char_map[brightness]
                    r, g, b = frame_rgb[y, x]
                    
                    # Only add color code when color changes (optimization)
                    current_color = (r, g, b)
                    if current_color != last_color:
                        color_code = self.rgb_to_ansi(r, g, b)
                        line += color_code
                        last_color = current_color
                    
                    line += char
                
                line += self.reset_color()
                ascii_lines.append(line)
            
            return '\n'.join(ascii_lines), target_width, target_height
            
        except Exception as e:
            return f"Error converting frame: {e}", 0, 0
    
    def center_output(self, ascii_art, content_width, content_height):
        """Center the ASCII art on screen"""
        lines = ascii_art.split('\n')
        
        # Calculate padding
        vertical_padding = max(0, (self.terminal_height - content_height) // 2)
        horizontal_padding = max(0, (self.terminal_width - content_width) // 2)
        
        # Build centered output
        centered_lines = []
        
        # Top padding
        for _ in range(vertical_padding):
            centered_lines.append(" " * self.terminal_width)
        
        # Centered content
        for line in lines:
            padded_line = " " * horizontal_padding + line
            centered_lines.append(padded_line)
        
        # Bottom padding
        remaining_lines = self.terminal_height - len(centered_lines)
        for _ in range(remaining_lines):
            centered_lines.append(" " * self.terminal_width)
        
        return '\n'.join(centered_lines)
    
    def play_video(self, video_path):
        """Play video in full screen color ASCII"""
        self.get_terminal_size()  # Ensure we have current dimensions
        
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            print(f"Error: Could not open video {video_path}")
            return False
        
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        original_fps = cap.get(cv2.CAP_PROP_FPS)
        frame_delay = 1.0 / original_fps if original_fps > 0 else 1.0 / 24
        
        print(f"FULL SCREEN COLOR MODE: {self.terminal_width}x{self.terminal_height}")
        print(f"Video: {total_frames} frames, {original_fps:.1f} FPS")
        print("Press 'q' to quit, 'f' to toggle info, 't' to toggle color, 'p' to pause")
        time.sleep(2)
        
        self.playing = True
        current_frame = 0
        show_info = True
        start_time = time.time()
        
        try:
            while self.playing and current_frame < total_frames:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Convert to full screen color ASCII
                ascii_frame, width, height = self.frame_to_fullscreen_color_ascii(frame)
                centered_frame = self.center_output(ascii_frame, width, height)
                
                self.clear_screen()
                
                # Display info if enabled
                if show_info:
                    progress = (current_frame / total_frames) * 100
                    elapsed = time.time() - start_time
                    estimated_total = total_frames * frame_delay
                    remaining = max(0, estimated_total - elapsed)
                    
                    info_line = (f"Frame: {current_frame}/{total_frames} ({progress:.1f}%) | "
                                f"Time: {elapsed:.1f}s / {estimated_total:.1f}s | "
                                f"Remaining: {remaining:.1f}s | "
                                f"Size: {width}x{height} | "
                                f"Color: {'ON' if self.color_mode else 'OFF'}")
                    print(info_line)
                    print("═" * self.terminal_width)
                
                # Display the centered ASCII art
                print(centered_frame)
                
                if show_info:
                    print("═" * self.terminal_width)
                    print("Controls: [Q]uit [F]toggle info [T]oggle color [P]ause")
                
                current_frame += 1
                
                # Input handling
                if msvcrt.kbhit():
                    key = msvcrt.getch().decode('utf-8').lower()
                    if key == 'q':
                        break
                    elif key == 'f':
                        show_info = not show_info
                    elif key == 't':
                        self.color_mode = not self.color_mode
                    elif key == 'p':
                        print("\n" + " " * (self.terminal_width // 2 - 10) + "PAUSED - Press any key to continue...")
                        msvcrt.getch()
                
                # Maintain timing
                target_time = current_frame / original_fps
                actual_time = time.time() - start_time
                sleep_time = max(0.001, target_time - actual_time)
                time.sleep(sleep_time)
                
        except Exception as e:
            print(f"Error: {e}")
            return False
        finally:
            cap.release()
            self.playing = False
            total_time = time.time() - start_time
            actual_fps = current_frame / total_time if total_time > 0 else 0
            print(f"\nPlayback complete! Average FPS: {actual_fps:.1f}")
        
        return True

class AdaptiveFullScreenColorPlayer:
    def __init__(self):
        self.chars = " ░▒▓█"  # Better for full screen
        self.color_mode = True
        self.precompute_mappings()
        self.update_terminal_size()
    
    def precompute_mappings(self):
        """Precompute character mappings"""
        self.char_map = {}
        for i in range(256):
            idx = int(i / 256 * (len(self.chars) - 1))
            self.char_map[i] = self.chars[idx]
    
    def update_terminal_size(self):
        """Update terminal size"""
        try:
            size = shutil.get_terminal_size()
            self.terminal_width = size.columns
            self.terminal_height = size.lines - 4
        except:
            self.terminal_width = 120
            self.terminal_height = 40
    
    def maximize_window(self):
        """Maximize terminal window"""
        try:
            if os.name == 'nt':
                os.system('mode con: cols=250 lines=80')
            else:
                print("\033[8;80;250t")
            time.sleep(0.5)
            self.update_terminal_size()
        except:
            pass
    
    def ultra_fast_color_convert(self, frame):
        """Ultra-fast full screen color conversion"""
        self.update_terminal_size()
        
        original_height, original_width = frame.shape[:2]
        aspect_ratio = original_height / original_width
        
        # Calculate maximum size that fits terminal
        target_width = self.terminal_width
        target_height = int(target_width * aspect_ratio * 0.5)
        
        if target_height > self.terminal_height:
            target_height = self.terminal_height
            target_width = int(target_height / aspect_ratio / 0.5)
        
        # Fast resize
        frame_resized = cv2.resize(frame, (target_width, target_height))
        frame_rgb = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
        frame_gray = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2GRAY)
        
        # Vectorized processing for speed
        ascii_lines = []
        for y in range(target_height):
            line = ""
            last_color = None
            
            for x in range(target_width):
                brightness = frame_gray[y, x]
                char = self.char_map[brightness]
                r, g, b = frame_rgb[y, x]
                
                # Apply slight color enhancement for better visibility
                r = min(255, int(r * 1.1))
                g = min(255, int(g * 1.1))
                b = min(255, int(b * 1.1))
                
                current_color = (r, g, b)
                if current_color != last_color:
                    color_code = f"\033[38;2;{r};{g};{b}m" if self.color_mode else ""
                    line += color_code
                    last_color = current_color
                
                line += char
            
            line += "\033[0m"
            ascii_lines.append(line)
        
        return '\n'.join(ascii_lines), target_width, target_height
    
    def play_video(self, video_path):
        """Adaptive full screen playback that handles resizing"""
        print("Initializing adaptive full screen color mode...")
        self.maximize_window()
        
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            print(f"Cannot open video: {video_path}")
            return False
        
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        print(f"Adaptive Full Screen: {self.terminal_width}x{self.terminal_height}")
        print("Video will adapt to terminal resizing automatically!")
        time.sleep(2)
        
        current_frame = 0
        show_info = True
        start_time = time.time()
        last_size = (self.terminal_width, self.terminal_height)
        
        try:
            while current_frame < total_frames:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Check for terminal resize
                current_size = (self.terminal_width, self.terminal_height)
                self.update_terminal_size()
                if current_size != last_size:
                    print("Terminal resize detected! Adapting...")
                    last_size = (self.terminal_width, self.terminal_height)
                    time.sleep(0.1)
                
                # Convert frame
                ascii_frame, width, height = self.ultra_fast_color_convert(frame)
                
                # Center the output
                lines = ascii_frame.split('\n')
                vertical_padding = max(0, (self.terminal_height - height) // 2)
                output_lines = [" " * self.terminal_width] * vertical_padding
                
                for line in lines:
                    if len(output_lines) < self.terminal_height:
                        padded_line = line.center(self.terminal_width)
                        output_lines.append(padded_line)
                
                while len(output_lines) < self.terminal_height:
                    output_lines.append(" " * self.terminal_width)
                
                # Display
                os.system('cls')
                
                if show_info:
                    progress = (current_frame / total_frames) * 100
                    elapsed = time.time() - start_time
                    remaining = (total_frames - current_frame) / fps if fps > 0 else 0
                    
                    info = (f"Frame: {current_frame}/{total_frames} ({progress:.1f}%) | "
                           f"Time: {elapsed:.1f}s | Remaining: {remaining:.1f}s | "
                           f"Size: {width}x{height} | Color: {'ON' if self.color_mode else 'OFF'}")
                    print(info)
                    print("═" * self.terminal_width)
                
                print('\n'.join(output_lines))
                
                if show_info:
                    print("═" * self.terminal_width)
                    print("Controls: [Q]uit [F]info [T]color [P]ause [R]rescan")
                
                current_frame += 1
                
                # Input handling with timeout
                input_start = time.time()
                while time.time() - input_start < (1.0 / fps):
                    if msvcrt.kbhit():
                        key = msvcrt.getch().decode('utf-8').lower()
                        if key == 'q':
                            return True
                        elif key == 'f':
                            show_info = not show_info
                            break
                        elif key == 't':
                            self.color_mode = not self.color_mode
                            break
                        elif key == 'p':
                            print("\n" + " " * (self.terminal_width // 2 - 10) + "PAUSED - Press any key...")
                            msvcrt.getch()
                            break
                        elif key == 'r':
                            self.update_terminal_size()
                            break
                    time.sleep(0.01)
                
                # Maintain timing
                target_time = current_frame / fps
                actual_time = time.time() - start_time
                time.sleep(max(0.001, target_time - actual_time))
                
        except Exception as e:
            print(f"Playback error: {e}")
            return False
        finally:
            cap.release()
            total_time = time.time() - start_time
            actual_fps = current_frame / total_time if total_time > 0 else 0
            print(f"\nFinished! Average FPS: {actual_fps:.1f}")
        
        return True

class FullScreenColorImageDisplay:
    def __init__(self):
        self.chars = "@%#*+=-:. "
        self.precompute_char_mapping()
        self.get_terminal_size()
    
    def get_terminal_size(self):
        try:
            size = shutil.get_terminal_size()
            self.terminal_width = size.columns
            self.terminal_height = size.lines - 4
        except:
            self.terminal_width = 120
            self.terminal_height = 40
    
    def precompute_char_mapping(self):
        self.char_map = {}
        for i in range(256):
            scale = len(self.chars) - 1
            idx = min(int(i / 255 * scale), scale)
            self.char_map[i] = self.chars[idx]
    
    def display_image(self, image_path):
        """Display image in full screen color ASCII"""
        try:
            img = Image.open(image_path)
            img_rgb = img.convert('RGB')
            
            # Calculate dimensions to fill screen
            w, h = img.size
            aspect_ratio = h / w
            
            target_width = self.terminal_width
            target_height = int(target_width * aspect_ratio * 0.5)
            
            if target_height > self.terminal_height:
                target_height = self.terminal_height
                target_width = int(target_height / aspect_ratio / 0.5)
            
            # Resize image
            img_resized = img_rgb.resize((target_width, target_height))
            img_gray = img.convert('L').resize((target_width, target_height))
            
            # Convert to color ASCII
            pixels_rgb = np.array(img_resized)
            pixels_gray = np.array(img_gray)
            
            ascii_lines = []
            for y in range(target_height):
                line = ""
                last_color = None
                
                for x in range(target_width):
                    r, g, b = pixels_rgb[y, x]
                    brightness = pixels_gray[y, x]
                    char = self.char_map[brightness]
                    
                    current_color = (r, g, b)
                    if current_color != last_color:
                        color_code = f"\033[38;2;{r};{g};{b}m"
                        line += color_code
                        last_color = current_color
                    
                    line += char
                
                line += "\033[0m"
                ascii_lines.append(line)
            
            # Center the image
            vertical_padding = max(0, (self.terminal_height - target_height) // 2)
            horizontal_padding = max(0, (self.terminal_width - target_width) // 2)
            
            centered_lines = []
            for _ in range(vertical_padding):
                centered_lines.append(" " * self.terminal_width)
            
            for line in ascii_lines:
                centered_lines.append(" " * horizontal_padding + line)
            
            while len(centered_lines) < self.terminal_height:
                centered_lines.append(" " * self.terminal_width)
            
            # Display
            os.system('cls')
            print(f"Full Screen Color Image: {os.path.basename(image_path)}")
            print("═" * self.terminal_width)
            print('\n'.join(centered_lines))
            print("═" * self.terminal_width)
            print("Press any key to continue...")
            
            return True
            
        except Exception as e:
            print(f"Error displaying image: {e}")
            return False

class ParrotAnimation:
    def __init__(self):
        self.frames = self._create_parrot_frames()
    
    def _create_parrot_frames(self):
        return [
            r"""
   _
  ( \
   \ \
    \ \  
    / /                 
   / / 
  ( (  
   \ \
    ) )
   / / 
  / /  
 ( (   
  \_\  
            """,
            r"""
   _
  ( \
   \ \
    \ \  
    / /                 
   / / 
  ( (  
   \ \
    ) )
   / / 
  / /  
 ( (   
  \_\  
            """
        ]
    
    def animate(self):
        """Animate the parrot"""
        try:
            while True:
                for frame in self.frames:
                    os.system('cls' if os.name == 'nt' else 'clear')
                    print("\033[92m" + frame + "\033[0m")  # Green color
                    print("🎵 Party Parrot! Press Ctrl+C to stop 🎵")
                    time.sleep(0.3)
        except KeyboardInterrupt:
            print("\n🦜 Parrot has flown away! 🦜")
            return True
        except Exception as e:
            print(f"Error in parrot animation: {e}")
            return False