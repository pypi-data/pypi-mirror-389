import numpy as np
import tensorflow as tf
from tensorflow.python.keras.utils.generic_utils import CustomObjectScope

from explainable_ai_tf.smooth_grad.smooth_grad_core import SmoothIntegrated

from explainable_ai_tf.guided_backpropagation import GuidedBackpropagation


class FusionGradCore:
    @staticmethod
    def add_noise_to_weights(model, noise_mean=1.0, noise_std=0.2):
        with CustomObjectScope({'guided_relu': GuidedBackpropagation.guided_relu}):
            noisy_model = tf.keras.models.clone_model(model)

        noisy_model.set_weights(model.get_weights())

        for layer in noisy_model.layers:
            if hasattr(layer, 'kernel') and layer.kernel is not None:
                noise = tf.random.normal(shape=layer.kernel.shape, mean=noise_mean, stddev=noise_std)
                layer.kernel.assign_add(noise)

        return noisy_model

    def GetFusionGradMask(self,
                          x_value,
                          call_model_function,
                          call_model_args=None,
                          sg_stdev_spread=0.15,
                          nsamples=10,
                          is_integrated=False,
                          fg_stdev=0.2,
                          fg_mean=1.0,
                          magnitude=True,
                          **kwargs):
        """Returns a mask that is fusionGrad with the SmoothGrad method.

        Args:
          x_value: Input ndarray.
          call_model_function: A function that interfaces with a model to return
            specific output in a dictionary when given an input and other arguments.
            Expected function signature:
            - call_model_function(x_value_batch,
                                  call_model_args=None,
                                  expected_keys=None):
              x_value_batch - Input for the model, given as a batch (i.e. dimension
                0 is the batch dimension, dimensions 1 through n represent a single
                input).
              call_model_args - Other arguments used to call and run the model.
              expected_keys - List of keys that are expected in the output. Possible
                keys in this list are CONVOLUTION_LAYER_VALUES,
                CONVOLUTION_OUTPUT_GRADIENTS, INPUT_OUTPUT_GRADIENTS, and
                OUTPUT_LAYER_VALUES, and are explained in detail where declared.
          call_model_args: The arguments that will be passed to the call model
            function, for every call of the model.
          sg_stdev_spread: Amount of noise to add to the input, as fraction of the
                        total spread (x_max - x_min). Defaults to 15%.
          nsamples: Number of samples to average across to get the smooth gradient.
          magnitude: If true, computes the sum of squares of gradients instead of
                     just the sum. Defaults to true.
          is_integrated: if we want to run integrated gradient mask
        """
        sg_stdev = sg_stdev_spread * (np.max(x_value) - np.min(x_value))

        smooth_integrated = SmoothIntegrated()
        fg_total_gradients = np.zeros_like(x_value, dtype=np.float32)
        origin_model = call_model_args["model"]
        for _ in range(nsamples):
            call_model_args["model"] = FusionGradCore.add_noise_to_weights(model=origin_model,
                                                                           noise_mean=fg_mean, noise_std=fg_stdev)
            sg_total_gradients = np.zeros_like(x_value, dtype=np.float32)
            for _ in range(nsamples):
                noise = np.random.normal(0, sg_stdev, x_value.shape)
                x_plus_noise = x_value + noise
                # normalize
                x_plus_noise = (x_plus_noise - np.mean(x_plus_noise, axis=(0, 1))) / np.std(x_plus_noise, axis=(0, 1))
                if is_integrated:
                    grad = smooth_integrated.GetMaskIntegratedGradients(x_plus_noise, call_model_function,
                                                                        call_model_args, **kwargs)
                else:
                    grad = smooth_integrated.GetMask(x_plus_noise, call_model_function, call_model_args)
                if magnitude:
                    sg_total_gradients += (grad * grad)
                else:
                    sg_total_gradients += grad

            fg_total_gradients+= (sg_total_gradients / nsamples)

        return fg_total_gradients / nsamples
