import numpy as np
from PIL import Image
import tensorflow as tf
from pytorch_grad_cam import GradCAM
from pytorch_grad_cam.utils.image import show_cam_on_image


class GradCam:
    @staticmethod
    def gradcam_for_model(model, img_input, pred_output, target_layer):
        cam = GradCAM(model=model, target_layers=[target_layer])

        heatmaps = []
        for channel in range(img_input.shape[-1]):
            img_array = img_input[..., channel]
            img_tensor = tf.convert_to_tensor(img_array, dtype=tf.float32)
            # targets = [ClassifierOutputTarget(pred_output)]
            grayscale_cam = cam(input_tensor=img_tensor, targets=[pred_output])
            heatmap = grayscale_cam[0, :]
            heatmaps.append(heatmap)
        return heatmaps

    @staticmethod
    def save_gradcam_heatmap(heatmap, original_img, output_path):
        heatmap = np.uint8(255 * heatmap)

        jet_heatmap = show_cam_on_image(original_img, heatmap, use_rgb=True)
        img = Image.fromarray(jet_heatmap)
        img.save(output_path)
