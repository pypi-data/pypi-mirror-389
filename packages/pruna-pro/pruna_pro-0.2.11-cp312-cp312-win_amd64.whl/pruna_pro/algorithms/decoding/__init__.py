from pruna.algorithms.pruna_base import PrunaAlgorithmBase
from pruna.engine.save import SAVE_FUNCTIONS

from pruna_pro import DECODER


class PrunaDecoder(PrunaAlgorithmBase):
    """Base class for decoder algorithms."""

    algorithm_group = DECODER
    save_fn = SAVE_FUNCTIONS.reapply
