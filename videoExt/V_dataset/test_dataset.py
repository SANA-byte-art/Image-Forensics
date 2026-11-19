from temporal_dataset import TemporalDeepfakeDataset
from torch.utils.data import DataLoader

root_path = "videoExt/frames"

dataset = TemporalDeepfakeDataset(root_dir=root_path)

print("Dataset size:", len(dataset))

loader = DataLoader(dataset, batch_size=4, shuffle=True)

clips, labels = next(iter(loader))

print("Batch shape:", clips.shape)
print("Labels shape:", labels.shape)
