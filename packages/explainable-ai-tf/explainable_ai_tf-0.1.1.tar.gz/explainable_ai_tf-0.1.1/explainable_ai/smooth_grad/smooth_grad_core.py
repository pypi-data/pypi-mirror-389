import numpy as np

# Output of the last convolution layer for the given input, including the batch
# dimension.
CONVOLUTION_LAYER_VALUES = 'CONVOLUTION_LAYER_VALUES'
# Gradients of the output being explained (the logit/softmax value) with respect
# to the last convolution layer, including the batch dimension.
CONVOLUTION_OUTPUT_GRADIENTS = 'CONVOLUTION_OUTPUT_GRADIENTS'
# Gradients of the output being explained (the logit/softmax value) with respect
# to the input. Shape should be the same shape as x_value_batch.
INPUT_OUTPUT_GRADIENTS = 'INPUT_OUTPUT_GRADIENTS'
# Value of the output being explained (the logit/softmax value).
OUTPUT_LAYER_VALUES = 'OUTPUT_LAYER_VALUES'

SHAPE_ERROR_MESSAGE = {
    CONVOLUTION_LAYER_VALUES: (
        'Expected outermost dimension of CONVOLUTION_LAYER_VALUES to be the '
        'same as x_value_batch - expected {}, actual {}'
    ),
    CONVOLUTION_OUTPUT_GRADIENTS: (
        'Expected outermost dimension of CONVOLUTION_OUTPUT_GRADIENTS to be the '
        'same as x_value_batch - expected {}, actual {}'
    ),
    INPUT_OUTPUT_GRADIENTS: (
        'Expected key INPUT_OUTPUT_GRADIENTS to be the same shape as input '
        'x_value_batch - expected {}, actual {}'
    ),
    OUTPUT_LAYER_VALUES: (
        'Expected outermost dimension of OUTPUT_LAYER_VALUES to be the same as'
        ' x_value_batch - expected {}, actual {}'
    ),
}


