# Bini Terminal ASCII Player

Play videos and images as full screen color ASCII art directly in your terminal!

## Installation

```bash
pip install bini-terminal-ascii-player
```

## Usage

### Play a video:
```bash
tmp play video.mp4
```

### Play an image:
```bash
tmp play image.jpg
```

### Show animated parrot (like curl parrot.live):
```bash
tmp parrot
```

### Get help:
```bash
tmp --help
```

## Features

- 🎨 Full color ASCII art based on original media colors
- 📺 Full screen terminal support
- ⚡ Real-time video playback
- 🖼️ Image display support
- 🦜 Fun parrot animation
- 🎮 Interactive controls during playback

## Controls During Playback

- `Q` - Quit
- `F` - Toggle info display
- `P` - Pause

## Supported Formats

- **Video**: MP4, AVI, MOV, MKV, WMV, FLV
- **Image**: JPG, JPEG, PNG, BMP, GIF

## Requirements

- Python 3.7+
- OpenCV
- Pillow
- NumPy

## License

MIT