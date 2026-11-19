import os

DATASETS = ["CelebDFV2", "DFD"]
FRAMES_ROOT = "videoExt/frames/"

def count_frames(root_folder):
    total = 0
    
    for root, dirs, files in os.walk(root_folder):
        for file in files:
            if file.lower().endswith(('.jpg', '.png', '.jpeg')):
                total += 1
    
    return total


if __name__ == "__main__":
    
    for dataset in DATASETS:
        path = os.path.join(FRAMES_ROOT, dataset)
        total_frames = count_frames(path)
        print(f"Total frames in {dataset}: {total_frames}")
