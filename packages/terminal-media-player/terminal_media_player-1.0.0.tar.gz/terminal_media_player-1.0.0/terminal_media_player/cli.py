#!/usr/bin/env python3
"""
Terminal Media Player CLI
Usage:
  tmp play <file>
  tmp parrot
  tmp --help
  tmp --version
"""

import argparse
import sys
import os
from pathlib import Path

from .player import FullScreenColorVideoPlayer, ParrotAnimation

def main():
    parser = argparse.ArgumentParser(
        description="Terminal Media Player - Play videos and images as ASCII art",
        epilog="Examples:\n  tmp play video.mp4\n  tmp parrot",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Play command
    play_parser = subparsers.add_parser('play', help='Play a video or image file')
    play_parser.add_argument('file', help='Path to the video or image file')
    
    # Parrot command
    subparsers.add_parser('parrot', help='Show animated parrot (like curl parrot.live)')
    
    # Version
    parser.add_argument('--version', action='store_true', help='Show version')
    
    args = parser.parse_args()
    
    if args.version:
        from . import __version__
        print(f"Terminal Media Player v{__version__}")
        return
    
    if not args.command:
        parser.print_help()
        return
    
    if args.command == 'play':
        file_path = Path(args.file)
        if not file_path.exists():
            print(f"Error: File '{args.file}' not found")
            sys.exit(1)
        
        # Check file type
        video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv'}
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.gif'}
        
        if file_path.suffix.lower() in video_extensions:
            player = FullScreenColorVideoPlayer()
            success = player.play_video(str(file_path))
            if not success:
                sys.exit(1)
        elif file_path.suffix.lower() in image_extensions:
            # For images, we'll create a simple slideshow
            from PIL import Image
            import numpy as np
            
            try:
                display = FullScreenColorVideoPlayer()
                img = Image.open(file_path)
                # Convert image to OpenCV format
                img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
                
                # Display image until keypress
                ascii_frame, width, height = display.frame_to_fullscreen_color_ascii(img_cv)
                centered_frame = display.center_output(ascii_frame, width, height)
                
                display.clear_screen()
                print(f"Image: {file_path.name}")
                print("═" * display.terminal_width)
                print(centered_frame)
                print("═" * display.terminal_width)
                print("Press any key to continue...")
                
                import msvcrt
                msvcrt.getch()
                
            except Exception as e:
                print(f"Error displaying image: {e}")
                sys.exit(1)
        else:
            print(f"Error: Unsupported file format '{file_path.suffix}'")
            sys.exit(1)
    
    elif args.command == 'parrot':
        parrot = ParrotAnimation()
        parrot.animate()

if __name__ == '__main__':
    main()