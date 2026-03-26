import google.generativeai as genai
import base64, json, os, time
from pathlib import Path

genai.configure(api_key="AIzaSyAYBuiA5m0y5AxeHNORdGfICbWPZuL1VX4")
model = genai.GenerativeModel("gemini-2.5-flash")

FRAMES_DIR = r"C:\Users\hyuns\Documents\1. Projects\26 Q1 Vibe-Coding Projects\Haikyu Vision\video-files\frames"
OUTPUT_FILE = r"C:\Users\hyuns\Documents\1. Projects\26 Q1 Vibe-Coding Projects\Haikyu Vision\video-files\segments.json"
SECONDS_PER_FRAME = 30

def encode_image(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

def scan_frames_batch(frame_paths, start_frame_index):
    images = []
    timestamps = []
    for i, path in enumerate(frame_paths):
        images.append({
            "mime_type": "image/jpeg",
            "data": encode_image(path)
        })
        timestamp_sec = (start_frame_index + i) * SECONDS_PER_FRAME
        timestamps.append(timestamp_sec)

    timestamp_list = ", ".join([f"frame {i}: {t}s ({t//60}:{t%60:02d})" 
                                 for i, t in enumerate(timestamps)])
    
    prompt = f"""You are analyzing frames from a volleyball practice video.
Each frame is sampled 30 seconds apart.
Frame timestamps: {timestamp_list}

For each frame, determine if it shows an active 6v6 volleyball practice session 
(both sides of court populated with ~6 players each in game-like play).

Respond ONLY with a valid JSON array, no markdown, no explanation:
[
  {{"frame_index": 0, "timestamp_sec": 0, "is_6v6": false, "reason": "warmup drills"}},
  {{"frame_index": 1, "timestamp_sec": 30, "is_6v6": true, "reason": "full court 6v6 play"}}
]

Set is_6v6 to false for: warmup, drills, small groups, empty court, breaks, huddles.
Set is_6v6 to true only for: both sides of court fully populated, live game-like play."""

    response = model.generate_content([prompt] + images)
    text = response.text.strip().replace("```json", "").replace("```", "").strip()
    return json.loads(text)

def find_6v6_segments(results):
    segments = []
    in_segment = False
    start = None
    
    for r in results:
        if r["is_6v6"] and not in_segment:
            in_segment = True
            start = max(0, r["timestamp_sec"] - 30)  # small buffer before
        elif not r["is_6v6"] and in_segment:
            in_segment = False
            segments.append({
                "start_sec": start,
                "end_sec": r["timestamp_sec"],
                "start_fmt": f"{start//60}:{start%60:02d}",
                "end_fmt": f"{r['timestamp_sec']//60}:{r['timestamp_sec']%60:02d}"
            })
    
    if in_segment:  # handle segment that goes to end of video
        last_ts = results[-1]["timestamp_sec"]
        segments.append({
            "start_sec": start,
            "end_sec": last_ts,
            "start_fmt": f"{start//60}:{start%60:02d}",
            "end_fmt": f"{last_ts//60}:{last_ts%60:02d}"
        })
    
    return segments

# Main
frame_files = sorted(Path(FRAMES_DIR).glob("frame_*.jpg"))
all_results = []
BATCH_SIZE = 10

print(f"Scanning {len(frame_files)} frames in batches of {BATCH_SIZE}...")

for i in range(0, len(frame_files), BATCH_SIZE):
    batch = frame_files[i:i + BATCH_SIZE]
    print(f"Processing frames {i+1}-{min(i+BATCH_SIZE, len(frame_files))}...")
    try:
        results = scan_frames_batch(batch, i)
        all_results.extend(results)
        time.sleep(2)  # avoid rate limiting
    except Exception as e:
        print(f"Error on batch {i}: {e}")
        print("Waiting 10 seconds and retrying...")
        time.sleep(10)
        try:
            results = scan_frames_batch(batch, i)
            all_results.extend(results)
        except Exception as e2:
            print(f"Batch {i} failed twice, skipping: {e2}")

segments = find_6v6_segments(all_results)

output = {
    "video": "2025.11.10-06.20-709201.mp4",
    "total_frames_scanned": len(all_results),
    "6v6_segments": segments,
    "raw_results": all_results
}

with open(OUTPUT_FILE, "w") as f:
    json.dump(output, f, indent=2)

print(f"\nDone! Found {len(segments)} 6v6 segments:")
for s in segments:
    print(f"  {s['start_fmt']} → {s['end_fmt']}")
print(f"\nFull results saved to: {OUTPUT_FILE}")