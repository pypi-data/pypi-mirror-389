import os

import numpy as np
import matplotlib.pyplot as plt
from tensorflow.keras.layers import Conv2D
from tensorflow.keras import models
from explainable_ai_tf.common import save_image, _normalize_image, deprocess_image
import tensorflow as tf


def plot_min_max_channels(model, activation, out_folder, ovl_index):
    dense_layer = model.get_layer("dense")
    weights_dense = dense_layer.get_weights()[0]  # Shape: (256, 2)
    min_index = np.argmin(weights_dense[:, ovl_index])  # Min in column ovl index
    max_index = np.argmax(weights_dense[:, ovl_index])  # Max in column ovl index
    indices = [min_index, max_index]
    for index in indices:
        filter_data = activation[0, :, :, index]  # Extract filter i.e:(25, 25)
        filter_data_normalized = _normalize_image(filter_data)
        image_title = f"channel_{index}_weight_{weights_dense[index, ovl_index]:.4f}"
        file_path = out_folder + f"/last_layer_min_max_filters/{image_title}.tiff"
        save_image(filter_data_normalized, file_path, image_title, 'gray')


def save_dense_weights(model, layer_name, filter_indices, out_folder):
    """
    תציג את המשקלים של שכבה Dense.
    """
    layer = model.get_layer(layer_name)
    weights = layer.get_weights()[0]  # מטריצת המשקלים
    print(f"Weight matrix shape: {weights.shape}")

    line_colors = ['tab:blue', 'tab:orange', 'tab:green', 'tab:red', 'tab:purple', 'tab:brown', 'tab:pink', 'tab:gray',
                   'tab:olive', 'tab:cyan']
    scatter_colors = ['blue', 'red', 'green', 'red', 'purple', 'brown', 'pink', 'gray', 'olive', 'cyan']

    plt.figure(figsize=(10, 6))
    for i in range(weights.shape[1]):  # עבור כל נוירון
        color_line = line_colors[i % len(line_colors)]
        color_scatter = scatter_colors[i % len(scatter_colors)]
        plt.plot(weights[:, i], label=f'Neuron {i + 1}', color=color_line)

        # הדגשה של פילטרים ספציפיים
        for idx in filter_indices:
            if idx < weights.shape[0]:  # בדוק אם האינדקס חוקי
                weight_value = weights[idx, i]
                plt.scatter(idx, weight_value, c=color_scatter, zorder=5)
                plt.text(idx + 0.1, weight_value, f'{weight_value:.4f}', color=color_scatter, fontsize=8)

    plt.title('Dense Layer Weights per Channel')
    plt.xlabel('Channel Index')
    plt.ylabel('Weight Value')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(out_folder + 'dense_weights.tiff', bbox_inches='tight')
    plt.close()


def save_conv_feature_map(feature_map, layer_name, out_folder):
    full_layer_name = f'{layer_name}_feature_map.tiff'
    # Ensure the directory exists
    file_path = out_folder + full_layer_name
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)

    # Create the plot
    plt.figure(figsize=(10, 8))  # Adjust the figure size to better fit the image
    plt.imshow(feature_map, cmap='gray', vmin=feature_map.min(), vmax=feature_map.max())
    plt.title(full_layer_name)
    plt.axis('off')  # Turn off the axis

    # Save the image
    plt.savefig(file_path, bbox_inches='tight', pad_inches=0.0)
    plt.close()


def save_filters(filters_list, layer_names, layers_to_save, out_folder):
    for layer in layers_to_save:
        full_layer_name = f'layer_{layer}_{layer_names[layer]}.tiff'
        # Ensure the directory exists
        file_path = out_folder + full_layer_name
        directory = os.path.dirname(file_path)
        if not os.path.exists(directory):
            os.makedirs(directory)

        # Create the plot
        plt.figure(figsize=(10, 8))  # Adjust the figure size to better fit the image
        plt.imshow(filters_list[layer], cmap='gray', vmin=filters_list[layer].min(), vmax=filters_list[layer].max())
        plt.title(full_layer_name)
        plt.axis('off')  # Turn off the axis

        # Save the image
        plt.savefig(file_path, bbox_inches='tight', pad_inches=0.0)
        plt.close()


