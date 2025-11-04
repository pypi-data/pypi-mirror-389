"""
⚠️ Este paquete ha sido renombrado a 'sorix'.

'allison' ya no recibirá actualizaciones. 
Por favor, actualice sus dependencias ejecutando:

    pip install sorix
    # y reemplace en su código:
    # import allison  →  import sorix

Mientras tanto, este módulo mantiene compatibilidad temporal con 'sorix' 
para evitar interrupciones en proyectos existentes.
"""

import warnings

warnings.warn(
    "El paquete 'allison' ha sido renombrado a 'sorix'. "
    "Por favor instale 'sorix' y actualice sus importaciones. "
    "Compatibilidad temporal activada.",
    DeprecationWarning,
    stacklevel=2
)

try:
    # Redirige las importaciones principales al nuevo paquete
    from sorix.tensor.tensor import tensor, no_grad
    from sorix.cuda import cuda
    from sorix.utils.utils import (
        sigmoid, softmax, argmax,
        as_tensor, from_numpy,
        zeros, ones, full, eye, diag, empty,
        arange, linspace, logspace,
        rand, randn, randint, randperm,
        zeros_like, ones_like, empty_like, full_like,
    )
    from sorix.utils.math import (
        sin, cos, tanh, exp, log, sqrt, mean, sum
    )

except ModuleNotFoundError as e:
    raise ImportError(
        "No se encontró el paquete 'sorix'. "
        "Instálelo con: pip install sorix"
    ) from e
