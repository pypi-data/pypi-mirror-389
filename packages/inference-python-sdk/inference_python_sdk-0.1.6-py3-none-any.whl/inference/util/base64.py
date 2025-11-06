import base64
from typing import Union


def format_base64_image(s: str) -> str:
    """
    Format base64 string to proper image format.
    """
    return f"data:image/jpeg;base64,{s}"


def format_base64_audio(s: str) -> str:
    """
    Format base64 string to proper audio format.
    """
    return f"data:audio/ogg;base64,{s}"


def encode_base64_from_content(content: Union[str, bytes]) -> str:
    """
    Encode base64 content.
    """
    if isinstance(content, str):
        content = open(content, "rb").read()

    return base64.b64encode(content).decode("utf-8")