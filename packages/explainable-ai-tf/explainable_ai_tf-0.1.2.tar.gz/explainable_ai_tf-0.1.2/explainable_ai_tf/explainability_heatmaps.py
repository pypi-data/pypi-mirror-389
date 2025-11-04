import os
import numpy as np
import pandas as pd

from explainable_ai_tf.common import save_image, plot_stack
from explainable_ai_tf.fusion_grad.fusion_grad import FusionGrad
from explainable_ai_tf.guided_backpropagation import GuidedBackpropagation
from explainable_ai_tf.smooth_grad.smooth_grad import SmoothGrad
# If you prefer your own Excel writer, you can keep the local helper below
# from explainable_ai.metrics.save_result import save_channel_results_to_excel


# --------- Small utility: write channel results to a tidy Excel ----------
def save_channel_results_to_excel(channel_results: dict, out_path: str):
    """
    channel_results example:
      {
        "smooth_grad_saliency": {
            "Complexity": {"Sparseness": 0.02, "Complexity": 11.97},
            "Randomisation": {"ModelParameterRandomisation": 0.17}
        },
        "guided_backpropagation": {
            "Complexity": {"Sparseness": 0.06, "Complexity": 11.96},
            "Randomisation": {"ModelParameterRandomisation": 0.03}
        },
      }
    """
    rows = {}
    for method, categories in channel_results.items():
        flat = {}
        for cat, metrics in categories.items():
            for mname, val in metrics.items():
                flat[f"{cat}.{mname}"] = float(val)
        rows[method] = flat

    df = pd.DataFrame.from_dict(rows, orient="index").sort_index()
    df.index.name = "xai_method"

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    df.to_excel(out_path, sheet_name="scores")


# --------- Main entrypoint ----------
def generate_explainability_heatmaps(
    model,
    image,
    overlay_index,
    base_dir,
    out_folder,
    top_left=None,
    bottom_right=None,
):
    """
    Generates XAI heatmaps with multiple methods and evaluates them.

    Inputs
    ------
    model: a TF/Keras model
    image: np.ndarray
        Expected HWC (H, W, C). If you pass BHWC or BCHW, we will normalize to HWC.
    overlay_index: label / scalar target (whatever your evaluate() expects)
    base_dir: str
    out_folder: str
        Directory layout will be method-first like version-2:
            {base_dir}/{out_folder}/{method}/{heatmap|stacked_heatmap}/channel_{i}.tif
        Metrics (Excel) are saved per-channel at:
            {base_dir}/{out_folder}/metrics/channel_{i}.xlsx
    """

    # ---- Normalize paths (avoid leading slashes that override base_dir) ----
    out_folder = (out_folder or "").strip().lstrip("/\\")
    root = os.path.join(base_dir, out_folder)
    os.makedirs(root, exist_ok=True)
    print(f"[XAI] Writing outputs under: {root}")

    # ---- Normalize image to HWC ----
    img = np.asarray(image)
    if img.ndim == 4:
        # Assume BHWC or BCHW and take the first item in the batch
        if img.shape[1] in (1, 2, 3, 4) and img.shape[-1] not in (1, 2, 3, 4):
            # Likely BCHW -> to HWC
            img = np.transpose(img[0], (1, 2, 0))
        else:
            # Likely BHWC -> take first
            img = img[0]
    elif img.ndim != 3:
        raise ValueError(f"Expected image with 3 dims (HWC) or 4 dims (BH?C?), got shape {img.shape}")

    H, W, C = img.shape
    if C < 1:
        raise ValueError("Image must have at least one channel (C >= 1).")

    # ---- Compute all heatmaps (same as v1 logic) ----
    smooth_integrated_guided_heatmaps = SmoothGrad.smooth_grad_integrated_gradients_guided(
        model=model, images=img, predicted_overlay_index=overlay_index
    )
    guided_heatmaps = GuidedBackpropagation.guided_backpropagation(
        model=model, images=np.expand_dims(img, axis=0), predicted_overlay_index=overlay_index
    )
    smooth_saliency_heatmaps = SmoothGrad.smooth_grad_saliency(
        model=model, images=img, predicted_overlay_index=overlay_index
    )
    fusiongrad_heatmaps = FusionGrad.fusion_grad(
        model=model, images=img, predicted_overlay_index=overlay_index
    )
    fusiongrad_integrated_heatmaps = FusionGrad.fusion_grad_integrated_gradients(
        model=model, images=img, predicted_overlay_index=overlay_index
    )

    explainability_methods = {
        "smooth_grad_saliency":          smooth_saliency_heatmaps,
        "smooth_integrated_guided_back": smooth_integrated_guided_heatmaps,
        "guided_backpropagation":        guided_heatmaps,
        "fusion_grad":                   fusiongrad_heatmaps,
        "fusion_grad_integrated":        fusiongrad_integrated_heatmaps,
    }

    # ---- Ensure method-first folders exist (like version-2) ----
    for method_name in explainability_methods.keys():
        for sub in ("heatmap", "stacked_heatmap"):
            os.makedirs(os.path.join(root, method_name, sub), exist_ok=True)
    os.makedirs(os.path.join(root, "metrics"), exist_ok=True)

    # ---- Per-channel loop (like version-1 logic) ----
    for i in range(C):
        eval_results_for_channel = {}

        for method_name, heatmaps in explainability_methods.items():
            heatmap = heatmaps[i]

            # Save heatmap (method-first layout + channel_{i}.tif)
            heatmap_path = os.path.join(root, method_name, "heatmap", f"channel_{i}.tif")
            save_image(
                heatmap,
                heatmap_path,
                title=f'{method_name} heatmap - Channel {i}',
                draw_rect=False,
                top_left=top_left,
                bottom_right=bottom_right,
            )

            # Save stacked (original single-channel + its heatmap)
            stacked_path = os.path.join(root, method_name, "stacked_heatmap", f"channel_{i}.tif")
            plot_stack(
                img[..., i],
                heatmap,
                stacked_path,
                title=f'{method_name}, Stacked Heatmap - Channel {i}',
            )


        # One Excel per channel (v1 behavior), but stored in a method-agnostic metrics folder
        excel_path = os.path.join(root, "metrics", f"fp_channel_{i}.xlsx")
        save_channel_results_to_excel(eval_results_for_channel, excel_path)
        print(f"[XAI] Saved metrics: {excel_path}")
    print(f"[XAI] Done. Outputs are under: {root}")