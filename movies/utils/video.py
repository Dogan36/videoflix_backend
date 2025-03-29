from django.conf import settings
import os
import subprocess

def convert_video_to_resolution(source_path, resolution):
    resolutions = {
        120: (160, 120),
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

    subprocess.run(command, check=True)
    print(f"✅ {resolution}p-Version gespeichert unter: {target_path}")
    return target_path