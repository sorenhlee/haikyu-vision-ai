from ultralytics import YOLO
import cv2, warnings, torchreid
warnings.filterwarnings("ignore")
from deep_sort_realtime.deepsort_tracker import DeepSort

# List all available models in torchreid
# print(torchreid.models.show_avai_models())
# exit(0)

# Load YOLOv11 model
model = YOLO('best.pt')

# Initialize Deep SORT tracker
tracker = DeepSort(
    max_age=200, # long memory
    n_init=5, # 5 frames to confirm a detection
    nms_max_overlap=0.1, # moderate suppression threshold
    max_iou_distance=0.3, # loose spatial matching
    max_cosine_distance=0.2, # strict visual matching
    nn_budget=300, # long term appearance memory
    embedder='torchreid',
    embedder_model_name='osnet_ain_x1_0',     
    embedder_gpu=True
)

# Load input video
cap = cv2.VideoCapture('15sec_input_720p.mp4')
fps = int(cap.get(cv2.CAP_PROP_FPS))
frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

# Create video writer for output
output = cv2.VideoWriter('output.mp4', cv2.VideoWriter_fourcc(*'mp4v'), fps, (frame_width, frame_height))

track_class_map = {}

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    # Run detection
    results = model(frame)[0]
    detections = []

    # Extract player detections
    for det in results.boxes.data.tolist():
        x1, y1, x2, y2, conf, cls_id = det
        cls_id = int(cls_id)
        
        # Filter by confidence, size, and class
        if conf < 0.6 or (x2 - x1 < 10 or y2 - y1 < 10) or results.names[cls_id] != 'player':
            continue

        det_class = results.names[cls_id]
        bbox = [int(x1), int(y1), int(x2 - x1), int(y2 - y1)]
        detections.append((bbox, conf, det_class))

    if not detections:
        continue

    # Update tracker with detections
    tracks = tracker.update_tracks(detections, frame=frame)

    # Draw tracks
    for track in tracks:
        if not track.is_confirmed():
            continue    

        track_id = track.track_id
        det_class = track.det_class if hasattr(track, 'det_class') else 'unknown'

        # Save class label per track (once)
        if track_id not in track_class_map:
            track_class_map[track_id] = det_class

        # Only draw if we believe this track is a player
        if track_class_map[track_id] != 'player':
            continue

        x1, y1, x2, y2 = map(int, track.to_ltrb())
        color = (0, 255, 0)
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        cv2.putText(frame, f'Player {track_id}', (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

    output.write(frame)
    cv2.imshow('Player Re-Identification', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
output.release()
cv2.destroyAllWindows()