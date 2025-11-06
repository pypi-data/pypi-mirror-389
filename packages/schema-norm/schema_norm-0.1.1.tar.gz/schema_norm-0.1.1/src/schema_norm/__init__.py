__version__ = "0.1.0"
__description__ = "Package for converting AWS Transcribe JSON data into Deepgram JSON data"

from .core import (
    normalize_schema,
    lambda_handler,
    AWSAlternative,
    AWSItem,
    AWSTranscript,
    AWSResults,
    AWSSchema,
    DGWord,
    DGAlternative,
    DGChannel,
    DGResults,
    DGSchema,
)

__all__ = [
    "normalize_schema",
    "lambda_handler",
    "AWSAlternative",
    "AWSItem",
    "AWSTranscript",
    "AWSResults",
    "AWSSchema",
    "DGWord",
    "DGAlternative",
    "DGChannel",
    "DGResults",
    "DGSchema",
]
