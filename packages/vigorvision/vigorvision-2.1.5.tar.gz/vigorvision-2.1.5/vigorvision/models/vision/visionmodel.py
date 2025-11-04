import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.checkpoint import checkpoint
from vigorvision.nn.module.conv import ConvBlock
from vigorvision.nn.module.c3k2 import C3K2Block
from vigorvision.nn.module.c4k2 import C4K2Block
from vigorvision.nn.module.a2c2f import A2C2FBlock
from vigorvision.nn.module.vigorneck import VigorNeck
from vigorvision.nn.module.detectionhead import DetectionHead
from vigorvision.models.model_config import get_scaled_config as model_configs, model_variants


class VisionModel(nn.Module):
    def __init__(self, dataset, num_classes: int, variant: str = "vision-s", use_checkpoint=False):
        super(VisionModel, self).__init__()

        assert variant in model_variants, f"Unknown model variant: {variant}"
        self.config = model_configs(variant, dataset)
        self.num_classes = num_classes
        self.use_checkpoint = use_checkpoint

        self.backbone = self._build_backbone(self.config["backbone"])
        self.neck = VigorNeck([256, 512, 1024])
        self.head = DetectionHead(
            ch=[256, 512, 1024],
            nc=self.num_classes,
            anchors=self.config["head"]["anchors"],
            stride=self.config["head"]["strides"]
        )

        self.anchors = self.head.anchors
        self.stride = self.head.stride

        # We'll create projection convs lazily in forward and register them as attributes:
        self.proj3 = None
        self.proj4 = None
        self.proj5 = None

    def _build_backbone(self, cfg):
        layers = []
        for block_type, in_ch, out_ch, repeat, kwargs in cfg:
            for _ in range(repeat):
                if block_type == "conv":
                    layers.append(ConvBlock(in_ch, out_ch, **kwargs))
                elif block_type == "c3k2":
                    layers.append(C3K2Block(in_ch, out_ch, **kwargs))
                elif block_type == "c4k2":
                    layers.append(C4K2Block(in_ch, out_ch, **kwargs))
                elif block_type == "a2c2f":
                    layers.append(A2C2FBlock(in_ch, out_ch, **kwargs))
                else:
                    raise ValueError(f"Unsupported block: {block_type}")
                in_ch = out_ch
        return nn.Sequential(*layers)

    def _ensure_proj(self, name: str, in_ch: int, out_ch: int, device):
        """Create or recreate a 1x1 conv if missing or channel mismatch."""
        existing = getattr(self, name)
        if existing is None or (isinstance(existing, nn.Conv2d) and existing.in_channels != in_ch):
            conv = nn.Conv2d(in_ch, out_ch, kernel_size=1, bias=False).to(device)
            setattr(self, name, conv)
        return getattr(self, name)

    def forward(self, x, targets=None):
        feature_maps = []

        for layer in self.backbone:
            if self.use_checkpoint and layer.__class__.__name__ not in ("BatchNorm2d", "Identity"):
                x = checkpoint(layer, x)
            else:
                x = layer(x)
            feature_maps.append(x)

        # Fixed index-based selection for stability
        n = len(feature_maps)
        idx_c3, idx_c4, idx_c5 = max(0, n // 3), max(0, 2 * n // 3), n - 1
        c3, c4, c5 = feature_maps[idx_c3], feature_maps[idx_c4], feature_maps[idx_c5]

        device = c3.device
        if c3.shape[1] != 256:
            c3 = self._ensure_proj("proj3", c3.shape[1], 256, device)(c3)
        if c4.shape[1] != 512:
            c4 = self._ensure_proj("proj4", c4.shape[1], 512, device)(c4)
        if c5.shape[1] != 1024:
            c5 = self._ensure_proj("proj5", c5.shape[1], 1024, device)(c5)

        # Enforce scale ratios using adaptive pooling
        c4 = F.adaptive_avg_pool2d(c4, (c3.shape[2] // 2, c3.shape[3] // 2))
        c5 = F.adaptive_avg_pool2d(c5, (c4.shape[2] // 2, c4.shape[3] // 2))

        # Neck and Head
        p3, p4, p5 = self.neck(c3, c4, c5)

        if self.training:
            preds, loss = self.head([p3, p4, p5], targets)
            return preds, loss
        else:
            preds = self.head([p3, p4, p5])
            return preds
