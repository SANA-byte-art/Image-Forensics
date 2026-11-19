import os
import torch
from torch.utils.data import Dataset
from PIL import Image
import torchvision.transforms as transforms


class TemporalDeepfakeDataset(Dataset):

    def __init__(self, root_dir, clip_length=8, stride=3):
        self.root_dir = root_dir
        self.clip_length = clip_length
        self.stride = stride
        self.samples = []
        self.transform = transforms.Compose([
            transforms.Resize((224,224)),
            transforms.RandomHorizontalFlip(),
            transforms.ColorJitter(brightness=0.2, contrast=0.2),
            transforms.ToTensor(),
            transforms.Normalize(
               mean=[0.485,0.456,0.406],
               std=[0.229,0.224,0.225]
    )
])
        self._prepare_dataset()

    def _prepare_dataset(self):

        for root, dirs, files in os.walk(self.root_dir):

            images = sorted([
                os.path.join(root, f)
                for f in files
                if f.lower().endswith((".jpg", ".png", ".jpeg"))
            ])

            if len(images) < self.clip_length:
                continue

            # Simple labeling rule
            if "real" in root.lower():
                label = 0
            elif "fake" in root.lower() or "synthesis" in root.lower():
                label = 1
            else:
                continue

            for i in range(0, len(images) - self.clip_length + 1, self.stride):
                clip = images[i:i+self.clip_length]
                self.samples.append((clip, label))
                # limit dataset size for faster training
                if len(self.samples) >= 30000:
                   print("Total clips:", len(self.samples)) 
                   return

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):

        clip_paths, label = self.samples[idx]

        frames = []
        for path in clip_paths:
            img = Image.open(path).convert("RGB")
            img = self.transform(img)
            frames.append(img)

        clip_tensor = torch.stack(frames)

        return clip_tensor, torch.tensor(label, dtype=torch.long)
