import numpy as np

from explainable_ai_tf.common import create_heatmaps, call_model_function
from explainable_ai_tf.fusion_grad.fusion_grad_core import FusionGradCore


class FusionGrad:
    @staticmethod
    def fusion_grad(model, images, predicted_overlay_index):
        gradient_fusion_grad = FusionGradCore()

        call_model_args = {'overlay_idx': predicted_overlay_index, "model": model}

        # Compute the fusion mask
        fusion_grad_mask_3d = gradient_fusion_grad.GetFusionGradMask(images, call_model_function=call_model_function,
                                                                     call_model_args=call_model_args, nsamples=10)

        return create_heatmaps(images,fusion_grad_mask_3d)

    @staticmethod
    def fusion_grad_integrated_gradients(model, images, predicted_overlay_index):
        gradient_fusion_grad = FusionGradCore()

        # Baseline is a black image
        baseline = np.zeros(images.shape)

        # guided backpropagation
        # guided_model = GuidedBackpropagation.guided_backpropagation_modify_model(model)

        call_model_args = {'overlay_idx': predicted_overlay_index, "model": model}

        fusiongrad_integrated_gradients_mask_3d = gradient_fusion_grad.GetFusionGradMask(images, call_model_function,
                                                                                         call_model_args,
                                                                                         is_integrated=True, x_steps=60,
                                                                                         x_baseline=baseline,
                                                                                         batch_size=20)

        return create_heatmaps(images, fusiongrad_integrated_gradients_mask_3d)