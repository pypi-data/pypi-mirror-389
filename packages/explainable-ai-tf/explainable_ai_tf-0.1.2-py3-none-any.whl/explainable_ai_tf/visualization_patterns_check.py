import os
from pathlib import Path

import numpy as np
from keras.applications.vgg16 import VGG16
from matplotlib import pyplot as plt
import tensorflow as tf

from explainable_ai_tf.common import deprocess_image


def visualize_all_patterns_vgg(model, out_folder):
    for layer_name in ['block1_conv1', 'block2_conv1', 'block3_conv1', 'block4_conv1']:
        size = 64
        margin = 5

        # This a empty (black) image where we will store our results.
        results = np.zeros((8 * size + 7 * margin, 8 * size + 7 * margin, 3))

        for i in range(8):  # iterate over the rows of our results grid
            for j in range(8):  # iterate over the columns of our results grid
                # Generate the pattern for filter `i + (j * 8)` in `layer_name`
                filter_img = generate_pattern(model=model, layer_name=layer_name, filter_index=i + (j * 8), size=size)

                # Put the result in the square `(i, j)` of the results grid
                horizontal_start = i * size + i * margin
                horizontal_end = horizontal_start + size
                vertical_start = j * size + j * margin
                vertical_end = vertical_start + size
                results[horizontal_start: horizontal_end, vertical_start: vertical_end, :] = filter_img

        results /= 255.0

        # Save the results grid
        file_path = out_folder + f"/conv_layers/patterns/{layer_name}_patterns.tiff"
        directory = os.path.dirname(file_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory)

        # Save the image using matplotlib
        plt.figure()
        plt.imshow(results)
        plt.axis('off')  # Hide axes
        plt.savefig(file_path, bbox_inches='tight')
        plt.close()

def generate_pattern(model, layer_name, filter_index, size=150):
    layer_output = model.get_layer(layer_name).output
    sub_model = tf.keras.Model(inputs=model.inputs, outputs=layer_output)

    # Start from a random image
    input_img_data = tf.random.uniform((1, size, size, 3)) * 20 + 128.
    input_img_data = tf.Variable(input_img_data)

    step = 1.0
    for i in range(40):
        with tf.GradientTape() as tape:
            activations = sub_model(input_img_data)
            loss = tf.reduce_mean(activations[:, :, :, filter_index])
        grads = tape.gradient(loss, input_img_data)
        grads /= (tf.sqrt(tf.reduce_mean(tf.square(grads))) + 1e-5)
        input_img_data.assign_add(grads * step)

    img = input_img_data.numpy()[0]
    return deprocess_image(img)

def main():
    model = VGG16(weights='imagenet',
                  include_top=False)
    base_dir = str(Path(__file__).parent.parent)
    visualize_all_patterns_vgg(model, base_dir + 'output/visualizing_patterns_output')

if __name__ == '__main__':
    os.environ["CUDA_VISIBLE_DEVICES"] = "0"
    main()
    print("completed")