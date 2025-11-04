import numpy as np
import pytest
import tensorflow as tf

explainable_ai = pytest.importorskip("explainable_ai", reason="requires explainable_ai package available")

# The API module created earlier; ensure it's importable via PYTHONPATH or colocated.
import explainable_ai_tf.tf_xai_methods_api as api


# ==========================
# Fixtures: tiny real model & inputs
# ==========================

@pytest.fixture(scope="module")
def rng():
    return np.random.default_rng(0)


@pytest.fixture(scope="module")
def tiny_model():
    # Small CNN with ReLU (supports guided backprop etc.)
    inp = tf.keras.Input(shape=(8, 8, 3))
    x = tf.keras.layers.Conv2D(4, 3, padding="same", activation="relu")(inp)
    x = tf.keras.layers.Conv2D(4, 3, padding="same", activation="relu")(x)
    x = tf.keras.layers.GlobalAveragePooling2D()(x)
    out = tf.keras.layers.Dense(5)(x)  # logits for 5 classes
    model = tf.keras.Model(inp, out)
    return model


@pytest.fixture()
def img_hwc(rng):
    # Single image HWC
    x = rng.random((8, 8, 3), dtype=np.float32)
    return x.astype(np.float32)


@pytest.fixture()
def batch_bhwc(rng):
    x = rng.random((2, 8, 8, 3), dtype=np.float32)
    return x.astype(np.float32)


@pytest.fixture()
def batch_bchw(rng):
    x = rng.random((2, 3, 8, 8), dtype=np.float32)
    return x.astype(np.float32)


# ==========================
# Core shape/dtype tests (no monkeypatches)
# ==========================

@pytest.mark.parametrize("func", [
    api.guided_backpropagation,
    api.smooth_grad_saliency,
    api.smooth_integrated_guided_back,
    api.fusion_grad,
    api.fusion_grad_integrated,
])
def test_single_image_hwc_to_bchw(func, tiny_model, img_hwc):
    out = func(tiny_model, img_hwc, target=0)
    assert isinstance(out, np.ndarray)
    assert out.dtype == np.float32
    assert out.ndim == 4 and out.shape[0] == 1 and out.shape[2:] == (8, 8)
    # Channels should be positive
    assert out.shape[1] >= 1
    # Finite
    assert np.isfinite(out).all()


@pytest.mark.parametrize("func", [
    api.guided_backpropagation,
    api.smooth_grad_saliency,
    api.smooth_integrated_guided_back,
    api.fusion_grad,
    api.fusion_grad_integrated,
])
def test_batch_bhwc(func, tiny_model, batch_bhwc):
    out = func(tiny_model, batch_bhwc, target=1)
    assert out.shape[0] == 2 and out.shape[2:] == (8, 8)
    assert out.dtype == np.float32
    assert np.isfinite(out).all()


@pytest.mark.parametrize("func", [
    api.guided_backpropagation,
    api.smooth_grad_saliency,
    api.smooth_integrated_guided_back,
    api.fusion_grad,
    api.fusion_grad_integrated,
])
def test_batch_bchw_input_path(func, tiny_model, batch_bchw):
    out = func(tiny_model, batch_bchw, target=2)
    assert out.shape[0] == 2 and out.shape[2:] == (8, 8)
    assert out.dtype == np.float32


def test_channel_reduction_and_abs(tiny_model, img_hwc):
    # channel selects a single channel (C=1); abs enforces non-negativity
    out = api.guided_backpropagation(tiny_model, img_hwc, target=3, channel=0, abs=True)
    assert out.shape == (1, 1, 8, 8)
    assert (out >= 0).all()


def test_tensor_inputs_supported(tiny_model, img_hwc):
    x_tensor = tf.convert_to_tensor(img_hwc)
    out = api.smooth_grad_saliency(tiny_model, x_tensor, target=4)
    assert out.shape[0] == 1 and out.shape[2:] == (8, 8)


@pytest.mark.parametrize("func,target", [
    (api.guided_backpropagation, 0),
    (api.smooth_grad_saliency, 1),
    (api.smooth_integrated_guided_back, 2),
    (api.fusion_grad, 3),
    (api.fusion_grad_integrated, 4),
])
def test_values_change_with_target(func, tiny_model, img_hwc, target):
    # Sanity: different targets can lead to different maps (not strictly guaranteed,
    # but often true). We'll just ensure call succeeds and produces finite outputs.
    out = func(tiny_model, img_hwc, target=target)
    assert np.isfinite(out).all()


def test_baselines_optional(tiny_model, img_hwc):
    # Ensure passing baselines doesn't crash even if the method ignores it
    baselines = np.zeros_like(img_hwc)
    out = api.fusion_grad_integrated(tiny_model, img_hwc, target=1, baselines=baselines)
    assert out.shape[0] == 1
