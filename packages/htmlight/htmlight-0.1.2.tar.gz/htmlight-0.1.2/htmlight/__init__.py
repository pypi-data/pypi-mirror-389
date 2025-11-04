from functools import partial
from typing import Callable, Union

__all__ = ["h"]


def build(name: str, /, *content: str, attributes: Union[dict[str, str], str, None] = None) -> str:
    if isinstance(attributes, str):
        attrs = " " + attributes
    elif attributes:
        attrs = " " + " ".join([f'{k}="{v}"' for k, v in attributes.items()])
    else:
        attrs = ""
    if content:
        return f"<{name}{attrs}>{''.join(content)}</{name}>"
    else:
        return f"<{name}{attrs}/>"


class H:
    def __getattribute__(self, name: str) -> Callable[..., str]:
        return partial(build, name)


h = H()
