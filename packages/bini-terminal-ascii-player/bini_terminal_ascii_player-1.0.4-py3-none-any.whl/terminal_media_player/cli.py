#!/usr/bin/env python3
"""
Terminal Media Player CLI
"""

import argparse
import sys
import os
from pathlib import Path

from .player import FullScreenColorVideoPlayer, AdaptiveFullScreenColorPlayer, FullScreenColorImageDisplay, ParrotAnimation

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
        description="Terminal Media Player - Play videos and images as ASCII art",
        epilog="Examples:\n  bini play video.mp4\n  bini image photo.jpg\n  bini parrot\n  bini list",
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
    
    # List command
    list_parser = subparsers.add_parser('list', help='List available media files')
    list_parser.add_argument('--videos', action='store_true', help='List only video files')
    list_parser.add_argument('--images', action='store_true', help='List only image files')
    
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
        # Show available media if no command
        video_files = find_video_files()
        image_files = find_image_files()
        
        print("Terminal Media Player")
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
            
        print("\nCommands: play, image, list, parrot, --help")
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
    
    elif args.command == 'parrot':
        parrot = ParrotAnimation()
        parrot.animate()

if __name__ == '__main__':
    main()