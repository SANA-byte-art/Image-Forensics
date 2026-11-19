import numpy as np
import matplotlib.pyplot as plt
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from sklearn.metrics import confusion_matrix, classification_report

# -----------------------------
# LOAD TRAINED MODEL
# -----------------------------
model = load_model("models/image_forensics_cnn_model.h5")

# -----------------------------
# TEST DATA GENERATOR
# -----------------------------
test_datagen = ImageDataGenerator(rescale=1./255)

test_generator = test_datagen.flow_from_directory(
    "dataset/test",
    target_size=(224, 224),
    batch_size=32,
    class_mode='categorical',
    shuffle=False
)
print("Class Mapping:", test_generator.class_indices)
# -----------------------------
# PREDICTIONS
# -----------------------------
y_pred = model.predict(test_generator)
y_pred_classes = np.argmax(y_pred, axis=1)
y_true = test_generator.classes

# -----------------------------
# CONFUSION MATRIX
# -----------------------------
cm = confusion_matrix(y_true, y_pred_classes)
print("Confusion Matrix:\n", cm)

# -----------------------------
# VISUALIZE CONFUSION MATRIX
# -----------------------------
class_names = ['Real', 'AI-Generated', 'Manipulated']

plt.figure(figsize=(6, 5))
plt.imshow(cm)
plt.title("Confusion Matrix")
plt.colorbar()

plt.xticks(range(3), class_names, rotation=45)
plt.yticks(range(3), class_names)

plt.xlabel("Predicted Label")
plt.ylabel("True Label")

for i in range(3):
    for j in range(3):
        plt.text(j, i, cm[i, j], ha='center', va='center')

plt.tight_layout()
plt.show()

# -----------------------------
# CLASSIFICATION REPORT
# -----------------------------
class_names = ['Real', 'AI-Generated', 'Manipulated']

report = classification_report(
    y_true,
    y_pred_classes,
    target_names=class_names
)

print("\nClassification Report:\n")
print(report)

print("Confusion Matrix:\n", cm)

