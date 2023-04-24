__all__ = ("TextEmbed",)

import re
from itertools import islice
from typing import Iterable, Optional, Tuple

import urwid


class TextEmbed(urwid.Text):
    # Used to guard the execution of `._update_canv_start_pos()`
    _initialized = True
    _layout_is_set = True

    # In case a placeholder gets wrapped:
    # - will match only the starting portion of a placeholder
    # - not trailing portions on subsequent lines
    _placeholder = re.compile("(\0\1*)")

    # A tail must occur at the beginning of a line but may be preceded by spaces
    # when `align != "left"`
    _placeholder_tail = re.compile("^( *)(\1+)")

    def __init__(self, *args, **kwargs):
        # The order of setting layout, align and wrap is unknown
        self._initialized = False
        super().__init__(*args, **kwargs)
        del self._initialized
        self._update_canv_start_pos()

    def render(self, size, focus=False):
        def append_text_lines():
            nonlocal top

            if n_lines:
                partial_canv = urwid.CompositeCanvas(text_canv)
                partial_canv.trim(top, n_lines)
                canvases.append((partial_canv, None, focus))
                top += n_lines

        text_canv = fix_text_canvas_attr(super().render(size))
        text = text_canv.text
        canvases = []
        placeholder = __class__._placeholder
        embedded_canvs = self._embedded_canvs
        tail = None
        top = 0
        n_lines = 0
        clipped = self.wrap == "clip"

        if clipped:
            if self.align != "left":
                translation = self.get_line_translation(size[0])
            text_canv_content = tuple(text_canv.content())
        else:
            embedded_canvs_iter = iter(embedded_canvs)

        for row, line in enumerate(text):
            line = line.decode()
            if clipped:
                if line.startswith("\1"):  # align != "left"
                    canv_index = text_canv_content[row][0][0]
                    canv_start, tail_canv = embedded_canvs[canv_index]
                    left_trim = -translation[row][0][0]
                    # the placeholder is clipped => left_trim > canv_start
                    tail_width = tail_canv.cols() - (left_trim - canv_start)
                    tail = (tail_width, tail_canv)
                    embedded_canvs_iter = islice(embedded_canvs, canv_index + 1, None)
                else:
                    tail = None
            if tail:
                append_text_lines()  # if clipped, there might be lines
                line_canv = urwid.CompositeCanvas(text_canv)
                line_canv.trim(top, 1)
                partial_canv, tail = self._embed(
                    line, line_canv, embedded_canvs_iter, focus, tail
                )
                canvases.append((partial_canv, None, focus))
                n_lines = 0
                top += 1
            elif placeholder.search(line):
                append_text_lines()
                if clipped:
                    for attr, *_ in text_canv_content[row]:
                        if isinstance(attr, int):
                            break
                    embedded_canvs_iter = islice(embedded_canvs, attr, None)
                line_canv = urwid.CompositeCanvas(text_canv)
                line_canv.trim(top, 1)
                partial_canv, tail = self._embed(
                    line, line_canv, embedded_canvs_iter, focus
                )
                canvases.append((partial_canv, None, focus))
                n_lines = 0
                top += 1
            else:
                n_lines += 1
        append_text_lines()

        return urwid.CanvasCombine(canvases)

    def set_layout(self, *args, **kwargs):
        # The order of setting layout, align and wrap is unknown
        self._layout_is_set = False
        super().set_layout(*args, **kwargs)
        del self._layout_is_set
        self._update_canv_start_pos()

    def set_text(self, markup):
        markup, self._embedded_canvs = self._substitute_widgets(markup)
        super().set_text(markup)
        self._update_canv_start_pos()

    def set_wrap_mode(self, mode):
        super().set_wrap_mode(mode)
        self._update_canv_start_pos()

    def _update_canv_start_pos(self):
        if not (self._initialized and self._layout_is_set and self.wrap == "clip"):
            return
        # - Text is clipped per line.
        # - Since the pad/trim amount in the translation (produced by
        #   `StandardTextLayout.align_layout()`) is relative to the start of the line
        #   wrt the layout width (maxcol), the position of an embedded widgets on its
        #   respective line should be relative to the start of the line, not considering
        #   alignment.
        embedded_canvs_iter = iter(self._embedded_canvs)
        self._embedded_canvs = [
            # Using `Text.pack()` instead of `match.start()` directly to account for
            # wide characters
            (urwid.Text(line[: match.start()]).pack()[0], canv)
            for line in self.text.splitlines()
            for match, (_, canv) in zip(
                __class__._placeholder.finditer(line), embedded_canvs_iter
            )
        ]

    @staticmethod
    def _substitute_widgets(markup):
        if isinstance(markup, list):
            embedded_canvs = []
            new_markup = []
            for markup in markup:
                if isinstance(markup, tuple) and isinstance(markup[0], int):
                    maxcols, widget = markup
                    new_markup.append(
                        (len(embedded_canvs), "\0" + "\1" * (maxcols - 1))
                    )
                    embedded_canvs.append((None, widget.render((maxcols, 1))))
                else:
                    new_markup.append(markup)
            return new_markup, embedded_canvs
        else:
            return markup, []

    @staticmethod
    def _embed(
        line: str,
        line_canv: urwid.CompositeCanvas,
        embedded_canvs: Iterable[Tuple[int, urwid.Canvas]],
        focus: bool = False,
        tail: Optional[Tuple[int, urwid.Canvas]] = None,
    ) -> Tuple[urwid.CompositeCanvas, Optional[Tuple[int, urwid.Canvas]]]:
        canvases = []
        line_index = 0

        if tail:
            # - Since this is the line after the head, then it must contain [a part of]
            #   the tail
            # - Only one possible occurence of a tail per line
            # - Might be preceded by padding spaces when `align != "left"`
            _, padding, tail_string, line = __class__._placeholder_tail.split(line)

            if padding:
                # Can use `len(padding)` since all characters should be spaces
                canv = urwid.Text(padding).render((len(padding),))
                canvases.append((canv, None, focus, len(padding)))
                line_index += len(padding)

            cols, tail_canv = tail
            canv = urwid.CompositeCanvas(tail_canv)
            canv.pad_trim_left_right(cols - tail_canv.cols(), len(tail_string) - cols)
            canvases.append((canv, None, focus, len(tail_string)))
            line_index += cols

            if not line:
                tail = (
                    (cols - len(tail_string), tail_canv)
                    if len(tail_string) < cols
                    else None
                )
                return urwid.CanvasJoin(canvases), tail
            tail = None

        placeholder = __class__._placeholder
        embedded_canvs_iter = iter(embedded_canvs)

        for string in placeholder.split(line):
            if not string:
                continue

            if placeholder.fullmatch(string):
                _, canv = next(embedded_canvs_iter)
                # `len(string)`, in case the placeholder has been wrapped
                canvases.append((canv, None, focus, len(string)))
                line_index += len(string)
                if len(string) != canv.cols():
                    tail = (canv.cols() - len(string), canv)
            else:
                w = urwid.Text(string)
                # Should't use `len(string)` because of wide characters
                maxcols, _ = w.pack()
                canv = urwid.CompositeCanvas(line_canv)
                canv.pad_trim_left_right(
                    -line_index, line_index + maxcols - line_canv.cols()
                )
                canvases.append((canv, None, focus, maxcols))
                line_index += maxcols

        return urwid.CanvasJoin(canvases), tail


def fix_text_canvas_attr(canv: urwid.TextCanvas) -> urwid.TextCanvas:
    """Workaround for a bug in in `urwid.text_layout.StandardTextLayout`.

    When `wrap=clip, align=center` and there's a line starting with a markup that has
    a display attribute, when the render width (maxcols) is one less than the line's
    width (in screen columns, not characters), the line is rendered as an empty
    string.

    See https://github.com/urwid/urwid/issues/542.
    """
    for line in canv._attr:
        if line[0] == (None, 0):
            del line[0]

    return canv
