from typing import Iterable, List, Optional, Tuple
import urwid
import re


class TextEmbed(urwid.WidgetWrap):

    class _FormatWidget(urwid.WidgetWrap):
        def __init__(self, widget: urwid.Widget, widget_list: List[urwid.Widget]):
            self._widget_list = widget_list
            super().__init__(widget)

        def __format__(self, spec):
            try:
                maxcols = int(spec)
                assert maxcols > 0
            except (ValueError, AssertionError):
                raise ValueError(
                    "Invalid widget 'maxcols' in replacement field "
                    f"{len(self._widget_list)} (got: {spec!r})"
                ) from None
            else:
                self._widget_list.append((maxcols, self._w))

            return "\0" + "\1" * (maxcols - 1)

    # In case a placeholder gets wrapped:
    # - will match only the starting portion of a placeholder
    # - not trailing portions on subsequent lines
    _placeholder = re.compile("(\0\1*)")

    # A tail must occur at the beginning of a line but may be preceded by spaces
    # when `align != "left"`
    _placeholder_tail = re.compile("^( *)(\1+)")

    def __init__(
        self,
        text: str,
        *args: urwid.Widget,
        align: str = "left",
        wrap: str = "space",
        **kwargs: urwid.Widget,
    ) -> None:
        self._text = text
        new_text, self._widgets = self._format(text, *args, **kwargs)
        super().__init__(urwid.Text(new_text, align, wrap))

    text = property(lambda self: self._text)

    def render(self, size, focus=False):
        text_canv = super().render(size)
        text = (line.decode() for line in text_canv.text)
        canvases = []
        placeholder = __class__._placeholder
        widgets_iter = iter(self._widgets)
        top = 0
        n_lines = 0

        for line in text:
            if not placeholder.search(line):
                n_lines += 1
                continue

            if n_lines:
                partial_canv = urwid.CompositeCanvas(text_canv)
                partial_canv.trim(top, n_lines)
                canvases.append((partial_canv, None, focus))
                top += n_lines

            partial_canv, tail = self._embed(line, widgets_iter, focus)
            canvases.append((partial_canv, None, focus))
            n_lines = 0
            top += 1

            while tail:
                try:
                    line = next(text)
                except StopIteration:  # wrap = "clip" / "elipsis"
                    break
                partial_canv, tail = self._embed(line, widgets_iter, focus, tail)
                canvases.append((partial_canv, None, focus))
                top += 1

        if n_lines:
            partial_canv = urwid.CompositeCanvas(text_canv)
            partial_canv.trim(top, n_lines)
            canvases.append((partial_canv, None, focus))

        return urwid.CanvasCombine(canvases)

    def set_text(self, text: str, *args: urwid.Widget, **kwargs: urwid.Widget) -> None:
        self._text = text
        new_text, self._widgets = self._format(text, *args, **kwargs)
        self._w.set_text(new_text)

    @classmethod
    def _format(cls, text: str, *args: urwid.Widget, **kwargs: urwid.Widget) -> str:
        widgets = []
        args = [cls._FormatWidget(widget, widgets) for widget in args]
        kwargs = {key: cls._FormatWidget(widget, widgets) for key, widget in kwargs.items()}

        return text.format(*args, **kwargs), widgets

    @staticmethod
    def _embed(
        line: str,
        widgets: Iterable[Tuple[int, urwid.Widget]],
        focus: bool = False,
        tail: Optional[int, urwid.Canvas] = None,
    ) -> Tuple[urwid.CompositeCanvas, Optional[Tuple[int, urwid.Canvas]]]:
        canvases = []

        if tail:
            # Since there is a line after the head, then it must contain the tail.
            # Only one possible occurence of a tail per line,
            # Might be preceded by padding spaces when `align != "left"`.
            _, padding, tail_string, line = __class__._placeholder_tail.split(line)

            if padding:
                # Can use `len(padding)` since all characters should be spaces
                canv = urwid.Text(padding).render((len(padding),))
                canvases.append((canv, None, focus, len(padding)))

            cols, tail_canv = tail
            canv = urwid.CompositeCanvas(tail_canv)
            canv.pad_trim_left_right(cols - tail_canv.cols(), len(tail_string) - cols)
            canvases.append((canv, None, focus, cols))

            if not line:
                tail = (cols - len(tail_string), tail_canv) if len(tail_string) < cols else None
                return urwid.CanvasJoin(canvases), tail
            tail = None

        placeholder = __class__._placeholder
        widgets_iter = iter(widgets)

        for string in placeholder.split(line):
            if not string:
                continue

            if placeholder.fullmatch(string):
                maxcols, widget = next(widgets_iter)
                canv = widget.render((maxcols, 1))
                # `len(string)`, in case the placeholder has been wrapped
                canvases.append((canv, None, focus, len(string)))
                if len(string) != maxcols:
                    tail = (maxcols - len(string), canv)
            else:
                w = urwid.Text(string)
                # Should't use `len(string)` because of wide characters
                maxcols, _ = w.pack()
                canv = w.render((maxcols,))
                canvases.append((canv, None, focus, maxcols))

        return urwid.CanvasJoin(canvases), tail
