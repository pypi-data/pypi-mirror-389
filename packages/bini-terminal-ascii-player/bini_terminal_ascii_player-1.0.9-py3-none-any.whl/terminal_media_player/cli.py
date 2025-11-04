#!/usr/bin/env python3
"""
Terminal Media Player CLI
"""

import argparse
import sys
import os
from pathlib import Path

from .player import FullScreenColorVideoPlayer, AdaptiveFullScreenColorPlayer, FullScreenColorImageDisplay, WebcamASCIICapture

def find_video_files(directory="."):
    """Find all video files in directory"""
    video_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv'}
    video_files = []
    
    for file in os.listdir(directory):
        if any(file.lower().endswith(ext) for ext in video_extensions):
            video_files.append(file)
    
    return video_files

def find_image_files(directory="."):
    """Find all image files in directory"""
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.gif'}
    image_files = []
    
    for file in os.listdir(directory):
        if any(file.lower().endswith(ext) for ext in image_extensions):
            image_files.append(file)
    
    return image_files

def main():
    parser = argparse.ArgumentParser(
        description="BINI Terminal ASCII Player - Play videos, images, and webcam as ASCII art",
        epilog="""Examples:
  bini play video.mp4                 # Play video as ASCII art
  bini image photo.jpg               # Display image as ASCII art
  bini webcam                        # Start webcam ASCII capture (camera 0, 15 FPS)
  bini webcam --camera 1 --fps 10    # Use camera 1 at 10 FPS
  bini webcam --width 100            # Custom ASCII width (100 characters)
  bini webcam --camera 0 --fps 20 --width 120  # All options combined
  bini list                          # List available media files
  bini --version                     # Show version""",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Play command
    play_parser = subparsers.add_parser('play', help='Play a video file')
    play_parser.add_argument('file', help='Path to the video file or number from list')
    play_parser.add_argument('--adaptive', action='store_true', help='Use adaptive full screen mode')
    
    # Image command
    image_parser = subparsers.add_parser('image', help='Display an image file')
    image_parser.add_argument('file', help='Path to the image file or number from list')
    
    # Webcam command
    webcam_parser = subparsers.add_parser('webcam', 
        help='Start webcam ASCII capture',
        description="""Start real-time webcam ASCII capture.
        
Webcam Examples:
  bini webcam                        # Basic webcam (camera 0, 15 FPS)
  bini webcam --camera 1 --fps 10    # Specific camera and FPS
  bini webcam --width 100            # Custom ASCII width
  bini webcam --camera 0 --fps 20 --width 120  # All options combined
  
Webcam Controls During Operation:
  Q - Quit webcam
  C - Switch between cameras (0 and 1)
  F - Toggle FPS/info display
  S - Save current frame as image""",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    webcam_parser.add_argument('--camera', type=int, default=0, help='Camera index (default: 0)')
    webcam_parser.add_argument('--fps', type=int, default=15, help='Target FPS (default: 15)')
    webcam_parser.add_argument('--width', type=int, default=80, help='ASCII width (default: 80)')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List available media files')
    list_parser.add_argument('--videos', action='store_true', help='List only video files')
    list_parser.add_argument('--images', action='store_true', help='List only image files')
    
    # Version
    parser.add_argument('--version', action='store_true', help='Show version')
    
    args = parser.parse_args()
    
    if args.version:
        from . import __version__
        print(f"BINI Terminal ASCII Player v{__version__}")
        return
    
    if not args.command:
        # Show available media if no command
        video_files = find_video_files()
        image_files = find_image_files()
        
        print("BINI Terminal ASCII Player")
        print("\nAvailable video files:")
        if video_files:
            for i, video in enumerate(video_files, 1):
                print(f"  {i}. {video}")
        else:
            print("  No video files found")
            
        print("\nAvailable image files:")
        if image_files:
            for i, image in enumerate(image_files, 1):
                print(f"  {i}. {image}")
        else:
            print("  No image files found")
            
        print("\nCommands: play, image, webcam, list, --help")
        print("\nWebcam Examples:")
        print("  bini webcam                        # Basic webcam (camera 0, 15 FPS)")
        print("  bini webcam --camera 1 --fps 10    # Specific camera and FPS")
        print("  bini webcam --width 100            # Custom ASCII width")
        print("  bini webcam --camera 0 --fps 20 --width 120  # All options combined")
        return
    
    if args.command == 'play':
        video_arg = args.file
        video_path = None
        
        if video_arg.isdigit():
            video_files = find_video_files()
            index = int(video_arg) - 1
            if 0 <= index < len(video_files):
                video_path = video_files[index]
            else:
                print(f"Error: Invalid selection {video_arg}")
                return
        else:
            video_path = video_arg
        
        if not os.path.exists(video_path):
            print(f"Error: File '{video_path}' not found")
            print(f"Current directory: {os.getcwd()}")
            return
        
        if args.adaptive:
            player = AdaptiveFullScreenColorPlayer()
        else:
            player = FullScreenColorVideoPlayer()
            
        success = player.play_video(video_path)
        if not success:
            sys.exit(1)
    
    elif args.command == 'image':
        image_arg = args.file
        image_path = None
        
        if image_arg.isdigit():
            image_files = find_image_files()
            index = int(image_arg) - 1
            if 0 <= index < len(image_files):
                image_path = image_files[index]
            else:
                print(f"Error: Invalid selection {image_arg}")
                return
        else:
            image_path = image_arg
        
        if not os.path.exists(image_path):
            print(f"Error: File '{image_path}' not found")
            print(f"Current directory: {os.getcwd()}")
            return
        
        display = FullScreenColorImageDisplay()
        success = display.display_image(image_path)
        if success:
            import msvcrt
            msvcrt.getch()
    
    elif args.command == 'webcam':
        webcam = WebcamASCIICapture()
        success = webcam.start_webcam(
            camera_index=args.camera, 
            fps=args.fps
        )
        if not success:
            sys.exit(1)
    
    elif args.command == 'list':
        if args.videos or not (args.videos or args.images):
            video_files = find_video_files()
            print("Video files in current directory:")
            if video_files:
                for i, video in enumerate(video_files, 1):
                    print(f"  {i}. {video}")
            else:
                print("  No video files found")
            print()
        
        if args.images or not (args.videos or args.images):
            image_files = find_image_files()
            print("Image files in current directory:")
            if image_files:
                for i, image in enumerate(image_files, 1):
                    print(f"  {i}. {image}")
            else:
                print("  No image files found")

if __name__ == '__main__':
    main()