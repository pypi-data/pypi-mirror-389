"""
Thin, explicit API with one function per explainer method.

Public functions exported:
- guided_backpropagation(model, inputs, target, *, channel=None, abs=False, **kwargs)
- smooth_grad_saliency(model, inputs, target, *, channel=None, abs=False, **kwargs)
- smooth_integrated_guided_back(model, inputs, target, *, channel=None, abs=False, **kwargs)
- fusion_grad(model, inputs, target, *, channel=None, abs=False, **kwargs)
- fusion_grad_integrated(model, inputs, target, *, channel=None, abs=False, **kwargs)

All functions:
- accept either np.ndarray or tf.Tensor for `inputs` (HWC / BHWC / BCHW)
- return np.ndarray with shape (B, C, H, W), dtype float32
- pass any extra **kwargs directly to the underlying explainer (e.g., sigma, n_samples...)

Usage example:

    from tf_xai_methods_api import guided_backpropagation, smooth_grad_saliency

    attr = guided_backpropagation(model, img_hwc, target=0, abs=True)
    attr2 = smooth_grad_saliency(model, img_hwc, target=1, n_samples=20, sigma=0.1)

"""
from __future__ import annotations

from typing import Any, Dict, Tuple, Callable, Optional
import numpy as np
import tensorflow as tf

from explainable_ai_tf.explanation_wrapper import make_explain_func

# ---------------------------------------------------------------------------
# Import the wrapper factory from your existing code.
# Replace this import path with the actual module where make_explain_func lives.
# Example: from explainers.wrapper import make_explain_func
# ---------------------------------------------------------------------------


# ----------------------- internal utils ------------------------------------

def _to_numpy(x: Any) -> np.ndarray:
    if isinstance(x, np.ndarray):
        return x
    if tf.is_tensor(x):
        return x.numpy()
    return np.asarray(x)


def _validate_model(model: tf.keras.Model) -> None:
    if not isinstance(model, tf.keras.Model):
        raise TypeError("`model` must be a tf.keras.Model.")


def _validate_target(target: Optional[int]) -> int:
    if target is None:
        raise ValueError("`target` is required.")
    try:
        return int(target)
    except Exception as e:
        raise TypeError("`target` must be an integer.") from e


# Cache: method_name -> (explain_func, explainer)
# make_explain_func(method) returns (fn, explainer)
_CACHE: Dict[str, Tuple[Callable[..., np.ndarray], Any]] = {}


def _get_fn(method: str) -> Callable[..., np.ndarray]:
    fn, _explainer = _CACHE.get(method, (None, None))  # type: ignore[assignment]
    if fn is None:
        fn, explainer = make_explain_func(method)
        _CACHE[method] = (fn, explainer)
    return fn


def _call(
    method: str,
    model: tf.keras.Model,
    inputs: Any,
    target: int,
    baselines: Any = None,
    **kwargs: Any,
) -> np.ndarray:
    """Internal unified call. Returns (B,C,H,W) float32."""
    _validate_model(model)
    tgt = _validate_target(target)
    x_np = _to_numpy(inputs)
    b_np = None if baselines is None else _to_numpy(baselines)

    fn = _get_fn(method)
    attributions = fn(model=model, inputs=x_np, targets=tgt, baselines=b_np, **kwargs)

    if not isinstance(attributions, np.ndarray):
        attributions = np.asarray(attributions)
    if attributions.ndim != 4:
        raise RuntimeError(
            f"Expected attributions with shape (B,C,H,W); got {attributions.shape}"
        )
    return attributions.astype(np.float32, copy=False)


# ----------------------- public functions ----------------------------------

def guided_backpropagation(
    model: tf.keras.Model,
    inputs: Any,
    target: int,
    *,
    channel: Optional[int] = None,
    abs: bool = False,
    baselines: Any = None,
    **kwargs: Any,
) -> np.ndarray:
    """Guided Backpropagation -> (B,C,H,W) float32.

    Parameters
    ----------
    model : tf.keras.Model
    inputs : array-like or tf.Tensor
        HWC / BHWC / BCHW supported by your wrapper.
    target : int
        Overlay/class index.
    channel : Optional[int]
        If provided, returns only that channel (C=1) from the explainer output.
    abs : bool
        If True, take absolute value of attributions (if supported by wrapper).
    baselines : Optional[array-like]
    **kwargs : Any
        Passed to underlying explainer (e.g., smoothing params).
    """
    return _call(
        "guided_backpropagation",
        model,
        inputs,
        target,
        baselines=baselines,
        channel=channel,
        abs=abs,
        **kwargs,
    )


