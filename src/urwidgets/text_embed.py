from __future__ import annotations

__all__ = ("TextEmbed",)

import re
from itertools import islice
from typing import Iterator, List, Optional, Tuple, Union

import urwid


class TextEmbed(urwid.Text):
    # In case a placeholder gets wrapped or clipped, this pattern will only match the
    # head of a placeholder not tails on subsequent lines
    _placeholder_pattern = re.compile("(\0\1*)")

    # A tail must occur at the beginning of a line but may be preceded by padding
    # spaces when `align != "left"` and `wrap != "clip"`
    _tail_pattern = re.compile("^( *)(\1+)")

    attrib = property(
        lambda self: super().attrib,
        doc="""Run-length encoding of display attributes of the widget's content.

        :type: List[Tuple[Union[None, str, bytes, int], int]]

        See the description of the return value of :py:meth:`get_text`.
        """,
    )

    embedded = property(
        lambda self: [(widget, width) for widget, width, _ in self._embedded],
        doc="""Embedded widgets.

        Returns:
            A list of all embedded widgets and their respective widths, in the same
            order in which they were given in the text markup.

        :type: List[Tuple[urwid.Widget, int]]
        """,
    )

    text = property(
        lambda self: super().text,
        doc="""Raw text content of the widget.

        :type: str

        See the description of the return value of :py:meth:`get_text`.
        """,
    )

    def get_text(
        self,
    ) -> Tuple[str, List[Tuple[Union[None, str, bytes, int], int]]]:
        """Returns a representation of the widget's content.

        Returns:
            A tuple ``(text, attrib)``, where:

            - *text* is the raw text content of the widget.

              Each embedded widget is represented by a substring starting with a
              `"\\x00"` character followed by zero or more `"\\x01"` characters,
              with length equal to the widget's width.

            - *attrib* is the run-length encoding of display attributes.

              Any entry containing a display attribute of the ``int`` type (e.g
              ``(1, 4)``) denotes an embedded widget, where the display attirbute is
              the index of the widget within the :py:data:`embedded` widgets list and
              the run length is the width of the widget.
        """
        return super().get_text()

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
        placeholder_pattern = __class__._placeholder_pattern
        embedded = self._embedded
        tail = None
        top = 0
        n_lines = 0
        clipped = self.wrap == "clip"

        if clipped:
            if self.align != "left":
                translation = self.get_line_translation(size[0])
            text_canv_content = tuple(text_canv.content())
        else:
            embedded_iter = iter(embedded)

        for row_index, line in enumerate(text):
            line = line.decode()
            if clipped:
                if line.startswith("\1"):  # align != "left"
                    widget_index = text_canv_content[row_index][0][0]
                    widget, width, start_pos = embedded[widget_index]
                    tail_canv = widget.render((width, 1))
                    left_trim = -translation[row_index][0][0]
                    # the placeholder is clipped => left_trim > start_pos
                    tail_width = width - (left_trim - start_pos)
                    tail = (tail_width, tail_canv)
                    embedded_iter = islice(embedded, widget_index + 1, None)
                else:
                    tail = None
            if tail:
                if clipped:
                    append_text_lines()
                line_canv = urwid.CompositeCanvas(text_canv)
                line_canv.trim(top, 1)
                partial_canv, tail = self._embed(
                    line, line_canv, embedded_iter, focus, tail
                )
                canvases.append((partial_canv, None, focus))
                n_lines = 0
                top += 1
            elif placeholder_pattern.search(line):
                append_text_lines()
                if clipped:
                    for attr, *_ in text_canv_content[row_index]:
                        if isinstance(attr, int):
                            break
                    embedded_iter = islice(embedded, attr, None)
                line_canv = urwid.CompositeCanvas(text_canv)
                line_canv.trim(top, 1)
                partial_canv, tail = self._embed(line, line_canv, embedded_iter, focus)
                canvases.append((partial_canv, None, focus))
                n_lines = 0
                top += 1
            else:
                n_lines += 1
        append_text_lines()

        return urwid.CanvasCombine(canvases)

    def set_text(self, markup):
        markup, self._embedded = self._substitute_widgets(markup)
        super().set_text(markup)
        self._update_widget_start_pos()

    def _update_widget_start_pos(self):
        if not self._embedded:
            return

        # - Text is clipped per line.
        # - Since the pad/trim amount in the translation (produced by
        #   `StandardTextLayout.align_layout()`) is relative to the start of the line
        #   wrt the layout width (maxcol), the position of an embedded widgets on its
        #   respective line should be relative to the start of the line, not considering
        #   alignment.
        find_placeholders = __class__._placeholder_pattern.finditer
        embedded_iter = iter(self._embedded)
        self._embedded = [
            # Using `Text.pack()` instead of `match.start()` directly to account for
            # wide characters
            (widget, width, urwid.Text(line[: match.start()]).pack()[0])
            for line in super().get_text()[0].splitlines()
            for match, (widget, width, _) in zip(find_placeholders(line), embedded_iter)
        ]

    @staticmethod
    def _substitute_widgets(markup):
        def recurse_markup(attr, markup):
            if isinstance(markup, list):
                for markup in markup:
                    recurse_markup(attr, markup)
            elif isinstance(markup, tuple):
                if len(markup) != 2:
                    raise urwid.TagMarkupException(
                        "Tuples must be in the form `(attribute, tagmarkup)` "
                        f"(got: {markup!r})"
                    )
                recurse_markup(*markup)
            elif isinstance(markup, urwid.Widget):
                if not isinstance(attr, int):
                    raise TypeError(
                        "Invalid type for embedded widget width "
                        f"(got: {type(attr).__name__!r})"
                    )
                if attr <= 0:
                    raise ValueError(f"Invalid widget width (got: {attr!r})")
                new_markup.append((len(embedded), "\0" + "\1" * (attr - 1)))
                embedded.append((markup, attr, 0))
            else:
                # Normalize text type to `str` since other parts of this class use
                # and expect `str`
                if isinstance(markup, bytes):
                    markup = markup.decode()
                new_markup.append(markup if attr is None else (attr, markup))

        embedded = []
        new_markup = []
        recurse_markup(None, markup)

        return new_markup, embedded

    @staticmethod
    def _embed(
        line: str,
        line_canv: urwid.CompositeCanvas,
        embedded_iter: Iterator[Tuple[urwid.Widget, int, int]],
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
            _, padding, tail_string, line = __class__._tail_pattern.split(line)

            if padding:
                # Can use `len(padding)` since all characters should be spaces
                canv = urwid.Text(padding).render((len(padding),))
                canvases.append((canv, None, focus, len(padding)))
                line_index += len(padding)

            tail_width, tail_canv = tail
            canv = urwid.CompositeCanvas(tail_canv)
            canv.pad_trim_left_right(tail_width - tail_canv.cols(), 0)
            canvases.append((canv, None, focus, len(tail_string)))
            line_index += len(tail_string)

            if not line:
                tail = (
                    (tail_width - len(tail_string), tail_canv)
                    if len(tail_string) < tail_width
                    else None
                )
                return urwid.CanvasJoin(canvases), tail
            tail = None

        placeholder_pattern = __class__._placeholder_pattern

        for part in placeholder_pattern.split(line):
            if not part:
                continue

            if placeholder_pattern.fullmatch(part):
                widget, width, _ = next(embedded_iter)
                canv = widget.render((width, 1))
                # `len(part)`, in case the placeholder was wrapped
                canvases.append((canv, None, focus, len(part)))
                line_index += len(part)
                if len(part) != width:
                    tail = (width - len(part), canv)
            else:
                # Should't use `len(part)` because of wide characters
                maxcol = urwid.Text(part).pack()[0]
                canv = urwid.CompositeCanvas(line_canv)
                canv.pad_trim_left_right(-line_index, 0)
                canvases.append((canv, None, focus, maxcol))
                line_index += maxcol

        return urwid.CanvasJoin(canvases), tail


def fix_text_canvas_attr(canv: urwid.TextCanvas) -> urwid.TextCanvas:
    """Workaround for a bug in in `urwid.text_layout.StandardTextLayout`.

    When `wrap=clip, align=center` and there's a line starting with a markup that has
    a display attribute, when the render width (maxcol) is one less than the line's
    width (in screen columns, not characters), the line is rendered as an empty
    string.

    See https://github.com/urwid/urwid/issues/542.
    """
    for line_attr in canv._attr:
        if line_attr[0] == (None, 0):
            del line_attr[0]

    return canv
