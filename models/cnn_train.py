from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv2D, MaxPooling2D, Flatten, Dense, Dropout
from tensorflow.keras.optimizers import Adam

# -----------------------------
# CONFIGURATION
# -----------------------------
img_size = (224, 224)
batch_size = 16
epochs = 10

# -----------------------------
# DATA GENERATORS
# -----------------------------
datagen = ImageDataGenerator(rescale=1.0 / 255)

train_data = datagen.flow_from_directory(
    "dataset/train",
    target_size=img_size,
    batch_size=batch_size,
    class_mode="categorical"
)

val_data = datagen.flow_from_directory(
    "dataset/val",
    target_size=img_size,
    batch_size=batch_size,
    class_mode="categorical"
)

test_data = datagen.flow_from_directory(
    "dataset/test",
    target_size=img_size,
    batch_size=batch_size,
    class_mode="categorical",
    shuffle=False
)

print("Class indices:", train_data.class_indices)
print("Train samples:", train_data.samples)
print("Val samples:", val_data.samples)
print("Test samples:", test_data.samples)

# -----------------------------
# CNN MODEL
# -----------------------------
model = Sequential()

model.add(Conv2D(32, (3, 3), activation="relu", input_shape=(224, 224, 3)))
model.add(MaxPooling2D(2, 2))

model.add(Conv2D(64, (3, 3), activation="relu"))
model.add(MaxPooling2D(2, 2))

model.add(Conv2D(128, (3, 3), activation="relu"))
model.add(MaxPooling2D(2, 2))

model.add(Flatten())
model.add(Dense(128, activation="relu"))
model.add(Dropout(0.5))
model.add(Dense(3, activation="softmax"))

# -----------------------------
# COMPILE MODEL
# -----------------------------
model.compile(
    optimizer=Adam(learning_rate=0.0001),
    loss="categorical_crossentropy",
    metrics=["accuracy"]
)

model.summary()

# -----------------------------
# TRAIN MODEL
# -----------------------------
history = model.fit(
    train_data,
    epochs=epochs,
    validation_data=val_data
)

# -----------------------------
# EVALUATE MODEL
# -----------------------------
test_loss, test_accuracy = model.evaluate(test_data)
print("Test Accuracy:", test_accuracy)

# -----------------------------
# SAVE MODEL
# -----------------------------
model.save("image_forensics_cnn_model.h5")
print("Model saved as image_forensics_cnn_model.h5")

import matplotlib.pyplot as plt

# Accuracy graph
plt.figure()
plt.plot(history.history['accuracy'], label='Training Accuracy')
plt.plot(history.history['val_accuracy'], label='Validation Accuracy')
plt.xlabel('Epochs')
plt.ylabel('Accuracy')
plt.title('Training vs Validation Accuracy')
plt.legend()
plt.grid(True)
plt.savefig("accuracy_plot.png")
plt.show()

# Loss graph
plt.figure()
plt.plot(history.history['loss'], label='Training Loss')
plt.plot(history.history['val_loss'], label='Validation Loss')
plt.xlabel('Epochs')
plt.ylabel('Loss')
plt.title('Training vs Validation Loss')
plt.legend()
plt.grid(True)
plt.savefig("loss_plot.png")
plt.show()
