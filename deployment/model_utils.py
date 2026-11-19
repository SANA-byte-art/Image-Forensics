import numpy as np
import tensorflow as tf
from tensorflow.keras.preprocessing import image

# ----------------------------------------------------------------------
# Custom deserializer for DTypePolicy: returns the dtype name as a string
# ----------------------------------------------------------------------
class PatchedDTypePolicy:
    @classmethod
    def from_config(cls, config):
        # config is like {'name': 'float32'}
        return config['name']

# ----------------------------------------------------------------------
# Patch InputLayer to convert 'batch_shape' to 'batch_input_shape'
# ----------------------------------------------------------------------
class PatchedInputLayer(tf.keras.layers.InputLayer):
    @classmethod
    def from_config(cls, config):
        if 'batch_shape' in config:
            config['batch_input_shape'] = config.pop('batch_shape')
        return super().from_config(config)

# ----------------------------------------------------------------------
# MODEL PATH
# ----------------------------------------------------------------------
MODEL_PATH = r"models/image_forensics_cnn_model.h5"

# ----------------------------------------------------------------------
# Load model with custom objects
# ----------------------------------------------------------------------
model = tf.keras.models.load_model(
    MODEL_PATH,
    compile=False,
    custom_objects={
        'InputLayer': PatchedInputLayer,
        'DTypePolicy': PatchedDTypePolicy,   # handles the dtype policy
    }
)

# Must match alphabetical order of folders used during training
class_names = ['ai_generated', 'manipulated', 'real']

def predict_image_streamlit(pil_image):
    img = pil_image.resize((224, 224))
    img_array = image.img_to_array(img) / 255.0
    img_array = np.expand_dims(img_array, axis=0)

    probs = model.predict(img_array, verbose=0)[0]

    final_index = np.argmax(probs)
    final_label = class_names[final_index]
    final_confidence = probs[final_index] * 100

    top_indices = probs.argsort()[::-1]
    top3 = [(class_names[i], probs[i] * 100) for i in top_indices]

    return final_label, final_confidence, top3, probs