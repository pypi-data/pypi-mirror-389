import os

import tensorflow as tf
import numpy as np
# import saliency.core
import matplotlib.pyplot as plt

INPUT_OUTPUT_GRADIENTS = 'INPUT_OUTPUT_GRADIENTS'
CONVOLUTION_LAYER_VALUES = 'CONVOLUTION_LAYER_VALUES'
CONVOLUTION_OUTPUT_GRADIENTS = 'CONVOLUTION_OUTPUT_GRADIENTS'

def print_last_layer_weights_model_statistics(model, out_folder, overlay_index):
    # Access the last layer
    last_layer = model.layers[-1]

    # Get weights and biases
    weights, _ = last_layer.get_weights()
    # Ensure the directory exists
    image_out_folder = out_folder+"/weights/last_layer_weight_distribution.tiff"
    directory = os.path.dirname(image_out_folder)
    if not os.path.exists(directory):
        os.makedirs(directory)
    # Create scatter plot
    plt.figure(figsize=(8, 5))
    plt.scatter(range(weights.shape[0]), weights[:, 0], color='blue', label='Neuron 1')
    # plt.scatter(range(weights.shape[0]), weights[:, 1], color='orange', label='Neuron 2')
    plt.xlabel('Neuron Index')
    plt.ylabel('Weight Value')
    plt.title('Last Layer Weights Distribution')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(image_out_folder)

    # Print basic statistics
    print("Last Layer Weight Statistics:")
    print(f"Min: {np.min(weights[:,overlay_index])}")
    print(f"Max: {np.max(weights[:,overlay_index])}")
    print(f"Mean: {np.mean(weights[:,overlay_index])}")
    print(f"Std Dev: {np.std(weights[:,overlay_index])}")
    print("Histogram saved as 'weight_distribution.png'")


def call_model_function(images, call_model_args, expected_keys=None):
    target_overlay_idx = call_model_args['overlay_idx']
    model = call_model_args["model"]
    images_tf = tf.convert_to_tensor(images, dtype=tf.float32)
    with tf.GradientTape() as tape:
        if expected_keys == [INPUT_OUTPUT_GRADIENTS]:
            tape.watch(images_tf)
            output_layer = model(images_tf)
            output_layer = output_layer[:, target_overlay_idx]
            gradients = np.array(tape.gradient(output_layer, images_tf))
            return {INPUT_OUTPUT_GRADIENTS: gradients}
        else:
            conv_layer, output_layer = model(images_tf)
            gradients = np.array(tape.gradient(output_layer, conv_layer))
            return {
                CONVOLUTION_LAYER_VALUES: conv_layer,
                CONVOLUTION_OUTPUT_GRADIENTS: gradients
            }


def call_model_function_with_filtered_neuron(images, call_model_args, expected_keys=None, weight_threshold=0.2):
    target_overlay_idx = call_model_args['overlay_idx']
    model = call_model_args["model"]
    images_tf = tf.convert_to_tensor(images, dtype=tf.float32)
    # גישה לשכבה האחרונה
    last_layer = model.layers[-1]
    weights, _ = last_layer.get_weights()
    # יצירת מסכה עבור נוירונים עם משקל משמעותי
    significant_neurons_mask = tf.reduce_any(tf.abs(weights[:,target_overlay_idx]) > weight_threshold, axis=0)
    with tf.GradientTape() as tape:
        tape.watch(images_tf)
        output = model(images_tf)
        if expected_keys == [INPUT_OUTPUT_GRADIENTS]:
            selected_outputs = output[:, target_overlay_idx]
            # סינון לפי משקולות
            filtered_output = tf.where(significant_neurons_mask[target_overlay_idx], selected_outputs,
                                       tf.zeros_like(selected_outputs))

            gradients = tape.gradient(filtered_output, images_tf)
            return {INPUT_OUTPUT_GRADIENTS: np.array(gradients)}
        else:
            conv_layer, output_layer = output
            # סינון לפי משקולות
            filtered_output = tf.where(significant_neurons_mask, output_layer, tf.zeros_like(output_layer))
            gradients = tape.gradient(filtered_output, conv_layer)
            return {
                CONVOLUTION_LAYER_VALUES: conv_layer,
                CONVOLUTION_OUTPUT_GRADIENTS: np.array(gradients)
            }


def create_heatmaps(images, mask_3d):
    heatmaps = []
    for channel in range(images.shape[-1]):
        image = mask_3d[..., channel]
        # computes the 99th percentile of all pixel values in the image - helps to ignore extreme outliers,
        # it gives a more stable and interpretable visualization
        span = abs(np.percentile(image, 99))
        vmin = -span
        vmax = span
        heatmap = np.clip((image - vmin) / (vmax - vmin), -1, 1)
        heatmap = np.uint8(255 * heatmap)
        heatmaps.append(heatmap)
    return heatmaps


def save_image(image_to_save, file_path, title='Heatmap', cmap='jet', draw_rect=False,
               top_left=(0, 0), bottom_right=(0, 0), print_colorbar=True):
    # Ensure the directory exists
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)

    if draw_rect:
        image_to_save = draw_rectangle(image_to_save, top_left, bottom_right)

    img = plt.imshow(image_to_save, cmap=cmap)
    if print_colorbar:
        plt.colorbar(img)
    plt.title(title)
    plt.savefig(file_path)
    plt.close()


def plot_stack(orig_image, heatmap, filename, title='Combine Heatmap & Image', cmap='jet'):
    scaled = (orig_image - np.min(orig_image)) / (np.max(orig_image - np.min(orig_image)))
    colored_orig_image = np.uint8(255 * scaled)
    if orig_image.ndim == 2:
        combined_image = np.stack((colored_orig_image, heatmap, heatmap), axis=-1)
    else:
        combined_image = np.stack((colored_orig_image[:, :, 0], heatmap, colored_orig_image[:, :, 1]), axis=-1)
    save_image(combined_image, filename, title, cmap)


def _normalize_image(image):  # Z-Score Normalization (Standardization to mean=0 and std=1)
    image -= image.mean()
    image /= image.std()
    image *= 64
    image += 128
    return np.clip(image, 0, 255).astype('uint8')


def deprocess_image(x):
    # normalize tensor: center on 0., ensure std is 0.1
    x -= x.mean()
    x /= (x.std() + 1e-5)
    x *= 0.1

    # clip to [0, 1]
    x += 0.5
    x = np.clip(x, 0, 1)

    # convert to RGB array
    x *= 255
    x = np.clip(x, 0, 255).astype('uint8')
    return x


def is_float_type(image):
    return image.dtype in [np.float32, np.float64]


def draw_rectangle(image, top_left, bottom_right):
    if is_float_type(image):
        image = (image - image.min()) / (image.max() - image.min())
        white_color = 1.0  # max of normalized range
    else:
        white_color = 255

    (x1, y1) = top_left
    (x2, y2) = bottom_right

    image[y1:y2, x1] = white_color
    image[y1:y2, x2] = white_color
    image[y1, x1:x2] = white_color
    image[y2, x1:x2] = white_color

    return image
