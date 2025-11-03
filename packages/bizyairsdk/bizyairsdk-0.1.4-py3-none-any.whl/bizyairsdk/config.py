import os

# Tensor encoding configuration
USE_SAFETENSORS_BY_DEFAULT = os.getenv("BIZYAIR_USE_SAFETENSORS", "false").lower() in (
    "true",
    "1",
    "yes",
)
__all__ = [
    "USE_SAFETENSORS_BY_DEFAULT",
]
