import csv
import subprocess
import os
import argparse

FFMPEG = r"C:\Users\hyuns\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-8.1-full_build\bin\ffmpeg.exe"

def render(video_path, csv_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)

    # Read CSV
    detections = {}
    with open(csv_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            frame = int(row['Frame'])
            visible = row.get('Visibility', row.get('Visible', '0'))
            if visible == '1':
                detections[frame] = (int(row['X']), int(row['Y']))

    print(f"Loaded {len(detections)} detections")

    # Write filter script to file
    filter_path = os.path.join(output_dir, "filter.txt")
    with open(filter_path, 'w') as f:
        filters = []
        for frame, (x, y) in sorted(detections.items()):
            filters.append(
                f"drawcircle=x={x}:y={y}:r=12:color=yellow:t=3:enable='between(n,{frame},{frame+2})'"
            )
        f.write(",".join(filters))

    out_path = os.path.join(output_dir, "overlay_ffmpeg.mp4")
    print(f"Rendering {len(detections)} detections with NVIDIA encoder...")

    subprocess.run([
        FFMPEG, "-y",
        "-i", video_path,
        "-vf", f"filter_script={filter_path}",
        "-c:v", "h264_nvenc",
        "-preset", "fast",
        out_path
    ])

    print(f"Done! Output: {out_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--video_path", required=True)
    parser.add_argument("--csv_path", required=True)
    parser.add_argument("--output_dir", default="output_overlay")
    args = parser.parse_args()
    render(args.video_path, args.csv_path, args.output_dir)