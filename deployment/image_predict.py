import numpy as np
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image
from tkinter import Tk, filedialog

# -----------------------------------
# Load trained model
# -----------------------------------
model = load_model(
    "models/image_forensics_cnn_model.h5"
)

# IMPORTANT: order must match training class_indices
class_names = ['AI-Generated', 'Manipulated', 'Real']

# -----------------------------------
# Predict single image
# -----------------------------------
def predict_image(img_path):
    img = image.load_img(img_path, target_size=(224, 224))
    img_array = image.img_to_array(img) / 255.0
    img_array = np.expand_dims(img_array, axis=0)

    probs = model.predict(img_array)[0]

    # Argmax → final decision
    final_index = np.argmax(probs)
    final_label = class_names[final_index]
    final_confidence = probs[final_index] * 100

    # Top-3 → interpretability
    top_indices = probs.argsort()[-3:][::-1]
    top3 = [(class_names[i], probs[i] * 100) for i in top_indices]

    return final_label, final_confidence, top3


# -----------------------------------
# File dialog (stable & on top)
# -----------------------------------
root = Tk()
root.withdraw()
root.lift()
root.attributes('-topmost', True)
root.after_idle(root.attributes, '-topmost', False)

image_path = filedialog.askopenfilename(
    parent=root,
    title="Select an image",
    filetypes=[("Image files", "*.jpg *.jpeg *.png")]
)

root.destroy()

# -----------------------------------
# Run prediction
# -----------------------------------
if image_path:
    final_label, final_confidence, top3 = predict_image(image_path)

    print("\nSelected Image:", image_path)

    print("\nFinal Prediction (Argmax):")
    print(f"{final_label} ({final_confidence:.2f}%)")

    print("\nTop-3 Probabilities:")
    for i, (label, conf) in enumerate(top3, start=1):
        print(f"{i}. {label} - {conf:.2f}%")

else:
    print("No image selected.")
