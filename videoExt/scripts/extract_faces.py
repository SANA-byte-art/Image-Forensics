import os
import cv2
from pathlib import Path
from PIL import Image
from tqdm import tqdm
from facenet_pytorch import MTCNN

# ================= CONFIG =================
FPS = 6
IMG_SIZE = 224
DATA_ROOT = "videoExt/data"
OUT_ROOT = "videoExt/frames"
DEVICE = "cpu"
MAX_FRAMES = 80
# =========================================

mtcnn = MTCNN(
    image_size=IMG_SIZE,
    margin=10,
    keep_all=True,
    device=DEVICE
)

def extract_faces(video_path, out_dir):
    # 🔁 RESUME LOGIC (VIDEO LEVEL)
    if out_dir.exists():
        existing = list(out_dir.glob("*.jpg"))
        if len(existing) >= MAX_FRAMES:
            return  # already processed

    os.makedirs(out_dir, exist_ok=True)

    cap = cv2.VideoCapture(str(video_path))
    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps == 0:
        cap.release()
        return

    frame_interval = max(int(round(fps / FPS)), 1)
    frame_id = 0
    saved = len(list(out_dir.glob("*.jpg")))  # resume count

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_id % frame_interval == 0:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(rgb)

            boxes, _ = mtcnn.detect(img)

            if boxes is not None:
                areas = [(b[2]-b[0])*(b[3]-b[1]) for b in boxes]
                i = areas.index(max(areas))
                x1, y1, x2, y2 = map(int, boxes[i])

                # clamp bounding box
                h, w = frame.shape[:2]
                x1, y1 = max(0, x1), max(0, y1)
                x2, y2 = min(w, x2), min(h, y2)

                face = frame[y1:y2, x1:x2]
                if face.size > 0:
                    face = cv2.resize(face, (IMG_SIZE, IMG_SIZE))
                    cv2.imwrite(
                        os.path.join(out_dir, f"{saved:05d}.jpg"),
                        face
                    )
                    saved += 1

                    if saved >= MAX_FRAMES:
                        break

        frame_id += 1

    cap.release()

# ================= MAIN LOOP =================
for dataset in ["DFD", "CelebDFv2"]:
    dataset_root = Path(DATA_ROOT) / dataset

    for split in ["train", "val", "test"]:
        split_dir = dataset_root / split
        if not split_dir.exists():
            continue

        for class_dir in split_dir.rglob("*"):
            if not class_dir.is_dir():
                continue

            rel = class_dir.relative_to(DATA_ROOT)
            out_base = Path(OUT_ROOT) / rel

            videos = list(class_dir.glob("*.mp4"))
            for video in tqdm(videos, desc=str(rel)):
                extract_faces(video, out_base / video.stem)
