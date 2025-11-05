from pruna.algorithms.pruna_base import PrunaAlgorithmBase
from pruna.engine.save import SAVE_FUNCTIONS

from pruna_pro import RESAMPLER


class PrunaResampler(PrunaAlgorithmBase):
    """Base class for resamplers."""

    algorithm_group = RESAMPLER
    save_fn = SAVE_FUNCTIONS.reapply
