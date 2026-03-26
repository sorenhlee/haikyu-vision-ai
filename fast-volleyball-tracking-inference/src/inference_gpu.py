import cv2
import numpy as np
import onnxruntime as ort
import csv
import os
import argparse
from pathlib import Path
from collections import deque
import threading
import queue

def preprocess_frames(frames, input_h=288, input_w=512):
    processed = []
    for frame in frames:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        resized = cv2.resize(gray, (input_w, input_h))
        normalized = resized.astype(np.float32) / 255.0
        processed.append(normalized)
    return np.stack(processed, axis=0)[np.newaxis, ...]

def postprocess_heatmap(output, orig_w, orig_h, threshold=0.5):
    heatmap = output[0]
    if heatmap.ndim == 3:
        heatmap = heatmap[0]
    if heatmap.max() < threshold:
        return None, 0.0
    idx = np.argmax(heatmap)
    hy, hx = np.unravel_index(idx, heatmap.shape)
    confidence = float(heatmap[hy, hx])
    x = int(hx * orig_w / heatmap.shape[1])
    y = int(hy * orig_h / heatmap.shape[0])
    return (x, y), confidence

def frame_reader(video_path, frame_queue, seq_len=9):
    """Read frames in background thread."""
    cap = cv2.VideoCapture(video_path)
    buffer = deque(maxlen=seq_len)
    frame_idx = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        buffer.append(frame.copy())
        if len(buffer) == seq_len:
            frame_queue.put((frame_idx, frame.copy(), list(buffer)))
        frame_idx += 1
    cap.release()
    frame_queue.put(None)  # signal done

def run_inference(video_path, model_path, output_dir, threshold=0.5, seq_len=9, batch_size=8):
    os.makedirs(output_dir, exist_ok=True)
    video_name = Path(video_path).stem

    # Load model with CUDA
    sess_options = ort.SessionOptions()
    sess_options.intra_op_num_threads = 4
    providers = [
        ('CUDAExecutionProvider', {
            'device_id': 0,
            'arena_extend_strategy': 'kNextPowerOfTwo',
            'gpu_mem_limit': 4 * 1024 * 1024 * 1024,  # 4GB
            'cudnn_conv_algo_search': 'EXHAUSTIVE',
            'do_copy_in_default_stream': True,
        }),
        'CPUExecutionProvider'
    ]
    session = ort.InferenceSession(model_path, sess_options=sess_options, providers=providers)
    input_name = session.get_inputs()[0].name
    print(f"Model loaded on: {session.get_providers()[0]}")

    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    orig_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    orig_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()

    print(f"Video: {orig_w}x{orig_h} @ {fps}fps, {total_frames} frames")
    print(f"Batch size: {batch_size}")

    # Output video
    out_path = os.path.join(output_dir, f"{video_name}_tracked.mp4")
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    writer = cv2.VideoWriter(out_path, fourcc, fps, (orig_w, orig_h))

    # CSV output
    csv_path = os.path.join(output_dir, f"{video_name}_ball.csv")
    csv_file = open(csv_path, 'w', newline='')
    csv_writer = csv.writer(csv_file)
    csv_writer.writerow(['Frame', 'Timestamp_sec', 'X', 'Y', 'Confidence', 'Visible'])

    # Start frame reader thread
    frame_queue = queue.Queue(maxsize=batch_size * 4)
    reader_thread = threading.Thread(target=frame_reader, args=(video_path, frame_queue, seq_len))
    reader_thread.start()

    # Batch processing
    batch_indices = []
    batch_frames = []
    batch_tensors = []
    processed = 0
    import time
    start_time = time.time()

    while True:
        item = frame_queue.get()
        if item is None:
            # Process remaining batch
            if batch_tensors:
                stacked = np.concatenate(batch_tensors, axis=0)
                outputs = session.run(None, {input_name: stacked})
                for j in range(len(batch_tensors)):
                    out = outputs[0][j:j+1]
                    pos, conf = postprocess_heatmap(out, orig_w, orig_h, threshold)
                    visible = pos is not None
                    x, y = pos if visible else (0, 0)
                    frame_idx = batch_indices[j]
                    timestamp = frame_idx / fps
                    csv_writer.writerow([frame_idx, f"{timestamp:.3f}", x, y, f"{conf:.3f}", int(visible)])
                    frame = batch_frames[j]
                    if visible:
                        cv2.circle(frame, (x, y), 8, (0, 255, 255), -1)
                        cv2.circle(frame, (x, y), 12, (0, 165, 255), 2)
                    writer.write(frame)
            break

        frame_idx, frame, seq = item
        tensor = preprocess_frames(seq)
        batch_indices.append(frame_idx)
        batch_frames.append(frame)
        batch_tensors.append(tensor)

        if len(batch_tensors) >= batch_size:
            stacked = np.concatenate(batch_tensors, axis=0)
            outputs = session.run(None, {input_name: stacked})
            for j in range(len(batch_tensors)):
                out = outputs[0][j:j+1]
                pos, conf = postprocess_heatmap(out, orig_w, orig_h, threshold)
                visible = pos is not None
                x, y = pos if visible else (0, 0)
                fidx = batch_indices[j]
                timestamp = fidx / fps
                csv_writer.writerow([fidx, f"{timestamp:.3f}", x, y, f"{conf:.3f}", int(visible)])
                frame = batch_frames[j]
                if visible:
                    cv2.circle(frame, (x, y), 8, (0, 255, 255), -1)
                    cv2.circle(frame, (x, y), 12, (0, 165, 255), 2)
                writer.write(frame)
            processed += len(batch_tensors)
            batch_indices, batch_frames, batch_tensors = [], [], []

            if processed % 1000 == 0:
                elapsed = time.time() - start_time
                fps_actual = processed / elapsed
                pct = processed / total_frames * 100
                eta = (total_frames - processed) / fps_actual / 60
                print(f"  {pct:.1f}% — {fps_actual:.0f} fps — ETA {eta:.1f} min")

    reader_thread.join()
    writer.release()
    csv_file.close()
    print(f"\nDone! Tracked video: {out_path}")
    print(f"Ball CSV: {csv_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--video_path", required=True)
    parser.add_argument("--model_path", required=True)
    parser.add_argument("--output_dir", default="output_gpu")
    parser.add_argument("--threshold", type=float, default=0.5)
    parser.add_argument("--batch_size", type=int, default=8)
    args = parser.parse_args()
    run_inference(args.video_path, args.model_path, args.output_dir, args.threshold, batch_size=args.batch_size)