import os
import cv2
import numpy as np

# ==========================
# CONFIGURATION
# ==========================
BLACK_THRESHOLD = 15
BLUR_THRESHOLD = 5
DRY_RUN = False  # True = Only count, False = Actually delete

FRAMES_ROOT = "videoExt/frames"


# ==========================
# IMAGE CHECK FUNCTIONS
# ==========================

def is_black_image(image_path, threshold=BLACK_THRESHOLD):
    img = cv2.imread(image_path)
    if img is None:
        return True
    
    mean_intensity = np.mean(img)
    return mean_intensity < threshold


def is_blurry(image_path, threshold=BLUR_THRESHOLD):
    img = cv2.imread(image_path)
    if img is None:
        return True
    
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    variance = cv2.Laplacian(gray, cv2.CV_64F).var()
    
    return variance < threshold


# ==========================
# CLEANING FUNCTION
# ==========================

def clean_video_folder(video_path):
    removed_count = 0
    
    for frame in os.listdir(video_path):
        frame_path = os.path.join(video_path, frame)
        
        if not frame.lower().endswith(('.png', '.jpg', '.jpeg')):
            continue
        
        try:
            if is_black_image(frame_path) or is_blurry(frame_path):
                
                if not DRY_RUN:
                    os.remove(frame_path)
                
                removed_count += 1
        
        except Exception as e:
            print(f"Error processing {frame_path}: {e}")
    
    return removed_count


# ==========================
# PROCESS DATASET
# ==========================

def process_dataset(dataset_name):
    dataset_path = os.path.join(FRAMES_ROOT, dataset_name)
    
    print("\n==============================")
    print(f"Processing Dataset: {dataset_name}")
    print("==============================")
    
    total_removed = 0
    
    for root, dirs, files in os.walk(dataset_path):
        if len(files) > 0:
            removed = clean_video_folder(root)
            total_removed += removed
    
    if DRY_RUN:
        print(f"[DRY RUN COMPLETE] {dataset_name} - {total_removed} frames would be removed.")
    else:
        print(f"[CLEANING COMPLETE] {dataset_name} - {total_removed} frames removed.")


# ==========================
# MAIN
# ==========================

def main():
    datasets = ["DFD", "CelebDFV2"]
    
    for dataset in datasets:
        process_dataset(dataset)


if __name__ == "__main__":
    main()
