from __future__ import annotations

__all__ = ("Hyperlink",)

from typing import Generator, List, Optional, Tuple, Union

import urwid

# NOTE: Any new "private" attribute of any subclass of an urwid class should be
# prepended with "_uw" to avoid clashes with names used by urwid itself.


ESC = "\033"
OSC = f"{ESC}]"
ST = f"{ESC}\\"
START = f"{OSC}8;id=%d;%s{ST}".encode()
END = f"{OSC}8;;{ST}".encode()

valid_byte_range = range(32, 127)


class Hyperlink(urwid.WidgetWrap):
    no_cache = ["render"]

    def __init__(
        self,
        uri: str,
        attr: Union[None, str, bytes, urwid.AttrSpec] = None,
        text: Optional[str] = None,
    ) -> None:
        if not isinstance(uri, str):
            raise TypeError(f"Invalid type for 'uri' (got: {type(text).__name__!r})")
        if not uri:
            raise ValueError("URI is empty")
        invalid_bytes = frozenset(uri.encode()).difference(valid_byte_range)
        if invalid_bytes:
            raise ValueError(
                f"Invalid byte 0x{invalid_bytes.pop():02x} found in URI: {uri!r}"
            )

        if text is not None:
            if not isinstance(text, str):
                raise TypeError(
                    "Invalid type for 'text' (got: {type(text).__name__!r})"
                )
            if "\n" in text:
                raise ValueError(f"'text' spans multiple lines (got: {text!r})")

        super().__init__(urwid.Text((attr, text or uri), "left", "ellipsis"))
        self.uri = uri

    def render(self, size: Tuple[int,], focus: bool = False) -> urwid.HyperlinkCanvas:
        return HyperlinkCanvas(self.uri, self._w.render(size, focus))


class HyperlinkCanvas(urwid.TextCanvas):
    cacheable = False

    _uw_next_id = 0
    _uw_free_ids = set()

    def __init__(self, uri: str, text_canv: urwid.TextCanvas) -> None:
        self.__dict__.update(text_canv.__dict__)
        self._uw_uri = uri.encode()
        self._uw_id = self._uw_get_id()

    def __del__(self):
        __class__._uw_free_ids.add(self._uw_id)

    def content(
        self, *args, **kwargs
    ) -> Generator[
        List[Tuple[Union[None, str, bytes, urwid.AttrSpec], Optional[str], bytes]],
        None,
        None,
    ]:
        yield [
            (None, "U", START % (self._uw_id, self._uw_uri)),
            # There can be only one line since wrap="ellipsis" and the text was checked
            # to not contain "\n".
            # There can be only one run since there was only one display attribute.
            next(super().content(*args, **kwargs))[0],
            (None, "U", END),
        ]

    @staticmethod
    def _uw_get_id():
        if __class__._uw_free_ids:
            return __class__._uw_free_ids.pop()
        __class__._uw_next_id += 1

        return __class__._uw_next_id - 1
