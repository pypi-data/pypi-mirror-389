from quantus import AUC


def compute_auc_scores(explainability_method_output, model, baseline, inputs, overlay_index):
    """
    Computes AUC Insertion and Deletion scores for a given explainability method output.

    Args:
        explainability_method_output (np.ndarray): Heatmap or saliency map from the explainability method.
        model (tf.keras.Model): The model being explained.
        baseline (np.ndarray): Baseline image (e.g., black image or blurred image).
        inputs (np.ndarray): Original input image.
        overlay_index (int): Index of the overlay being explained.

    Returns:
        dict: A dictionary containing AUC Insertion and Deletion scores.
    """
    # Define the AUC metric for insertion and deletion
    auc_insertion = AUC(metric="insertion", steps=100)
    auc_deletion = AUC(metric="deletion", steps=100)

    # Compute the scores
    insertion_score = auc_insertion(
        model=model,
        attributions=explainability_method_output,
        inputs=inputs,
        targets=overlay_index,
        baselines=baseline
    )

    deletion_score = auc_deletion(
        model=model,
        attributions=explainability_method_output,
        inputs=inputs,
        targets=overlay_index,
        baselines=baseline
    )

    return {
        "AUC Insertion": insertion_score,
        "AUC Deletion": deletion_score
    }