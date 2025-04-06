import os
import sys
import argparse
from pathlib import Path
from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips, CompositeAudioClip
import numpy as np

def debug_print(msg: str, obj=None):
    """Print debug information."""
    print(f"\nDEBUG: {msg}")
    if obj is not None:
        print(f"Type: {type(obj)}")
        print(f"Value: {obj}")
        if hasattr(obj, 'duration'):
            print(f"Duration: {obj.duration}")
        if hasattr(obj, 'fps'):
            print(f"FPS: {obj.fps}")
        if hasattr(obj, 'size'):
            print(f"Size: {obj.size}")

def list_media_files(directory: str, extensions: list) -> list:
    """List all media files with given extensions in a directory."""
    files = []
    for ext in extensions:
        files.extend(Path(directory).glob(f"*.{ext}"))
    return sorted(files)

def print_numbered_list(items: list, title: str):
    """Print a numbered list of items with a title."""
    print(f"\n{title}:")
    for idx, item in enumerate(items, 1):
        print(f"{idx}. {item.name}")

def get_user_selection(items: list, prompt: str, multiple: bool = False) -> list:
    """Get user selection from a list of items."""
    while True:
        try:
            if multiple:
                print("\nEnter numbers separated by spaces (e.g., '1 3 4')")
                selections = input(prompt).strip().split()
                indices = [int(x) - 1 for x in selections]
                if all(0 <= i < len(items) for i in indices):
                    return [items[i] for i in indices]
            else:
                selection = int(input(prompt)) - 1
                if 0 <= selection < len(items):
                    return [items[selection]]
            
        except (ValueError, IndexError):
            print("Invalid selection. Please try again.")

def get_audio_from_file(file_path: Path) -> AudioFileClip:
    """Load an audio file."""
    try:
        debug_print(f"Loading audio file: {file_path}")
        audio = AudioFileClip(str(file_path))
        debug_print("Audio loaded", audio)
        return audio
    except Exception as e:
        debug_print(f"Error loading audio: {str(e)}")
        raise ValueError(f"Failed to load audio from {file_path}: {str(e)}")

