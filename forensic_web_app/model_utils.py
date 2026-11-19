import numpy as np
from tensorflow.keras.models import load_model
from PIL import Image

model = load_model("image_forensics_cnn_model.h5")

class_names = ['AI-Generated', 'Manipulated', 'Real']

def predict_image(img_path):
    img = Image.open(img_path).convert("RGB")
    img = img.resize((224, 224))

    img_array = np.array(img) / 255.0
    img_array = np.expand_dims(img_array, axis=0)

    probs = model.predict(img_array)[0]

    final_index = np.argmax(probs)
    final_label = class_names[final_index]
    final_confidence = round(float(probs[final_index] * 100), 2)

    top_indices = probs.argsort()[-3:][::-1]
    top3 = [(class_names[i], round(float(probs[i] * 100), 2)) for i in top_indices]

    return final_label, final_confidence, top3
