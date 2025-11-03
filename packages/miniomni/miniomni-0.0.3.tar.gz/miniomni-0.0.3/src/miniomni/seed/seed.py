import contextlib
import os
from typing import Union, Optional, Tuple, List


@contextlib.contextmanager
def temp_seed(
    seed: Optional[Union[int, Tuple[int, ...]]],
    pkgs: Optional[Union[str, List[str]]] = ['random', 'torch', 'numpy'],
):
    """
        A context manager for setting temporary seed.
        The code block under the `with temp_seed(seed):` would be use temporary 
        random seed on torch, numpy and random packages. Finally the random state 
        before would be set back. 
    """
    if seed is not None:
        try:
            if 'numpy' in pkgs:
                import numpy as np
                np_state = np.random.get_state()
                np.random.seed(seed)
            
            if 'torch' in pkgs:
                import torch
                torch.random.manual_seed(seed if isinstance(seed, int) else sum(seed))
                torch_state = torch.get_rng_state()

            if 'random' in pkgs:
                import random
                rd_state = random.getstate()
                random.seed(seed)

            yield

        finally:

            if 'numpy' in pkgs:
                np.random.set_state(np_state)
            if 'torch' in pkgs:
                torch.set_rng_state(torch_state)
            if 'random' in pkgs:
                random.setstate(rd_state)
    else:
        yield