def create_video(video_paths: list, music_path: Path, output_path: str):
    """Create final video with background music while preserving original audio."""
    video_clips = []
    background_audio = None
    final_video = None
    
    try:
        print("\nProcessing videos...")
        
        # Load videos and ensure they're all valid
        total_duration = 0
        base_size = None
        base_fps = None
        
        # First pass: analyze audio levels across all videos
        print("\nAnalyzing audio levels...")
        max_volume = 0
        for video_path in video_paths:
            try:
                clip = VideoFileClip(str(video_path))
                if clip.audio is not None:
                    # Get max volume for this clip
                    audio_array = clip.audio.to_soundarray()
                    clip_max_volume = np.abs(audio_array).max()
                    max_volume = max(max_volume, clip_max_volume)
                clip.close()
            except Exception as e:
                debug_print(f"Error analyzing audio: {str(e)}")
                raise ValueError(f"Failed to analyze audio in {video_path.name}: {str(e)}")

        # Second pass: load and normalize videos
        for video_path in video_paths:
            print(f"Loading {video_path.name}...")
            try:
                debug_print(f"Loading video file: {video_path}")
                clip = VideoFileClip(str(video_path))
                debug_print("Video clip loaded", clip)
                
                if clip.duration == 0:
                    debug_print("Video has zero duration")
                    raise ValueError("Video has zero duration")
                
                # Normalize audio if present
                if clip.audio is not None and max_volume > 0:
                    debug_print("Normalizing audio track")
                    audio_array = clip.audio.to_soundarray()
                    clip_max_volume = np.abs(audio_array).max()
                    if clip_max_volume > 0:
                        # Normalize to match the loudest clip
                        volume_factor = max_volume / clip_max_volume
                        clip = clip.set_audio(clip.audio.volumex(volume_factor))
                        debug_print(f"Applied volume factor: {volume_factor}")
                
                # Ensure all videos have the same size and fps
                if base_size is None:
                    base_size = clip.size
                    base_fps = clip.fps
                else:
                    if clip.size != base_size:
                        debug_print(f"Resizing video from {clip.size} to {base_size}")
                        clip = clip.resize(width=base_size[0], height=base_size[1])
                    if clip.fps != base_fps:
                        debug_print(f"Adjusting FPS from {clip.fps} to {base_fps}")
                        clip = clip.set_fps(base_fps)
                
                video_clips.append(clip)
                total_duration += clip.duration
                debug_print(f"Total duration so far: {total_duration}")
            except Exception as e:
                debug_print(f"Error loading video: {str(e)}")
                raise ValueError(f"Failed to load video {video_path.name}: {str(e)}")
        
        if not video_clips:
            debug_print("No valid video clips to process")
            raise ValueError("No valid video clips to process")
        
        print("\nConcatenating videos...")
        debug_print(f"Concatenating {len(video_clips)} video clips")
        try:
            final_video = concatenate_videoclips(video_clips, method="compose")
            debug_print("Concatenation complete", final_video)
        except Exception as e:
            debug_print(f"Error during concatenation: {str(e)}")
            raise ValueError(f"Failed to concatenate videos: {str(e)}")
        
        print("Processing background music...")
        # Load and process background music
        try:
            background_audio = get_audio_from_file(music_path)
            if background_audio is None:
                debug_print("Audio loading returned None")
                raise ValueError("Audio loading returned None")
            
            debug_print("Background audio loaded successfully", background_audio)
            
            # Loop audio if needed
            if background_audio.duration < final_video.duration:
                debug_print(f"Audio duration ({background_audio.duration}) < Video duration ({final_video.duration})")
                print("Background track is shorter than video - will loop it...")
                num_loops = int(np.ceil(final_video.duration / background_audio.duration))
                debug_print(f"Will loop audio {num_loops} times")
                background_audio = concatenate_videoclips([background_audio] * num_loops)
                debug_print("Audio looping complete", background_audio)
            
            # Trim audio to match video length
            debug_print(f"Trimming audio to {final_video.duration} seconds")
            background_audio = background_audio.subclip(0, final_video.duration)
            debug_print("Audio trimming complete", background_audio)
            
            # Lower background music volume and add fadeout
            print("Adjusting background music volume and adding fadeout...")
            debug_print("Applying volume reduction")
            background_audio = background_audio.volumex(0.3)  # Reduce volume to 30%
            debug_print("Applying fadeout")
            background_audio = background_audio.audio_fadeout(3)  # 3 second fadeout
            debug_print("Audio processing complete", background_audio)
            
            # Combine original audio with background music
            debug_print("Combining original audio with background music")
            if final_video.audio is not None:
                final_audio = CompositeAudioClip([final_video.audio, background_audio])
                final_video = final_video.set_audio(final_audio)
            else:
                final_video = final_video.set_audio(background_audio)
            debug_print("Audio tracks combined", final_video)
        except Exception as e:
            debug_print(f"Background audio processing error: {str(e)}")
            print(f"\nWarning: Failed to process background audio: {str(e)}")
            print("Continuing with original audio only...")
        
        if final_video is None:
            raise ValueError("Failed to create final video")
        
        print(f"\nWriting final video to {output_path}...")
        debug_print("Starting video write process")
        
        # Ensure the video has valid properties before writing
        if not hasattr(final_video, 'fps') or final_video.fps is None:
            debug_print("Setting default FPS to 30")
            final_video = final_video.set_fps(30)
        
        if not hasattr(final_video, 'duration') or final_video.duration == 0:
            raise ValueError("Final video has invalid duration")
        
        final_video.write_videofile(
            output_path,
            codec='libx264',
            audio_codec='aac',
            temp_audiofile='temp-audio.m4a',
            remove_temp=True,
            fps=final_video.fps
        )
        
        print("\nVideo created successfully!")
        
    except Exception as e:
        debug_print(f"Fatal error: {str(e)}")
        print(f"\nError: {str(e)}")
        sys.exit(1)
    
    finally:
        # Clean up
        print("\nCleaning up resources...")
        try:
            if final_video:
                debug_print("Closing final video")
                final_video.close()
            for clip in video_clips:
                debug_print(f"Closing video clip")
                clip.close()
            if background_audio:
                debug_print("Closing background audio")
                background_audio.close()
        except Exception as e:
            debug_print(f"Cleanup error: {str(e)}")
            print(f"Warning: Cleanup encountered an error: {str(e)}")

def main():
    # Set up command line argument parser
    parser = argparse.ArgumentParser(description='Create a video by combining clips and adding background music.')
    parser.add_argument('--video-dir', '-v', required=True, help='Directory containing video files')
    parser.add_argument('--music-dir', '-m', required=True, help='Directory containing audio files (mp3, wav)')
    parser.add_argument('--output', '-o', help='Output video path (optional, will prompt if not provided)')
    
    args = parser.parse_args()
    
    # Validate directories
    if not os.path.isdir(args.video_dir):
        print(f"\nError: Video directory '{args.video_dir}' does not exist!")
        sys.exit(1)
        
    if not os.path.isdir(args.music_dir):
        print(f"\nError: Music directory '{args.music_dir}' does not exist!")
        sys.exit(1)

    # List available videos
    video_files = list_media_files(args.video_dir, ["mp4", "avi", "mov", "mkv", "webm"])
    if not video_files:
        print("\nNo video files found in the specified directory!")
        sys.exit(1)
    
    print_numbered_list(video_files, "Available Videos")
    selected_videos = get_user_selection(
        video_files,
        "\nSelect videos to combine (enter numbers): ",
        multiple=True
    )

    # List available audio files
    music_files = list_media_files(args.music_dir, ["mp3", "wav"])
    if not music_files:
        print("\nNo audio files found in the specified directory!")
        sys.exit(1)
    
    print_numbered_list(music_files, "Available Audio Files")
    selected_music = get_user_selection(
        music_files,
        "\nSelect background music (enter number): ",
        multiple=False
    )[0]

    # Get output path
    output_path = args.output
    while not output_path:
        output_path = input("\nEnter the output video path (e.g., output.mp4): ").strip()
        if not output_path:
            continue
        output_dir = os.path.dirname(output_path) or "."
        if not os.path.isdir(output_dir):
            print("Invalid output directory. Please try again.")
            output_path = None

    # Create the video
    create_video(selected_videos, selected_music, output_path)

if __name__ == "__main__":
    main() 