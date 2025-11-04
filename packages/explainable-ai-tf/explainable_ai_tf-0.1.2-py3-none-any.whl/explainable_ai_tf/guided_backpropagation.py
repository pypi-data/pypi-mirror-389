import numpy as np
import tensorflow as tf

from tensorflow.keras.models import clone_model
from explainable_ai_tf.common import call_model_function, create_heatmaps
INPUT_OUTPUT_GRADIENTS = 'INPUT_OUTPUT_GRADIENTS'

INPUT_OUTPUT_GRADIENTS: (
        'Expected key INPUT_OUTPUT_GRADIENTS to be the same shape as input '
        'x_value_batch - expected {}, actual {}'
    )


class GuidedBackpropagation:

    @staticmethod
    @tf.custom_gradient
    def guided_relu(x):
        def grad(dy):
            # dy is the incoming gradient from the layer above during backpropagation.
            # x is the input to the ReLU during the forward pass
            # The custom gradient does this:
            # It blocks negative gradients (dy > 0) — only allows positive gradients to flow.
            # It also blocks gradients where the input to ReLU was negative (x > 0) - like ReLU
            # The result is that only positive influences are propagated back
            return tf.cast(dy > 0, dtype=tf.float32) * tf.cast(x > 0, dtype=tf.float32) * dy

        return tf.nn.relu(x), grad

    @staticmethod
    def guided_backpropagation_modify_model(model):


        def modify_relu(model):
            for layer in model.layers:
                if hasattr(layer, 'activation') and layer.activation == tf.keras.activations.relu:
                    layer.activation = GuidedBackpropagation.guided_relu
            return model

        # Clone the model architecture
        cloned_model = clone_model(model)
        cloned_model.build(model.input_shape)  # Ensure the model is built
        cloned_model.set_weights(model.get_weights())  # Copy weights

        # Modify ReLU activations in the cloned model
        guided_model = modify_relu(cloned_model)

        return guided_model

    @staticmethod
    def guided_backpropagation(model, images, predicted_overlay_index):
        expected_keys = [INPUT_OUTPUT_GRADIENTS]

        # guided backpropagation
        guided_model = GuidedBackpropagation.guided_backpropagation_modify_model(model)

        call_model_args = {'overlay_idx': predicted_overlay_index, "model": guided_model}

        guided_backpropagation_gradients = call_model_function(images, call_model_args, expected_keys)

        guided_backpropagation_gradients_image = np.squeeze(guided_backpropagation_gradients[INPUT_OUTPUT_GRADIENTS], axis=0)

        return create_heatmaps(images, guided_backpropagation_gradients_image)