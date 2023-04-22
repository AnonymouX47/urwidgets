from typing import Iterable, List, Optional, Tuple
import urwid
import re


class TextEmbed(urwid.Text):

    # In case a placeholder gets wrapped:
    # - will match only the starting portion of a placeholder
    # - not trailing portions on subsequent lines
    _placeholder = re.compile("(\0\1*)")

    # A tail must occur at the beginning of a line but may be preceded by spaces
    # when `align != "left"`
    _placeholder_tail = re.compile("^( *)(\1+)")

    def render(self, size, focus=False):
        text_canv = super().render(size)
        text = (line.decode() for line in text_canv.text)
        canvases = []
        placeholder = __class__._placeholder
        embedded_canvs_iter = iter(self._embedded_canvs)
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

            partial_canv, tail = self._embed(line, embedded_canvs_iter, focus)
            canvases.append((partial_canv, None, focus))
            n_lines = 0
            top += 1

            while tail:
                try:
                    line = next(text)
                except StopIteration:  # wrap = "clip" / "elipsis"
                    break
                partial_canv, tail = self._embed(line, embedded_canvs_iter, focus, tail)
                canvases.append((partial_canv, None, focus))
                top += 1

        if n_lines:
            partial_canv = urwid.CompositeCanvas(text_canv)
            partial_canv.trim(top, n_lines)
            canvases.append((partial_canv, None, focus))

        return urwid.CanvasCombine(canvases)

    def set_text(self, markup):
        markup, self._embedded_canvs = self._substitute_widgets(markup)
        super().set_text(markup)

    @staticmethod
    def _substitute_widgets(markup):
        if isinstance(markup, list):
            embedded_canvs = []
            new_markup = []
            for markup in markup:
                if isinstance(markup, tuple) and isinstance(markup[0], int):
                    maxcols, widget = markup
                    embedded_canvs.append(widget.render((maxcols, 1)))
                    new_markup.append((len(embedded_canvs), "\0" + "\1" * (maxcols - 1)))
                else:
                    new_markup.append(markup)
            return new_markup, embedded_canvs
        else:
            return markup, []

    @staticmethod
    def _embed(
        line: str,
        embedded_canvs: Iterable[urwid.Canvas],
        focus: bool = False,
        tail: Optional[Tuple[int, urwid.Canvas]] = None,
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
        embedded_canvs_iter = iter(embedded_canvs)

        for string in placeholder.split(line):
            if not string:
                continue

            if placeholder.fullmatch(string):
                canv = next(embedded_canvs_iter)
                # `len(string)`, in case the placeholder has been wrapped
                canvases.append((canv, None, focus, len(string)))
                if len(string) != canv.cols():
                    tail = (canv.cols() - len(string), canv)
            else:
                w = urwid.Text(string)
                # Should't use `len(string)` because of wide characters
                maxcols, _ = w.pack()
                canv = w.render((maxcols,))
                canvases.append((canv, None, focus, maxcols))

        return urwid.CanvasJoin(canvases), tail
