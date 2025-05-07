from django.conf import settings
import os
import subprocess

def convert_video_to_resolution(source_path, resolution):
    """
    Converts a video file to the specified resolution (e.g., 360p, 720p).
    The converted file is saved in a resolution-specific folder under MEDIA_ROOT.
    Uses ffmpeg to handle the conversion.
    """
    resolutions = {
        120: (210, 120),
        360: (640, 360),
        720: (1280, 720),
        1080: (1920, 1080),
    }
    width, height = resolutions[resolution]
    base_name = os.path.basename(source_path).split('.')[0]
    folder = os.path.join(settings.MEDIA_ROOT, f"videos/{resolution}p")
    os.makedirs(folder, exist_ok=True)
    target_path = os.path.join(folder, f"{base_name}_{resolution}p.mp4")
    command = [
        "ffmpeg", "-i", source_path,
        "-vf", f"scale={width}:{height}",
        "-c:v", "libx264", "-preset", "slow", "-crf", "22",
        target_path
    ]
    subprocess.run(command, stdin=subprocess.DEVNULL, check=True)
    return target_path

def generate_thumbnail(video_path, output_path, time='00:00:05'):
    """
    Generates a thumbnail image from a video at a specific time position.
    The thumbnail is saved to the given output path.
    """
    command = [
        'ffmpeg',
        '-ss', time,
        '-i', video_path,
        '-frames:v', '1',
        '-q:v', '2',  # Quality from 1 (best) to 31 (worst)
        output_path
    ]

    subprocess.run(command, stdin=subprocess.DEVNULL, check=True)
    return output_path

def get_video_duration(video_path):
    """
    Gets the duration (in seconds) of a video file using ffprobe.
    """
    command = [
        'ffprobe',
        '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        video_path
    ]
    result = subprocess.run(command, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    duration = float(result.stdout.strip())
    return duration

def cut_video_for_trailer(video_path, output_path, duration=7):
    """
    Cuts a short trailer from a video with the specified duration in seconds.
    The trailer is saved to the given output path.
    """
    command = [
        'ffmpeg',
        '-i', video_path,
        '-t', str(duration),
        '-c:v', 'libx264',
        '-preset', 'slow',
        '-crf', '22',
        output_path
    ]

    subprocess.run(command, stdin=subprocess.DEVNULL, check=True)
    return output_path