def save_image_with_labels(image_to_save, file_path, filter_size, title='Heatmap', cmap='gray'):
    # Ensure the directory exists
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)

    fig, ax = plt.subplots(figsize=(20, 20))  # Increase figure size for better clarity
    img = ax.imshow(image_to_save, cmap=cmap)
    ax.set_title(title)

    # # Add channel labels at the top
    # n_rows, n_cols = image_to_save.shape
    # n_channels = n_cols // (filter_size + 1)  # +1 for padding
    # for j in range(n_channels+1):
    #     x = j * (filter_size + 1) + filter_size / 2
    #     ax.text(x, -2, f"C{j}", ha='center', va='bottom', fontsize=6, rotation=90)
    #
    # # Add filter labels on the left
    # n_rows, n_cols = image_to_save.shape
    # n_filters = n_rows // (filter_size + 1)  # +1 for padding
    # for i in range(n_filters+1):
    #     y = i * (filter_size + 1) + filter_size / 2
    #     ax.text(-2, y, f"F{i+1}", ha='right', va='center', fontsize=6)

    ax.axis('off')
    plt.savefig(file_path, bbox_inches='tight')
    plt.close()


def print_feature_map_and_filters_of_conv_layer(model, image, feature_map_out_folder):
    feature_map_out_folder += '/conv_layers/'
    # Create a model that outputs the activations of all layers
    layer_outputs = [layer.output for layer in model.layers]
    activation_model = models.Model(inputs=model.input, outputs=layer_outputs)

    # Get the activations
    activations = activation_model.predict(np.expand_dims(image, axis=0))

    # Visualize the activations
    layer_names = []
    for layer in model.layers:
        layer_names.append(layer.name)

    images_per_row = 16
    all_grids = []
    for layer_name, layer_activation, layer in zip(layer_names, activations, model.layers):
        print(f"Layer: {layer_name}")
        print(f"Activation shape: {layer_activation.shape}")

        if isinstance(layer, Conv2D):  # Check if the layer is a convolutional layer
            # Save the filters (kernels) of the convolutional layer
            filters = layer.weights[0].numpy()
            n_filters = filters.shape[-1]
            filter_size = filters.shape[0]
            if filter_size == 1:
                continue  # we skip 1x1 conv layers
            padding = 1  # 1 pixel padding between filters and channels
            filters_per_row = 16

            # Calculate number of rows needed
            n_rows = int(np.ceil(n_filters / filters_per_row))

            # Calculate grid size with padding
            grid_height = n_rows * filter_size + (n_rows - 1) * padding
            grid_width = filters_per_row * filter_size + (filters_per_row - 1) * padding
            filter_grid = np.ones((grid_height, grid_width)) * np.nan  # Use NaN for padding visualization

            for idx in range(n_filters):
                row = idx // filters_per_row
                col = idx % filters_per_row
                filter_image = filters[:, :, 0, idx]  # First channel only
                filter_image = _normalize_image(filter_image)
                row_start = row * (filter_size + padding)
                col_start = col * (filter_size + padding)
                filter_grid[row_start:row_start + filter_size, col_start:col_start + filter_size] = filter_image

            # Save the filter grid
            save_image_with_labels(filter_grid, feature_map_out_folder + f"{layer_name}_filters.tiff",
                                   filter_size=filter_size, title=f"Filters - {layer_name}", cmap='gray')

            # Plot the feature maps
            n_channels = layer_activation.shape[-1]
            # The feature map has shape (1, size, size, n_features)
            size = layer_activation.shape[1]
            # We will tile the activation channels in this matrix
            n_rows = int(np.ceil(n_channels / images_per_row))

            padding = 2  # 1 pixel black padding
            grid_height = n_rows * size + (n_rows - 1) * padding
            grid_width = images_per_row * size + (images_per_row - 1) * padding
            display_grid = np.ones((grid_height, grid_width), dtype=np.uint8) * 255  # white background

            for row in range(n_rows):
                for col in range(images_per_row):
                    channel_index = row * images_per_row + col
                    if channel_index >= n_channels:
                        break
                    channel_image = layer_activation[0, :, :, channel_index]
                    channel_image = _normalize_image(channel_image)

                    row_start = row * (size + padding)
                    col_start = col * (size + padding)
                    display_grid[row_start:row_start + size, col_start:col_start + size] = channel_image

            all_grids.append(display_grid)
            # Save the feature map grid
            save_conv_feature_map(display_grid, layer_name, feature_map_out_folder)

        else:
            print("layer is not a conv, skipping visualization")


