"""Conv module.

- Author: Jongkuk Lim
- Contact: lim.jeikei@gmail.com
"""

from typing import Union

import torch
from torch import nn

from kindle.modules.activation import Activation
from kindle.utils.torch_utils import autopad


class Conv(nn.Module):
    """Standard convolution with batch normalization and activation.

    Arguments: [channel, kernel_size, stride, padding, groups, activation]
    """

    def __init__(
        self,
        in_channels: int,
        out_channels: int,
        kernel_size: int,
        stride: int = 1,
        padding: Union[int, None] = None,
        groups: int = 1,
        activation: Union[str, None] = "ReLU",
    ) -> None:
        """Standard convolution with batch normalization and activation.

        Args:
            in_channels: input channels.
            out_channels: output channels.
            kernel_size: kernel size.
            stride: stride.
            padding: input padding. If None is given, autopad is applied
                which is identical to padding='SAME' in TensorFlow.
            groups: group convolution.
            activation: activation name. If None is given, nn.Identity is applied
                which is no activation.
        """
        super().__init__()
        # error: Argument "padding" to "Conv2d" has incompatible type "Union[int, List[int]]";
        # expected "Union[int, Tuple[int, int]]"
        self.conv = nn.Conv2d(
            in_channels,
            out_channels,
            kernel_size,
            stride,
            padding=autopad((kernel_size, kernel_size), padding),  # type: ignore
            groups=groups,
            bias=False,
        )
        self.batch_norm = nn.BatchNorm2d(out_channels)
        self.activation = Activation(activation)()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward."""
        return self.activation(self.batch_norm(self.conv(x)))

    def fuseforward(self, x: torch.Tensor) -> torch.Tensor:
        """Fuse forward."""
        return self.activation(self.conv(x))


class Focus(Conv):
    """Focus module from YOLOv5.

    Arguments: [channel, kernel_size, stride, padding, groups, activation]
    """

    @classmethod
    def __reduce_focus(cls, x: torch.Tensor) -> torch.Tensor:
        """Run reduce image by half."""

        return torch.cat(
            [
                x[..., ::2, ::2],
                x[..., 1::2, ::2],
                x[..., ::2, 1::2],
                x[..., 1::2, 1::2],
            ],
            1,
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Reduce image size and run convolution."""
        return super().forward(self.__reduce_focus(x))

    def fuseforward(self, x: torch.Tensor) -> torch.Tensor:
        """Reduce image size and run convolution with batchnorm fused."""
        return super().fuseforward(self.__reduce_focus(x))
