import cv2
import torch
import numpy as np
from PIL import Image
import torchvision.transforms as transforms
from torchvision.models import resnet18
import torch.nn as nn

# ===== MODEL (same as training) =====

class VideoCNN(nn.Module):
    def __init__(self):
        super(VideoCNN, self).__init__()

        base_model = resnet18(pretrained=False)
        self.feature_extractor = nn.Sequential(*list(base_model.children())[:-1])

        self.classifier = nn.Sequential(
            nn.Linear(512, 128),
            nn.ReLU(),
            nn.Linear(128, 1),
            nn.Sigmoid()
        )

    def forward(self, x):
        B, T, C, H, W = x.shape
        x = x.view(B*T, C, H, W)

        features = self.feature_extractor(x)
        features = features.view(features.size(0), -1)

        out = self.classifier(features)
        out = out.view(B, T)

        return torch.mean(out, dim=1)


# ===== LOAD MODEL =====

device = torch.device("cpu")

model = VideoCNN()
MODEL_PATH = "video_deepfake_model.pth"
model.load_state_dict(torch.load(MODEL_PATH, map_location=device))
model.eval()



# ===== TRANSFORM =====

transform = transforms.Compose([
    transforms.Resize((224,224)),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485,0.456,0.406],
        std=[0.229,0.224,0.225]
    )
])


# ===== VIDEO PREDICTION =====

def predict_video(video_path, clip_length=8):

    cap = cv2.VideoCapture(video_path)

    frames = []
    results = []

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(rgb)
        img = transform(img)

        frames.append(img)
        

        if len(frames) == clip_length:
            clip = torch.stack(frames).unsqueeze(0)

            with torch.no_grad():
                output = model(clip)
                print("Model output:", output.item())
                pred = output.item()

            results.append(pred)
            frames = []

    cap.release()

    if not results:
        return "Error", 0

    avg_pred = np.mean(results)
    std_pred = np.std(results)

    print("Average:", avg_pred, "Std:", std_pred)

    # SMART LOGIC
    if std_pred < 0.02:
       # model too confident → suspicious
       label = "FAKE VIDEO"
       confidence = avg_pred
    else:
        label = "REAL VIDEO"
        confidence = 1 - avg_pred

    return label, round(confidence * 100, 2)