def print_activation_per_layer(model, image, filters_out_folder, overlay_index):
    # Create a model that outputs the activations of all layers
    layer_outputs = [layer.output for layer in model.layers]
    activation_model = models.Model(inputs=model.input, outputs=layer_outputs)

    # Get the activations
    activations = activation_model.predict(np.expand_dims(image, axis=0))

    # Visualize the activations
    layer_names = []
    for layer in model.layers:
        layer_names.append(layer.name)

    images_per_row = 16
    all_grids = []
    for layer_name, layer_activation in zip(layer_names, activations):
        print(f"Layer: {layer_name}")
        print(f"Activation shape: {layer_activation.shape}")

        if len(layer_activation.shape) == 4:
            # Plot the activations
            n_channels = layer_activation.shape[-1]
            # The feature map has shape (1, size, size, n_features)
            size = layer_activation.shape[1]
            # We will tile the activation channels in this matrix
            n_rows = int(np.ceil(n_channels / images_per_row))
            display_grid = np.zeros((size * n_rows, images_per_row * size))

            for row in range(n_rows):
                for col in range(images_per_row):
                    channel_index = row * images_per_row + col
                    if channel_index >= n_channels:
                        break
                    channel_image = layer_activation[0, :, :, channel_index]
                    channel_image = _normalize_image(channel_image)

                    display_grid[row * size: (row + 1) * size, col * size: (col + 1) * size] = channel_image
            all_grids.append(display_grid)

            # scale = 1. / size
            # plt.figure(figsize=(scale * display_grid.shape[1], scale * display_grid.shape[0]))
            # plt.title(layer_name)
            # plt.grid(False)
            # plt.imshow(display_grid, aspect='auto', cmap='viridis')
        else:
            print("Activation is not a 4D tensor, skipping visualization")

    layers_to_save = [0, 1, 2, 34, 35, 36, 37]

    out_folder = filters_out_folder + '/filters/'
    save_filters(all_grids, layer_names, layers_to_save, out_folder)
    # find nan channels
    nan_mask = np.any(np.isnan(activations[37]), axis=(1, 2))  # Check along height and width
    nan_channels_indices = np.where(nan_mask.flatten())[0]  # Get indices of channels with NaNs
    save_dense_weights(model, 'dense', list(nan_channels_indices), out_folder)
    plot_min_max_channels(model, activations[37], out_folder, ovl_index=overlay_index)


def generate_pattern(model, layer_name, filter_index, size):
    # Build a loss function that maximizes the activation
    # of the nth filter of the layer considered.
    layer = model.get_layer(name=layer_name)
    # create a sub-model that outputs the feature map of the specified layer
    sub_model = tf.keras.Model(inputs=model.inputs, outputs=layer.output)

    # Start from a random image
    input_img_data = tf.random.uniform((1, size, size, model.input_shape[-1])) * 20 + 128

    step = 1.0
    for i in range(40):
        with tf.GradientTape() as tape:
            tape.watch(input_img_data)
            activations = sub_model(input_img_data)
            loss = tf.reduce_mean(activations[:, :, :, filter_index])
        grads = tape.gradient(loss, input_img_data)
        # Normalize gradients
        grads /= (tf.sqrt(tf.reduce_mean(tf.square(grads))) + 1e-5)
        input_img_data += grads * step

    img = input_img_data.numpy()[0]
    return deprocess_image(img)


def visualize_all_patterns(model, out_folder, margin=15, channel_margin=5):
    height, width, channels = model.input_shape[1:]
    size = height  # assuming square input
    for layer in model.layers:
        if isinstance(layer, Conv2D) and layer.weights[0].shape[:2] != (1, 1):  # Skip 1x1 conv layers
            layer_name = layer.name

            n_filters = layer.filters
            n_cols = int(np.sqrt(n_filters))
            n_rows = int(np.ceil(n_filters / n_cols))

            filter_height = height
            filter_width = channels * width + (channels - 1) * channel_margin

            results = np.ones((n_rows * filter_height + (n_rows - 1) * margin,
                               n_cols * filter_width + (n_cols - 1) * margin))

            for filter_index in range(n_filters):
                filter_img = generate_pattern(model, layer_name, filter_index, size=size)

                row = filter_index // n_cols
                col = filter_index % n_cols
                h_start = row * filter_height + row * margin
                h_end = h_start + filter_height
                v_start = col * filter_width + col * margin
                v_end = v_start + filter_width

                # Create horizontal strip with white margins between channels
                strip = np.ones((size, filter_width))
                for c in range(channels):
                    ch_start = c * size + c * channel_margin
                    ch_end = ch_start + size
                    strip[:, ch_start:ch_end] = filter_img[:, :, c]

                results[h_start:h_end, v_start:v_end] = strip

            save_image(results, out_folder + f"/conv_layers/patterns/{layer_name}_patterns.tiff", title=f"Patterns for {layer_name} per filter",
                       cmap='gray', print_colorbar=False)
