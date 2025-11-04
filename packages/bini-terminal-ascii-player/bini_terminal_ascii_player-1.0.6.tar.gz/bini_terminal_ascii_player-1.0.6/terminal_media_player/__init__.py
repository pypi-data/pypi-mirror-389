"""Terminal Media Player - Play videos and images as ASCII art in your terminal"""
__version__ = "1.0.0"
__author__ = "scarlieee02"

from .player import FullScreenColorVideoPlayer, AdaptiveFullScreenColorPlayer, FullScreenColorImageDisplay, ParrotAnimation
from .cli import main

__all__ = [
    'FullScreenColorVideoPlayer', 
    'AdaptiveFullScreenColorPlayer', 
    'FullScreenColorImageDisplay', 
    'ParrotAnimation', 
    'main'
]