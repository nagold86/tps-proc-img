"""
Domain exceptions of the core. Given.

The core only raises these exceptions: it does not know about HTTP. Whoever
uses it decides how to report them (the API with a status code, the command
line with a message on stderr). Add your own subclasses of ScanError if you
need them.
"""


class ScanError(Exception):
    """Base class of every error of the core."""


class InvalidImage(ScanError):
    """The bytes cannot be opened as an image (empty, corrupt, not an image)."""


class DocumentNotFound(ScanError):
    """The photo is valid, but no document could be recognized in it."""

    DEFAULT_MESSAGE = (
        "No se encontró un documento en la foto. Asegurate de que se vean las cuatro "
        "esquinas, que la hoja ocupe buena parte de la imagen y que haya contraste "
        "con el fondo."
    )

    def __init__(self, message: str | None = None) -> None:
        super().__init__(message or self.DEFAULT_MESSAGE)
