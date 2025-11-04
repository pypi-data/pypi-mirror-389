class AdaptiveFullScreenColorPlayer:
    """Adaptive full screen player that handles terminal resizing"""
    
    def __init__(self, color_mode=True):
        self.color_mode = color_mode
        self.chars = "@%#*+=-:. "
        self.playing = False
        self.precompute_char_mapping()
        self.update_terminal_size()
    
    def precompute_char_mapping(self):
        self.char_map = {}
        for i in range(256):
            scale = len(self.chars) - 1
            idx = min(int(i / 255 * scale), scale)
            self.char_map[i] = self.chars[idx]
    
    def update_terminal_size(self):
        try:
            size = shutil.get_terminal_size()
            self.terminal_width = size.columns
            self.terminal_height = size.lines - 4
        except:
            self.terminal_width = 120
            self.terminal_height = 40
    
    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def rgb_to_ansi(self, r, g, b):
        if not self.color_mode:
            return ""
        return f"\033[38;2;{r};{g};{b}m"
    
    def reset_color(self):
        return "\033[0m" if self.color_mode else ""
    
    def play_video(self, video_path):
        """Play video with adaptive sizing"""
        self.update_terminal_size()
        
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            print(f"Error: Could not open video {video_path}")
            return False
        
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        original_fps = cap.get(cv2.CAP_PROP_FPS)
        frame_delay = 1.0 / original_fps if original_fps > 0 else 1.0 / 24
        
        self.playing = True
        current_frame = 0
        start_time = time.time()
        last_size = (self.terminal_width, self.terminal_height)
        
        try:
            while self.playing and current_frame < total_frames:
                # Check for terminal resize
                current_size = (self.terminal_width, self.terminal_height)
                self.update_terminal_size()
                if current_size != last_size:
                    print("Terminal resized! Adapting...")
                    last_size = current_size
                
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Convert frame
                ascii_frame, width, height = self.frame_to_ascii(frame)
                centered_frame = self.center_output(ascii_frame, width, height)
                
                self.clear_screen()
                
                progress = (current_frame / total_frames) * 100
                elapsed = time.time() - start_time
                
                print(f"Frame: {current_frame}/{total_frames} ({progress:.1f}%) | "
                      f"Time: {elapsed:.1f}s | Size: {width}x{height}")
                print("═" * self.terminal_width)
                print(centered_frame)
                print("═" * self.terminal_width)
                print("Controls: [Q]uit [P]ause")
                
                current_frame += 1
                
                if msvcrt.kbhit():
                    key = msvcrt.getch().decode('utf-8').lower()
                    if key == 'q':
                        break
                    elif key == 'p':
                        print("\nPAUSED - Press any key to continue...")
                        msvcrt.getch()
                
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
        
        return True
    
    def frame_to_ascii(self, frame):
        """Convert frame to ASCII art"""
        try:
            original_height, original_width = frame.shape[:2]
            aspect_ratio = original_height / original_width
            
            target_width = self.terminal_width
            target_height = int(target_width * aspect_ratio * 0.5)
            
            if target_height > self.terminal_height:
                target_height = self.terminal_height
                target_width = int(target_height / aspect_ratio / 0.5)
            
            frame_resized = cv2.resize(frame, (target_width, target_height))
            frame_rgb = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
            frame_gray = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2GRAY)
            
            ascii_lines = []
            for y in range(target_height):
                line = ""
                last_color = None
                
                for x in range(target_width):
                    brightness = frame_gray[y, x]
                    char = self.char_map[brightness]
                    r, g, b = frame_rgb[y, x]
                    
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
            return f"Error: {e}", 0, 0
    
    def center_output(self, ascii_art, content_width, content_height):
        """Center the ASCII art on screen"""
        lines = ascii_art.split('\n')
        vertical_padding = max(0, (self.terminal_height - content_height) // 2)
        horizontal_padding = max(0, (self.terminal_width - content_width) // 2)
        
        centered_lines = []
        for _ in range(vertical_padding):
            centered_lines.append(" " * self.terminal_width)
        
        for line in lines:
            padded_line = " " * horizontal_padding + line
            centered_lines.append(padded_line)
        
        remaining_lines = self.terminal_height - len(centered_lines)
        for _ in range(remaining_lines):
            centered_lines.append(" " * self.terminal_width)
        
        return '\n'.join(centered_lines)