import os

# Adjust this path if needed
FRAMES_ROOT = "videoExt/frames/DFD"

def count_frames(root_folder):
    total = 0
    
    for root, dirs, files in os.walk(root_folder):
        for file in files:
            if file.lower().endswith(('.jpg', '.png', '.jpeg')):
                total += 1
    
    return total


if __name__ == "__main__":
    total_frames = count_frames(FRAMES_ROOT)
    print(f"\nTotal frames in CelebDFV2: {total_frames}")
