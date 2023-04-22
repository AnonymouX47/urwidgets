from typing import Iterable, List, Tuple
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

    def __init__(self, text: str, *args: urwid.Widget, **kwargs: urwid.Widget):
        self._text = text
        new_text, self._widgets = self._format(text, *args, **kwargs)
        super().__init__(urwid.Text(new_text))

    text = property(lambda self: self._text)

    def render(self, size, focus=False):
        text_canv = super().render(size)
        cols, rows = self.pack(size)
        canv = urwid.CompositeCanvas()
        text = text_canv.text
        placeholder = __class__._placeholder
        top = 0
        n_lines = 0
        widgets_iter = iter(self._widgets)

        for line in text:
            line = line.decode()
            if not placeholder.search(line):
                n_lines += 1
                continue

            if n_lines:
                partial_canv = urwid.CompositeCanvas(text_canv)
                partial_canv.trim(top, n_lines)
                canv = urwid.CanvasCombine([(canv, None, focus), (partial_canv, None, focus)])
                top += n_lines

            partial_canv = self._embed(line, widgets_iter, focus)
            canv = urwid.CanvasCombine([(canv, None, focus), (partial_canv, None, focus)])
            n_lines = 0
            top += 1

        if n_lines:
            partial_canv = urwid.CompositeCanvas(text_canv)
            partial_canv.trim(top, n_lines)
            canv = urwid.CanvasCombine([(canv, None, focus), (partial_canv, None, focus)])

        return canv

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
    ) -> urwid.CompositeCanvas:
        placeholder = __class__._placeholder
        canvases = []
        widgets_iter = iter(widgets)

        for string in placeholder.split(line):
            if not string:
                continue

            if placeholder.fullmatch(string):
                maxcols, widget = next(widgets_iter)
                canv = widget.render((maxcols, 1))
                # `len(string)` in case the placeholder has been split across lines
                canvases.append((canv, None, focus, len(string)))
            else:
                w = urwid.Text(string)
                # Should't use `len(string)` because of wide characters
                maxcols, _ = w.pack()
                canv = w.render((maxcols,))
                canvases.append((canv, None, focus, maxcols))

        return urwid.CanvasJoin(canvases)
