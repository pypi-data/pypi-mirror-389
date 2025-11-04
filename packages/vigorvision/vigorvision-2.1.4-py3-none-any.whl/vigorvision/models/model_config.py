# vigorvision/models/model_config.py
from vigorvision.utils import AutoAnchor as aa

"""
Unified model configuration for scalable Vision models.

Supports variants:
  - vision-n
  - vision-s
  - vision-m
  - vision-l
  - vision-x
"""

model_variants = {
    "vision-n": {"depth_mult": 0.33, "width_mult": 0.50, "base_channels": 32},
    "vision-s": {"depth_mult": 0.50, "width_mult": 0.75, "base_channels": 48},
    "vision-m": {"depth_mult": 0.75, "width_mult": 1.00, "base_channels": 64},
    "vision-l": {"depth_mult": 1.00, "width_mult": 1.00, "base_channels": 64},
    "vision-x": {"depth_mult": 1.33, "width_mult": 1.25, "base_channels": 80},
}


def make_divisible(x, divisor=8):
    """Ensures channel count is divisible by 8 for better efficiency."""
    return int((x + divisor / 2) // divisor * divisor)


def get_scaled_config(variant: str, dataset):
    assert variant in model_variants, f"Invalid model variant: {variant}"

    depth_mult = model_variants[variant]["depth_mult"]
    width_mult = model_variants[variant]["width_mult"]
    base = model_variants[variant]["base_channels"]

    def c(ch):  # Channel scaling
        return make_divisible(ch * width_mult)

    def d(n):  # Depth scaling
        return max(round(n * depth_mult), 1)

    # ----------------------------
    # BACKBONE (C4K2 removed)
    # ----------------------------
    backbone = [
        ("conv",  3, c(base), d(1), {"kernel_size": 3}),
        ("c3k2",  c(base), c(base * 2),  d(1), {"residual": True}),
        ("a2c2f", c(base * 2), c(base * 4),  d(1), {"residual": True}),
        ("a2c2f", c(base * 4), c(base * 8),  d(1), {"residual": True}),
        ("a2c2f", c(base * 8), c(base * 16), d(1), {"residual": True}),
        ("a2c2f", c(base * 16), c(base * 32), d(1), {"residual": True}),
    ]

    # ----------------------------
    # NECK & HEAD
    # ----------------------------
    neck_channels = [c(base * 8), c(base * 16), c(base * 32)]

    head_cfg = {
        "anchors": [
            [(10, 13), (16, 30), (33, 23)],
            [(30, 61), (62, 45), (59, 119)],
            [(116, 90), (156, 198), (373, 326)],
        ],
        "strides": [8, 16, 32],  # kept for compatibility but not used directly
    }

    return {
        "backbone": backbone,
        "neck_channels": neck_channels,
        "head": head_cfg,
    }


def model_configs(variant: str, dataset: str):
    """Return model config dict for the specified variant and dataset."""
    return get_scaled_config(variant, dataset)
