import numpy as np
import tensorflow as tf

from explainable_ai_tf.guided_backpropagation import GuidedBackpropagation
from explainable_ai_tf.smooth_grad.smooth_grad import SmoothGrad
from explainable_ai_tf.fusion_grad.fusion_grad import FusionGrad

# ---------- helpers ----------

def _to_bhwc(x: np.ndarray) -> np.ndarray:
    # Accept HWC or BHWC or BCHW and convert to BHWC
    x = np.asarray(x)
    if x.ndim == 3:  # HWC
        x = np.expand_dims(x, axis=0)
    elif x.ndim == 4:
        if x.shape[-1] in (1, 2, 3, 4):
            pass  # already BHWC
        elif x.shape[1] in (1, 2, 3, 4):
            x = np.transpose(x, (0, 2, 3, 1))  # BCHW -> BHWC
    else:
        raise ValueError(f"inputs must be HWC or BHWC/BCHW; got {x.shape}")
    print("Wrapper sees:", x.shape)
    return x.astype(np.float32)


def _per_channel_list_to_hwc(heatmaps_per_channel):
    # Convert list/tuple of 2D maps or (C,H,W) into (H,W,C)
    a = np.asarray(heatmaps_per_channel)
    if isinstance(heatmaps_per_channel, (list, tuple)):
        chans = [np.asarray(hm)[..., None] for hm in heatmaps_per_channel]
        return np.concatenate(chans, axis=-1)
    if a.ndim == 3 and a.shape[0] in (1, 2, 3, 4):
        return np.transpose(a, (1, 2, 0))
    if a.ndim == 3 and a.shape[-1] in (1, 2, 3, 4):
        return a
    raise ValueError(f"Unexpected attribution shape: {a.shape}")


def _apply_abs(a: np.ndarray, use_abs: bool) -> np.ndarray:
    return np.abs(a) if use_abs else a


def _sanitize_kwargs(d):
    # Remove keys Quantus may inject that would collide with explicit args
    d = dict(d or {})
    for k in (
        "model", "device", "channel_first", "explain_func",
        "explain_func_kwargs", "return_numpy", "batch_size"
    ):
        d.pop(k, None)
    return d


# ---------- strict method names (NO aliases, NO normalization) ----------

ALLOWED_METHODS = {
    "smooth_grad_saliency",
    "smooth_integrated_guided_back",
    "guided_backpropagation",
    "fusion_grad",
    "fusion_grad_integrated",
}


# ---------- Captum-like adapter (model passed per call) ----------

class CaptumLikeExplainer:
    """
    Exposes a Captum-style .attribute(...) over your TF explainers.
    IMPORTANT: does NOT store a model; you must pass the model on each call.

    Supported method names (strict, case-sensitive):
      - "smooth_grad_saliency"
      - "smooth_integrated_guided_back"
      - "guided_backpropagation"
      - "fusion_grad"
      - "fusion_grad_integrated"

    Returns attributions as BCHW np.float32.
    """

    def __init__(self, method: str = "guided_backpropagation"):
        # Strict check: method must be exactly one of ALLOWED_METHODS
        if method not in ALLOWED_METHODS:
            raise ValueError(
                f"Unknown method '{method}'. Use one of: {sorted(ALLOWED_METHODS)}"
            )
        self.method = method

    def attribute(
        self,
        model: tf.keras.Model, # type: ignore
        inputs,
        target: int,
        baselines=None,
        abs: bool = False,
        return_convergence_delta: bool = False,
        **kwargs,
    ):
        # Pull and sanitize kwargs; `channel` is our per-channel switch
        channel = kwargs.pop("channel", None)
        kwargs = _sanitize_kwargs(kwargs)

        x_bhwc = _to_bhwc(inputs)  # BHWC
        b, h, w, c = x_bhwc.shape

        if channel is not None:
            # Normalize negative indices and validate
            if not isinstance(channel, (int, np.integer)):
                raise TypeError("`channel` must be an integer.")
            if channel < 0:
                channel = c + int(channel)
            if not (0 <= int(channel) < c):
                raise ValueError(f"`channel` out of range: {channel} for C={c}")

        batch_attrs = []
        for i in range(b):
            x_hwc = x_bhwc[i]

            if self.method == "guided_backpropagation":
                hmaps = GuidedBackpropagation.guided_backpropagation(
                    model=model,
                    images=np.expand_dims(x_hwc, axis=0),
                    predicted_overlay_index=target,
                )
                attr_hwc = _per_channel_list_to_hwc(hmaps)

            elif self.method == "smooth_grad_saliency":
                hmaps = SmoothGrad.smooth_grad_saliency(
                    model=model,
                    images=x_hwc,
                    predicted_overlay_index=target,
                    **kwargs,
                )
                attr_hwc = _per_channel_list_to_hwc(hmaps)

            elif self.method == "smooth_integrated_guided_back":
                # Integrated Gradients + Guided Backprop (your naming)
                hmaps = SmoothGrad.smooth_grad_integrated_gradients_guided(
                    model=model,
                    images=x_hwc,
                    predicted_overlay_index=target,
                    **kwargs,
                )
                attr_hwc = _per_channel_list_to_hwc(hmaps)

            elif self.method == "fusion_grad":
                hmaps = FusionGrad.fusion_grad(
                    model=model,
                    images=x_hwc,
                    predicted_overlay_index=target,
                    **kwargs,
                )
                attr_hwc = _per_channel_list_to_hwc(hmaps)

            elif self.method == "fusion_grad_integrated":
                hmaps = FusionGrad.fusion_grad_integrated_gradients(
                    model=model,
                    images=x_hwc,
                    predicted_overlay_index=target,
                    **kwargs,
                )
                attr_hwc = _per_channel_list_to_hwc(hmaps)

            else:
                # Unreachable due to strict check in __init__
                raise RuntimeError(f"Unsupported method {self.method}")

            # If a specific channel was requested, keep shape (H,W,1)
            if channel is not None:
                attr_hwc = attr_hwc[..., int(channel)][..., None]

            attr_hwc = _apply_abs(attr_hwc.astype(np.float32), abs)
            attr_chw = np.transpose(attr_hwc, (2, 0, 1))  # HWC -> CHW
            batch_attrs.append(attr_chw[None, ...])       # -> BCHW

        attributions_bchw = np.concatenate(batch_attrs, axis=0)
        return attributions_bchw


def make_explain_func(method: str):
    """
    Returns a callable with signature:
      explain_func(model, inputs, targets=None, baselines=None, **kwargs) -> attributions (B,C,H,W)

    The `method` must be EXACTLY one of (strict, case-sensitive):
      "smooth_grad_saliency", "smooth_integrated_guided_back",
      "guided_backpropagation", "fusion_grad", "fusion_grad_integrated"

    Supports `channel` kwarg to return only that channel (C=1).
    """
    explainer = CaptumLikeExplainer(method=method)

    def _fn(model, inputs, targets=None, baselines=None, **kwargs):
        if targets is None:
            raise ValueError("targets (overlay/class index) is required.")
        if np.isscalar(targets):
            tgt = int(targets)
        else:
            tgt = int(np.asarray(targets).ravel()[0])
        return explainer.attribute(
            model=model,
            inputs=inputs,
            target=tgt,
            baselines=baselines,
            **kwargs,
        )

    return _fn, explainer
