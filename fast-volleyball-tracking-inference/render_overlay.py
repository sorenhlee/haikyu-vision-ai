import cv2
import csv
import subprocess
import os
import argparse
import numpy as np
from pathlib import Path
from collections import deque

FFMPEG = r"C:\Users\hyuns\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1-full_build\bin\ffmpeg.exe"

def render(video_path, csv_path, output_dir, trail_length=15):
    os.makedirs(output_dir, exist_ok=True)
    video_name = Path(video_path).stem

    detections = {}
    with open(csv_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            frame = int(row['Frame'])
            visible = row.get('Visibility', row.get('Visible', '0'))
            if visible == '1':
                detections[frame] = (int(row['X']), int(row['Y']))

    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    out_path = os.path.join(output_dir, f"{video_name}_overlay.mp4")

    # Pipe raw frames to ffmpeg with NVENC hardware encoding
    ffmpeg_cmd = [
        FFMPEG, "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-s", "1920x1080",
        "-pix_fmt", "bgr24",
        "-r", "125",
        "-i", "pipe:0",
        "-c:v", "h264_nvenc",
        "-preset", "fast",
        "-pix_fmt", "yuv420p",
        out_path
    ]

    pipe = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE)

    trail = deque(maxlen=trail_length)
    frame_idx = 0

    print(f"Rendering {total} frames with NVENC...")
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        data = detections.get(frame_idx)
        if data:
            trail.append(data)

        # Draw trail
        for i, (tx, ty) in enumerate(trail):
            radius = max(3, int(8 * (i + 1) / len(trail)))
            cv2.circle(frame, (tx, ty), radius, (0, 255, 255), -1)

        # Draw current ball
        if data:
            x, y = data
            cv2.circle(frame, (x, y), 10, (0, 255, 255), -1)
            cv2.circle(frame, (x, y), 14, (0, 165, 255), 2)

        pipe.stdin.write(frame.tobytes())
        frame_idx += 1

        if frame_idx % 1000 == 0:
            print(f"  {frame_idx/total*100:.1f}%")

    cap.release()
    pipe.stdin.close()
    pipe.wait()
    print(f"\nDone! Output: {out_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--video_path", required=True)
    parser.add_argument("--csv_path", required=True)
    parser.add_argument("--output_dir", default="output_overlay")
    parser.add_argument("--trail_length", type=int, default=15)
    args = parser.parse_args()
    render(args.video_path, args.csv_path, args.output_dir, args.trail_length)
