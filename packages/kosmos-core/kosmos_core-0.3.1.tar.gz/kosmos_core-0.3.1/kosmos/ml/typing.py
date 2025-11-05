from collections.abc import Callable

import torch

type TensorMapping = Callable[[torch.Tensor], torch.Tensor]
