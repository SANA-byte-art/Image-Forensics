import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
from torchvision.models import resnet18, ResNet18_Weights

from V_dataset.temporal_dataset import TemporalDeepfakeDataset

# =====================
# CONFIG
# =====================

DATA_PATH = r"videoExt\frames"

BATCH_SIZE = 2
EPOCHS = 5
LEARNING_RATE = 0.0001

CHECKPOINT_PATH = "video_checkpoint.pth"

# =====================
# DEVICE (GPU if available)
# =====================

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

print("Using device:", device)

# =====================
# DATASET
# =====================

dataset = TemporalDeepfakeDataset(DATA_PATH)

loader = DataLoader(
    dataset,
    batch_size=BATCH_SIZE,
    shuffle=True,
    num_workers=0
)

# =====================
# MODEL (Pretrained ResNet18)
# =====================

class VideoCNN(nn.Module):

    def __init__(self):
        super(VideoCNN, self).__init__()

        # Load pretrained ResNet18
        base_model = resnet18(weights=ResNet18_Weights.DEFAULT)

        # Remove last classification layer
        self.feature_extractor = nn.Sequential(*list(base_model.children())[:-1])

        # New classifier
        self.classifier = nn.Sequential(
            nn.Linear(512, 128),
            nn.ReLU(),
            nn.Linear(128, 1),
            nn.Sigmoid()
        )

    def forward(self, x):

        B, T, C, H, W = x.shape

        # Merge batch + temporal dimension
        x = x.view(B*T, C, H, W)

        # Extract features
        features = self.feature_extractor(x)

        features = features.view(features.size(0), -1)

        out = self.classifier(features)

        # Restore temporal dimension
        out = out.view(B, T)

        # Temporal averaging
        out = torch.mean(out, dim=1)

        return out


model = VideoCNN().to(device)

criterion = nn.BCELoss()

optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE)

# =====================
# RESUME FROM CHECKPOINT
# =====================

start_epoch = 0

if torch.cuda.is_available():
    map_location = None
else:
    map_location = torch.device('cpu')

try:
    checkpoint = torch.load(CHECKPOINT_PATH, map_location=map_location)

    model.load_state_dict(checkpoint['model_state_dict'])
    optimizer.load_state_dict(checkpoint['optimizer_state_dict'])

    start_epoch = checkpoint['epoch'] + 1

    print("Checkpoint loaded. Resuming from epoch", start_epoch)

except:
    print("No checkpoint found. Starting fresh training.")

# =====================
# TRAINING LOOP
# =====================

for epoch in range(start_epoch, EPOCHS):

    total_loss = 0

    for clips, labels in loader:

        clips = clips.to(device)
        labels = labels.float().to(device)

        outputs = model(clips)

        loss = criterion(outputs, labels)

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        total_loss += loss.item()

    print(f"Epoch {epoch+1}/{EPOCHS} Loss: {total_loss:.4f}")

    # =====================
    # SAVE CHECKPOINT
    # =====================

    torch.save({
        'epoch': epoch,
        'model_state_dict': model.state_dict(),
        'optimizer_state_dict': optimizer.state_dict(),
    }, CHECKPOINT_PATH)

    print("Checkpoint saved")

# =====================
# SAVE FINAL MODEL
# =====================

torch.save(model.state_dict(), "video_deepfake_model.pth")

print("Training complete. Model saved.")