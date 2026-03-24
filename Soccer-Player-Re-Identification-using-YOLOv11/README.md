# Soccer Player Re-Identification with YOLOv11 and Deep SORT

This project performs player detection and re-identification in a 15-second soccer video using a fine-tuned YOLOv11 model and Deep SORT tracker enhanced with the `osnet_ain_x1_0` appearance model from TorchreID.

Players are tracked even when they leave and re-enter the frame, and the same IDs are consistently assigned throughout the clip.

---

## 🧩 Features

- Uses **YOLOv11** for real-time object detection (players, ball, etc.)
- Integrates **Deep SORT** for multi-object tracking with re-identification
- Embeds appearance features using **TorchreID (osnet_ain_x1_0)**
- Filters out non-player detections and maintains track ID consistency
- Outputs annotated video with tracked player IDs

---

## 🔧 Setup Instructions

### 1. Clone the repository (or place the scripts)

Ensure `soccer_player_reidentify.py`, `best.pt` (YOLOv11 model), and your video file (e.g., `15sec_input_720p.mp4`) are in the same directory.

### 2. Create a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
```

### 3. Install required dependencies

```bash
pip install -U pip
pip install ultralytics
pip install opencv-python
pip install torch torchvision torchaudio
pip install torchreid
pip install deep_sort_realtime
```

**Note:** TorchReID may require specific PyTorch versions. You can install it manually from source if needed:

```bash
pip uninstall torchreid
git clone https://github.com/KaiyangZhou/deep-person-reid.git
cd deep-person-reid
pip install -e .
```

---

## 🚀 Running the Code

Make sure the following files are in your working directory:

<ul>
	<li>soccer_player_reidentify.py — Main script</li>
    <li>best.pt — Trained YOLOv11 weights (fine-tuned on player & ball classes)</li>
	<li>15sec_input_720p.mp4 — Input video</li>
</ul>

Then, run the script:

```bash
python soccer_player_reidentify.py
```

This will:

<ul>
	<li>Open the video</li>
	<li>Detect players using YOLOv11</li>
	<li>Track each player using Deep SORT</li>
	<li>Assign persistent IDs</li>
	<li>Write an output video file named output.mp4</li>
</ul>

You can view the results in real-time or press **q** to stop early.

---

## 🖥️ Output

<ul>
	<li>output.mp4: A new video file with bounding boxes and consistent Player {ID} labels.</li>
	<li>Players that re-enter the frame are given their original ID (re-identification).</li>
	<li>Only players are visualized (referees, ball, or other classes are filtered out).</li>
</ul>

---

## ⚙️ Environment Notes

<ul>
	<li>Python 3.8–3.11 recommended</li>
	<li>GPU support (CUDA) is optional but recommended for performance</li>
	<li>Tested on macOS and Linux; Windows supported with slight path adjustments</li>
</ul>

---

## 📬 Contact

For questions or improvements, feel free to reach out.