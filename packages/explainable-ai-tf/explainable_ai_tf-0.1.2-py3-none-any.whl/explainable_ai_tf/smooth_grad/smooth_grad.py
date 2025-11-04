import numpy as np
import saliency.core
# from saliency.core import IntegratedGradients, GradientSaliency

from explainable_ai_tf.common import call_model_function, create_heatmaps, call_model_function_with_filtered_neuron
from explainable_ai_tf.guided_backpropagation import GuidedBackpropagation
from explainable_ai_tf.smooth_grad.smooth_grad_core import SmoothIntegrated


class SmoothGrad:
    @staticmethod
    def blur_integrated_gradients(model, images, predicted_overlay_index):
        blur_ig = saliency.core.BlurIG()

        call_model_args = {'overlay_idx': predicted_overlay_index, "model": model}

        # Compute the vanilla mask and the Blur IG mask.
        blur_ig_mask_3d = blur_ig.GetMask(
            images, call_model_function, call_model_args, batch_size=20)
        # Call the visualization methods to convert the 3D tensors to 2D grayscale.
        return create_heatmaps(images, blur_ig_mask_3d)

    # @staticmethod
    # def vanilla_integrated_gradients(model, images, predicted_overlay_index):
    #     integrated_gradients = IntegratedGradients()
    #
    #     # Baseline is a black image for vanilla integrated gradients.
    #     baseline = np.zeros(images.shape)
    #
    #     call_model_args = {'overlay_idx': predicted_overlay_index, "model": model}
    #
    #     # Compute the vanilla mask and the Blur IG mask.
    #     vanilla_integrated_gradients_mask_3d = integrated_gradients.GetMask(
    #         images, call_model_function, call_model_args, x_steps=25, x_baseline=baseline, batch_size=20)
    #
    #     return create_heatmaps(images, vanilla_integrated_gradients_mask_3d)

    @staticmethod
    def smooth_grad_saliency(model, images, predicted_overlay_index):
        # gradient_saliency = GradientSaliency()
        gradient_saliency = SmoothIntegrated()

        call_model_args = {'overlay_idx': predicted_overlay_index, "model": model}

        # Compute the vanilla mask and the smoothed mask.
        smoothgrad_mask_3d = gradient_saliency.GetSmoothedMask(images, call_model_function, call_model_args, nsamples=50)

        return create_heatmaps(images,smoothgrad_mask_3d)

    @staticmethod
    def smooth_grad_integrated_gradients_guided(model, images, predicted_overlay_index):
        # integrated_gradients = IntegratedGradients()
        integrated_gradients = SmoothIntegrated()

        # Baseline is a black image
        baseline = np.zeros(images.shape)

        # guided backpropagation
        guided_model = GuidedBackpropagation.guided_backpropagation_modify_model(model)

        call_model_args = {'overlay_idx': predicted_overlay_index, "model": guided_model}

        smoothgrad_integrated_gradients_mask_3d = integrated_gradients.GetSmoothedMask(
            images, call_model_function, call_model_args, x_steps=25, x_baseline=baseline, batch_size=20,
            is_integrated=True)

        return create_heatmaps(images, smoothgrad_integrated_gradients_mask_3d)

    @staticmethod
    def smooth_grad_integrated_gradients_guided_with_filtered_neurons(model, images, predicted_overlay_index):
        # integrated_gradients = IntegratedGradients()
        integrated_gradients = SmoothIntegrated()

        # Baseline is a black image
        baseline = np.zeros(images.shape)

        # guided backpropagation
        guided_model = GuidedBackpropagation.guided_backpropagation_modify_model(model)

        call_model_args = {'overlay_idx': predicted_overlay_index, "model": guided_model}

        smoothgrad_integrated_gradients_mask_3d = integrated_gradients.GetSmoothedMask(
            images, call_model_function_with_filtered_neuron, call_model_args, x_steps=25, x_baseline=baseline, batch_size=20,
            is_integrated=True)

        return create_heatmaps(images, smoothgrad_integrated_gradients_mask_3d)