class SmoothIntegrated:
    expected_keys = [INPUT_OUTPUT_GRADIENTS]

    def GetSmoothedMask(self,
                        x_value,
                        call_model_function,
                        call_model_args=None,
                        stdev_spread=.15,
                        nsamples=25,
                        is_integrated=False,
                        magnitude=True,
                        **kwargs):
        """Returns a mask that is smoothed with the SmoothGrad method.

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
          stdev_spread: Amount of noise to add to the input, as fraction of the
                        total spread (x_max - x_min). Defaults to 15%.
          nsamples: Number of samples to average across to get the smooth gradient.
          magnitude: If true, computes the sum of squares of gradients instead of
                     just the sum. Defaults to true.
          is_integrated: if we want to run integrated gradient mask
        """
        stdev = stdev_spread * (np.max(x_value) - np.min(x_value))

        total_gradients = np.zeros_like(x_value, dtype=np.float32)
        for _ in range(nsamples):
            noise = np.random.normal(0, stdev, x_value.shape)
            x_plus_noise = x_value + noise
            # normalize
            x_plus_noise = (x_plus_noise - np.mean(x_plus_noise, axis=(0, 1))) / np.std(x_plus_noise, axis=(0, 1))
            if is_integrated:
                grad = self.GetMaskIntegratedGradients(x_plus_noise, call_model_function, call_model_args, **kwargs)
            else:
                grad = self.GetMask(x_plus_noise, call_model_function, call_model_args)
            if magnitude:
                total_gradients += (grad * grad)
            else:
                total_gradients += grad

        return total_gradients / nsamples

    def GetMask(self, x_value, call_model_function, call_model_args=None):
        """Returns a vanilla gradients mask.

        Args:
          x_value: Input ndarray.
          call_model_function: A function that interfaces with a model to return
            specific data in a dictionary when given an input and other arguments.
            Expected function signature:
            - call_model_function(x_value_batch,
                                  call_model_args=None,
                                  expected_keys=None):
              x_value_batch - Input for the model, given as a batch (i.e. dimension
                0 is the batch dimension, dimensions 1 through n represent a single
                input).
              call_model_args - Other arguments used to call and run the model.
              expected_keys - List of keys that are expected in the output. For this
                method (Gradients), the expected keys are
                INPUT_OUTPUT_GRADIENTS - Gradients of the output layer
                  (logit/softmax) with respect to the input. Shape should be the
                  same shape as x_value_batch.
          call_model_args: The arguments that will be passed to the call model
            function, for every call of the model.
        """
        x_value_batched = np.expand_dims(x_value, axis=0)
        call_model_output = call_model_function(
            x_value_batched,
            call_model_args=call_model_args,
            expected_keys=self.expected_keys)

        self.format_and_check_call_model_output(call_model_output,
                                                x_value_batched.shape,
                                                self.expected_keys)

        return call_model_output[INPUT_OUTPUT_GRADIENTS][0]

    def GetMaskIntegratedGradients(self, x_value, call_model_function, call_model_args=None,
                x_baseline=None, x_steps=25, batch_size=1):
        """Returns an integrated gradients mask.

        Args:
          x_value: Input ndarray.
          call_model_function: A function that interfaces with a model to return
            specific data in a dictionary when given an input and other arguments.
            Expected function signature:
            - call_model_function(x_value_batch,
                                  call_model_args=None,
                                  expected_keys=None):
              x_value_batch - Input for the model, given as a batch (i.e. dimension
                0 is the batch dimension, dimensions 1 through n represent a single
                input).
              call_model_args - Other arguments used to call and run the model.
              expected_keys - List of keys that are expected in the output. For this
                method (Integrated Gradients), the expected keys are
                INPUT_OUTPUT_GRADIENTS - Gradients of the output being
                  explained (the logit/softmax value) with respect to the input.
                  Shape should be the same shape as x_value_batch.
          call_model_args: The arguments that will be passed to the call model
            function, for every call of the model.
          x_baseline: Baseline value used in integration. Defaults to 0.
          x_steps: Number of integrated steps between baseline and x.
          batch_size: Maximum number of x inputs (steps along the integration path)
            that are passed to call_model_function as a batch.
        """
        if x_baseline is None:
            x_baseline = np.zeros_like(x_value)

        assert x_baseline.shape == x_value.shape

        x_diff = x_value - x_baseline

        total_gradients = np.zeros_like(x_value, dtype=np.float32)

        x_step_batched = []
        for alpha in np.linspace(0, 1, x_steps):
            x_step = x_baseline + alpha * x_diff
            x_step_batched.append(x_step)
            if len(x_step_batched) == batch_size or alpha == 1:
                x_step_batched = np.asarray(x_step_batched)
                call_model_output = call_model_function(
                    x_step_batched,
                    call_model_args=call_model_args,
                    expected_keys=self.expected_keys)

                self.format_and_check_call_model_output(call_model_output,
                                                        x_step_batched.shape,
                                                        self.expected_keys)

                total_gradients += call_model_output[INPUT_OUTPUT_GRADIENTS].sum(axis=0)
                x_step_batched = []

        return total_gradients * x_diff / x_steps

    def format_and_check_call_model_output(self, output, input_shape, expected_keys):
        """Converts keys in the output into an np.ndarray, and confirms its shape.

        Args:
          output: The output dictionary of data to be formatted.
          input_shape: The shape of the input that yielded the output
          expected_keys: List of keys inside output to format/check for shape agreement.

        Raises:
            ValueError: If output shapes do not match expected shape."""
        # If key is in check_full_shape, the shape should be equal to the input shape (e.g.
        # INPUT_OUTPUT_GRADIENTS, which gives gradients for each value of the input). Otherwise,
        # only checks the outermost dimension of output to match input_shape (i.e. the batch size
        # should be the same).
        check_full_shape = [INPUT_OUTPUT_GRADIENTS]
        for expected_key in expected_keys:
            output[expected_key] = np.asarray(output[expected_key])
            expected_shape = input_shape
            actual_shape = output[expected_key].shape
            if expected_key not in check_full_shape:
                expected_shape = expected_shape[0]
                actual_shape = actual_shape[0]
            if expected_shape != actual_shape:
                raise ValueError(SHAPE_ERROR_MESSAGE[expected_key].format(
                    expected_shape, actual_shape))