def smooth_grad_saliency(
    model: tf.keras.Model,
    inputs: Any,
    target: int,
    *,
    channel: Optional[int] = None,
    abs: bool = False,
    baselines: Any = None,
    **kwargs: Any,
) -> np.ndarray:
    """
    SmoothGrad Saliency -> (B,C,H,W) float32.
    Parameters
    ----------
    model : tf.keras.Model
    inputs : array-like or tf.Tensor
        HWC / BHWC / BCHW supported by your wrapper.
    target : int
        Overlay/class index.
    channel : Optional[int]
        If provided, returns only that channel (C=1) from the explainer output.
    abs : bool
        If True, take absolute value of attributions (if supported by wrapper).
    baselines : Optional[array-like]
    **kwargs : Any
        Passed to underlying explainer (e.g., smoothing params).
    """
    return _call(
        "smooth_grad_saliency",
        model,
        inputs,
        target,
        baselines=baselines,
        channel=channel,
        abs=abs,
        **kwargs,
    )


def smooth_integrated_guided_back(
    model: tf.keras.Model,
    inputs: Any,
    target: int,
    *,
    channel: Optional[int] = None,
    abs: bool = False,
    baselines: Any = None,
    **kwargs: Any,
) -> np.ndarray:
    """
    Integrated Gradients + Guided Backprop (as named in your wrapper) -> (B,C,H,W).
    Parameters
    ----------
    model : tf.keras.Model
    inputs : array-like or tf.Tensor
        HWC / BHWC / BCHW supported by your wrapper.
    target : int
        Overlay/class index.
    channel : Optional[int]
        If provided, returns only that channel (C=1) from the explainer output.
    abs : bool
        If True, take absolute value of attributions (if supported by wrapper).
    baselines : Optional[array-like]
    **kwargs : Any
        Passed to underlying explainer (e.g., smoothing params).
    """
    return _call(
        "smooth_integrated_guided_back",
        model,
        inputs,
        target,
        baselines=baselines,
        channel=channel,
        abs=abs,
        **kwargs,
    )


def fusion_grad(
    model: tf.keras.Model,
    inputs: Any,
    target: int,
    *,
    channel: Optional[int] = None,
    abs: bool = False,
    baselines: Any = None,
    **kwargs: Any,
) -> np.ndarray:
    """
    FusionGrad -> (B,C,H,W) float32.
    Parameters
    ----------
    model : tf.keras.Model
    inputs : array-like or tf.Tensor
        HWC / BHWC / BCHW supported by your wrapper.
    target : int
        Overlay/class index.
    channel : Optional[int]
        If provided, returns only that channel (C=1) from the explainer output.
    abs : bool
        If True, take absolute value of attributions (if supported by wrapper).
    baselines : Optional[array-like]
    **kwargs : Any
        Passed to underlying explainer (e.g., smoothing params).
    """
    return _call(
        "fusion_grad",
        model,
        inputs,
        target,
        baselines=baselines,
        channel=channel,
        abs=abs,
        **kwargs,
    )


def fusion_grad_integrated(
    model: tf.keras.Model,
    inputs: Any,
    target: int,
    *,
    channel: Optional[int] = None,
    abs: bool = False,
    baselines: Any = None,
    **kwargs: Any,
) -> np.ndarray:
    """
    FusionGrad with Integrated Gradients -> (B,C,H,W) float32.
    Parameters
    ----------
    model : tf.keras.Model
    inputs : array-like or tf.Tensor
        HWC / BHWC / BCHW supported by your wrapper.
    target : int
        Overlay/class index.
    channel : Optional[int]
        If provided, returns only that channel (C=1) from the explainer output.
    abs : bool
        If True, take absolute value of attributions (if supported by wrapper).
    baselines : Optional[array-like]
    **kwargs : Any
        Passed to underlying explainer (e.g., smoothing params).
    """
    return _call(
        "fusion_grad_integrated",
        model,
        inputs,
        target,
        baselines=baselines,
        channel=channel,
        abs=abs,
        **kwargs,
    )


__all__ = [
    "guided_backpropagation",
    "smooth_grad_saliency",
    "smooth_integrated_guided_back",
    "fusion_grad",
    "fusion_grad_integrated",
]
