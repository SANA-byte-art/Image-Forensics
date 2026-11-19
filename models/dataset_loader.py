from tensorflow.keras.preprocessing.image import ImageDataGenerator

img_size = (224, 224)
batch_size = 16

datagen = ImageDataGenerator(rescale=1./255)

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
print(train_data.samples)
print(val_data.samples)
print(test_data.samples)
