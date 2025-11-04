# vigorvision/nn/module/vigorneck.py

import torch
import torch.nn as nn
import torch.nn.functional as F
from .a2c2f import A2C2FBlock
from .c4k2 import C4K2Block
from .c3k2 import C3K2Block
from .seblock import SEBlock
from .custom_upsample import CustomUpsample  # Assuming you have this defined
from .conv import ConvBlock


class VigorNeck(nn.Module):
    """
    VigorNeck:
    - PANet style deep multi-scale feature aggregation
    - A2C2F + C4K2 + C3K2 modules for feature refinement
    - Smart upsample/downsample with SE
    - Self-adaptive 1x1 reducers to ensure channel compatibility
    """

    def __init__(self, channels_list, use_se=True, depthwise=False, dropout=0.0):
        """
        channels_list: List of [C3, C4, C5] channel sizes from backbone (expected canonical channels)
        """
        super(VigorNeck, self).__init__()

        assert len(channels_list) == 3, "channels_list must be [C3, C4, C5]"

        C3, C4, C5 = channels_list

        self.use_se = use_se

        # Reduce & refine top C5
        self.reduce_c5 = ConvBlock(C5, C4, kernel_size=1)
        self.a2c2f_c5 = A2C2FBlock(C4, C4, residual=True, use_se=use_se, depthwise=depthwise, dropout=dropout)

        # Upsample helpers
        self.upsample_c5 = CustomUpsample(C4, C4, scale=2, mode='nearest')
        # We'll reduce the concat (p5_up + c4) via a 1x1 conv to canonical C4 channels
        self.p4_reduce = ConvBlock(C4 + C4, C4, kernel_size=1)

        # c4_merge expects C4 input (after reduction)
        self.c4_merge = C3K2Block(C4, C4, residual=True, use_se=use_se, depthwise=depthwise, dropout=dropout)

        # Upsample & merge with C3. After c4_merge we upsample to match c3 spatially.
        self.upsample_c4 = CustomUpsample(C4, C3, scale=2, mode='nearest')
        # Reduce concat (p4_up + c3) -> canonical C4 channels before feeding C4K2Block
        self.p3_reduce = ConvBlock(C4 + C3, C4, kernel_size=1)

        # c3_merge now takes canonical C4 (reduced) and outputs C3 refined features
        self.c3_merge = C4K2Block(C4, C3, residual=True, use_se=use_se, depthwise=depthwise, dropout=dropout)

        # Bottom-Up Path: downsample p3 -> concat with p4 then reduce to canonical C4
        self.down_c3 = ConvBlock(C3, C4, kernel_size=3, stride=2)
        self.p4out_reduce = ConvBlock(C4 + C4, C4, kernel_size=1)
        self.c4_out = C3K2Block(C4, C4, residual=True, use_se=use_se, depthwise=depthwise, dropout=dropout)

        # Downsample p4_out -> concat with p5 then reduce to canonical C5
        self.down_c4 = ConvBlock(C4, C5, kernel_size=3, stride=2)
        self.p5out_reduce = ConvBlock(C5 + C4, C5, kernel_size=1)  # note ordering: we'll reduce (p4_down + p5) -> C5
        self.c5_out = C4K2Block(C5, C5, residual=True, use_se=use_se, depthwise=depthwise, dropout=dropout)

        # Final SE Attention on all outputs (applied to final shapes: C3, C4, C5)
        self.se_c3 = SEBlock(C3) if use_se else nn.Identity()
        self.se_c4 = SEBlock(C4) if use_se else nn.Identity()
        self.se_c5 = SEBlock(C5) if use_se else nn.Identity()

    def forward(self, c3, c4, c5):
        """
        Inputs:
            c3: large spatial, channels maybe != C3 (we expect caller already projected to C3)
            c4: mid spatial
            c5: small spatial
        Returns:
            p3 (C3), p4_out (C4), p5_out (C5)
        """

        # Top-Down Path
        p5 = self.reduce_c5(c5)           # C5 -> C4 channels
        p5 = self.a2c2f_c5(p5)            # refine
        p5_up = self.upsample_c5(p5)      # upsample to c4 spatial

        # concat and reduce for stable channel count
        p4_cat = torch.cat([p5_up, c4], dim=1)            # (C4 + C4)
        p4 = self.p4_reduce(p4_cat)                       # -> C4 canonical
        p4 = self.c4_merge(p4)                            # refine
        p4_up = self.upsample_c4(p4)                      # upsample to c3 spatial

        p3_cat = torch.cat([p4_up, c3], dim=1)            # (C4 + C3)
        p3_reduced = self.p3_reduce(p3_cat)               # -> C4 canonical
        p3 = self.c3_merge(p3_reduced)                    # outputs C3

        # Bottom-Up Path
        p3_down = self.down_c3(p3)                        # C3 -> C4 (spatial down)
        p4_cat_out = torch.cat([p3_down, p4], dim=1)      # (C4 + C4)
        p4_out_reduced = self.p4out_reduce(p4_cat_out)    # -> C4 canonical
        p4_out = self.c4_out(p4_out_reduced)              # finalized p4_out (C4)

        p4_down = self.down_c4(p4_out)                    # C4 -> C5 (spatial down)
        # concat p4_down (C5) and p5 (C4 after reduce->C4)? we reduced p5 earlier to C4,
        # ensure we concat in consistent channel ordering: (p4_down, p5) -> reduce to C5
        # p4_down currently has C5 channels (from down_c4), p5 has C4 channels (from earlier)
        p5_cat = torch.cat([p4_down, p5], dim=1)          # (C5 + C4)
        p5_out_reduced = self.p5out_reduce(p5_cat)        # -> C5 canonical
        p5_out = self.c5_out(p5_out_reduced)              # finalized p5_out (C5)

        # Final SE Attention
        return self.se_c3(p3), self.se_c4(p4_out), self.se_c5(p5_out)


def test_vigorneck():
    c3 = torch.randn(1, 256, 80, 80)
    c4 = torch.randn(1, 512, 40, 40)
    c5 = torch.randn(1, 1024, 20, 20)
    model = VigorNeck([256, 512, 1024], use_se=True, depthwise=False, dropout=0.1)
    p3, p4, p5 = model(c3, c4, c5)
    print(f"P3 shape: {p3.shape} | P4 shape: {p4.shape} | P5 shape: {p5.shape}")


if __name__ == "__main__":
    test_vigorneck()
