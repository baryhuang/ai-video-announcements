# Video Creator

A command-line Python application that allows you to create videos by combining multiple video clips and adding background music.

## Features

- Select multiple video files from a directory to concatenate
- Add background audio from either audio files or video files
- Automatic audio extraction from video files
- Automatic audio looping if the track is shorter than the video
- Volume reduction and fade out effect for background audio
- Simple command-line interface

## Requirements

- Python 3.7 or higher
- MoviePy
- NumPy

## Installation

1. Clone this repository or download the files
2. Install the required packages:
```bash
pip install -r requirements.txt
```

## Usage

1. Prepare your media files:
   - Put all your video files to be combined in a directory
   - Put your background audio sources (audio or video files) in another directory

2. Run the program with the required directory paths:
```bash
python video_creator.py --video-dir /path/to/videos --music-dir /path/to/audio_sources
```

Or use the short form:
```bash
python video_creator.py -v /path/to/videos -m /path/to/audio_sources
```

3. Follow the interactive prompts:
   - Select which videos to combine from the numbered list
   - Select which audio source to use (can be audio file or video file)
   - Specify the output video path

## Command-line Arguments

- `--video-dir`, `-v`: Directory containing video files (required)
- `--music-dir`, `-m`: Directory containing audio sources (audio or video files) (required)

## Supported Formats

- Videos: .mp4, .avi, .mov, .mkv, .webm
- Audio: .mp3, .wav
- Audio can also be extracted from any supported video format (including WebM)

## Notes

- The background audio volume will be reduced to 30% of the original
- A 3-second fadeout effect will be applied at the end of the video
- If the audio track is shorter than the final video, it will be looped
- The output video will be in MP4 format with H.264 encoding
- When using a video file as an audio source, only its audio track will be extracted

## Example Usage

```bash
$ python video_creator.py --video-dir ~/Documents/Waymaker日常播报素材2025/videos --music-dir ~/Documents/Waymaker日常播报素材2025/music -o ~/Documents/Waymaker日常播报素材2025/output/20250406.mp4

Available Videos:
1. video1.mp4
2. video2.webm
3. video3.mkv

Enter numbers separated by spaces (e.g., '1 3 4')
Select videos to combine (enter numbers): 1 2

Available Audio Files:
1. background1.mp3
2. background2.wav
3. soundtrack.mp3

Select background music (enter number): 3

Processing videos...
Loading video1.mp4...
Loading video2.webm...
Concatenating videos...
Processing background music...
Audio track is shorter than video - will loop it...
Adjusting background music volume and adding fadeout...
Writing final video to ~/Documents/Waymaker日常播报素材2025/output/20250406.mp4...
Video created successfully!