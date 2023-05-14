from __future__ import annotations

__all__ = (
    "parse_text",
    "TextEmbed",
    # Type Aliases
    "Markup",
    "StringMarkup",
    "ListMarkup",
    "TupleMarkup",
    "NormalTupleMarkup",
    "DisplayAttribute",
    "WidgetTupleMarkup",
    "WidgetListMarkup",
)

import re
from functools import cache, lru_cache
from itertools import islice
from typing import Any, Callable, Dict, Iterable, Iterator, List, Optional, Tuple, Union

import urwid

# NOTE: Any new "private" attribute of any subclass of an urwid class should be
# prepended with "_uw" to avoid clashes with names used by urwid itself.

# I really hope these are correct :D
Markup = Union["StringMarkup", "ListMarkup", "TupleMarkup"]
StringMarkup = Union[str, bytes]
ListMarkup = List["Markup"]
TupleMarkup = Union["NormalTupleMarkup", "WidgetTupleMarkup"]
NormalTupleMarkup = Tuple["DisplayAttribute", Union["StringMarkup", "ListMarkup"]]
DisplayAttribute = Union[None, str, bytes, urwid.AttrSpec]
WidgetTupleMarkup = Tuple[int, Union[urwid.Widget, "WidgetListMarkup"]]
WidgetListMarkup = List[Union[urwid.Widget, "Markup", "WidgetListMarkup"]]


class TextEmbed(urwid.Text):
    """A text widget within which other widgets may be embedded.

    This is an extension of the :py:class:`urwid.Text` widget. Every feature and
    interface of :py:class:`~urwid.Text` is supported and works essentially the same,
    **except for the "ellipsis" wrap mode** which is currently not implemented.
    Text markup format is essentially the same, except when embedding widgets.

    **Embedding Widgets**
        A widget is embedded by specifying it as a markup element with an **integer
        display attribute**, where the display attribute is the number of screen
        columns the widget should occupy.

        Examples:

        >>> # w1 spans 2 columns
        >>> TextEmbed(["This widget (", (2, w1), ") spans two columns"])
        >>> # w1 and w2 span 2 columns
        >>> TextEmbed(["These widgets (", (2, [w1, w2]), ") span two columns each"])
        >>> # w1 and w2 span 2 columns, the text in-between has no display attribute
        >>> TextEmbed([(2, [w1, (None, "and"), w2]), " span two columns each"])
        >>> # w1 and w2 span 2 columns, text in the middle is red
        >>> TextEmbed((2, [w1, ("red", " i am red "), w2]))
        >>> # w1 and w3 span 2 columns, w2 spans 5 columns
        >>> TextEmbed((2, [w1, (5, w2), w3]))

        Visible embedded widgets are always rendered (may be cached) whenever the
        ``TextEmbed`` widget is re-rendered (i.e an uncached render). Hence, this
        allows for dynamic parts of text without updating the entire widget.
        Going a step further, embeddded widgets can be swapped by using
        ``urwid.WidgetPlaceholder`` but their widths will remain the same.

        NOTE:
            - Every embedded widget must be a box widget and is always rendered with
              size ``(width, 1)``.  :py:class:`urwid.Filler` can be used to wrap flow
              widgets.
            - Each embedded widgets are treated as a single WORD (i.e containing no
              whitespace). Therefore, consecutive embedded widgets are also treated as
              a single WORD. This affects the "space" wrap mode.
            - After updating or swapping an embedded widget, this widget's canvases
              should be invalidated to ensure it re-renders.

    Raises:
        TypeError: A widget markup element has a non-integer display attribute.
        ValueError: A widget doesn't support box sizing.
        ValueError: A widget has a non-positive width (display attribute).
    """

    # In case a placeholder gets wrapped or clipped, this pattern will only match the
    # head of a placeholder not tails on subsequent lines
    _uw_placeholder_pattern = re.compile("(\0\1*)")

    # A tail must occur at the beginning of a line but may be preceded by padding
    # spaces when `align != "left"` and `wrap != "clip"`
    _uw_tail_pattern = re.compile("^( *)(\1+)")

    attrib = property(
        lambda self: super().attrib,
        doc="""Run-length encoding of display attributes of the widget's content.

        :type: List[Tuple[Union[DisplayAttribute, int], int]]

        See the description of the second item in the return value of
        :py:meth:`get_text`.
        """,
    )

    embedded = property(
        lambda self: [(widget, width) for widget, width, _ in self._uw_embedded],
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

        See the description of the first item in the return value of
        :py:meth:`get_text`.
        """,
    )

    def get_text(
        self,
    ) -> Tuple[str, List[Tuple[Union[DisplayAttribute, int], int]]]:
        """Returns a representation of the widget's content.

        Returns:
            A tuple ``(text, attrib)``, where

            - *text* is the raw text content of the widget.

              Each embedded widget is represented by a substring starting with a
              ``"\\x00"`` character followed by zero or more ``"\\x01"`` characters,
              with length equal to the widget's width.

            - *attrib* is the run-length encoding of display attributes.

              Any entry containing a display attribute of the ``int`` type (e.g
              ``(1, 4)``) denotes an embedded widget, where the display attirbute is
              the index of the widget within the :py:attr:`embedded` widgets list and
              the run length is the width of the widget.
        """
        return super().get_text()

    def render(
        self, size: Tuple[int,], focus: bool = False
    ) -> Union[urwid.TextCanvas, urwid.CompositeCanvas]:
        text_canv = fix_text_canvas_attr(super().render(size, focus))
        embedded = self._uw_embedded
        if not embedded:
            return text_canv

        def append_text_lines():
            nonlocal top

            if n_lines:
                partial_canv = urwid.CompositeCanvas(text_canv)
                partial_canv.trim(top, n_lines)
                canvases.append((partial_canv, None, focus))
                top += n_lines

        text = text_canv.text
        canvases = []
        placeholder_pattern = __class__._uw_placeholder_pattern
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
                    tail_canv = widget.render((width, 1), focus)
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
                partial_canv, tail = self._uw_embed(
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
                partial_canv, tail = self._uw_embed(
                    line, line_canv, embedded_iter, focus
                )
                canvases.append((partial_canv, None, focus))
                n_lines = 0
                top += 1
            else:
                n_lines += 1
        append_text_lines()

        return urwid.CanvasCombine(canvases)

    def set_text(self, markup: Markup) -> None:
        """Sets the widget's content.

        Also supports widget markup elements. See the class description.
        """
        markup, self._uw_embedded = self._uw_substitute_widgets(markup)
        super().set_text(markup)
        self._uw_update_widget_start_pos()

    def set_wrap_mode(self, mode: str) -> None:
        if mode == "ellipsis":
            raise NotImplementedError("Wrap mode 'ellipsis' is not implemented.")
        super().set_wrap_mode(mode)

    wrap = property(lambda self: super().wrap, set_wrap_mode)

    def _uw_update_widget_start_pos(self) -> None:
        """Updates the start position of embedded widgets on their respective lines."""
        if not self._uw_embedded:
            return

        # - Text is clipped per line.
        # - Since the pad/trim amount in the translation (produced by
        #   `StandardTextLayout.align_layout()`) is relative to the start of the line
        #   wrt the layout width (maxcol), the position of an embedded widgets on its
        #   respective line should be relative to the start of the line, not considering
        #   alignment.
        find_placeholders = __class__._uw_placeholder_pattern.finditer
        embedded_iter = iter(self._uw_embedded)
        self._uw_embedded = [
            # Using `Text.pack()` instead of `match.start()` directly to account for
            # wide characters
            (widget, width, urwid.Text(line[: match.start()]).pack()[0])
            for line in super().get_text()[0].splitlines()
            for match, (widget, width, _) in zip(find_placeholders(line), embedded_iter)
        ]

    @staticmethod
    def _uw_substitute_widgets(
        markup: Markup,
    ) -> Tuple[Markup, List[Tuple[urwid.Widget, int, int]]]:
        """Extracts embedded widgets from *markup* and replace widget markup elements
        with placeholders.

        Returns:
            A tuple containing:

            - The given markup flattened and with all widget elements replaced by
              placeholders.
            - A list of ``(widget, width, start_position)`` tuples describing the
              embedded widgets, where *start_position* is initialized to zero and
              later updated by :py:meth:`_uw_update_widget_start_pos`.
        """

        def recurse_markup(attr: Union[DisplayAttribute, int], markup: Markup) -> None:
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
                if "box" not in markup.sizing():
                    raise ValueError(f"Not a box widget (got: {markup!r})")
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
    def _uw_embed(
        line: str,
        line_canv: urwid.CompositeCanvas,
        embedded_iter: Iterator[Tuple[urwid.Widget, int, int]],
        focus: bool = False,
        tail: Optional[Tuple[int, urwid.Canvas]] = None,
    ) -> Tuple[urwid.CompositeCanvas, Optional[Tuple[int, urwid.Canvas]]]:
        """Replaces widget placeholders in a line with with the widgets' contents.

        Args:
            line: A line of the original text canvas.
            line_canv: A canvas corresponding to *line*.
            embedded_iter: An iterator of ``(widget, width, start_position)`` tuples
              in the same order as :py:attr:`embedded`, where *start_position* is as
              determined by :py:meth:`_uw_update_widget_start_pos`.
            focus: As in :py:meth:`render`.
            tail: The description of the "tail" of an embedded widget that is the first
              part of the line ``(tail_width, tail_canv)``, if it was wrapped/clipped,
              where:

              - *tail_width* is the width of the remaining (unused) portion of the
                widget's canvas content towards it's right end.
              - *tail_canv* is the original rendered canvas of the widget, unmodified.

              OR ``None`` if a widget is not the first part of the line.

        Returns:
            A tuple containing:

            - A ``CompositeCanvas`` containing the separate parts from the original
              text canvas and the embedded widgets' canvases.
            - The description of the "tail" of an embedded widget that is the last part
              of the line ``(tail_width, tail_canv)`` (see the description of *tail*
              above), if it was wrapped/clipped OR ``None`` if it wasn't wrapped/clipped
              or a widget is not the last part of the line.
        """
        canvases = []
        line_index = 0

        if tail:
            # - Since this is the line after the head, then it must contain [a part of]
            #   the tail
            # - Only one possible occurence of a tail per line
            # - Might be preceded by padding spaces when `align != "left"`
            _, padding, tail_string, line = __class__._uw_tail_pattern.split(line)

            if padding:
                # Can use `len(padding)` since all characters should be spaces
                canv = urwid.Text(padding).render((len(padding),), focus)
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

        placeholder_pattern = __class__._uw_placeholder_pattern

        for part in placeholder_pattern.split(line):
            if not part:
                continue

            if placeholder_pattern.fullmatch(part):
                widget, width, _ = next(embedded_iter)
                canv = widget.render((width, 1), focus)
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


def parse_text(
    text: str,
    patterns: Iterable[re.Pattern],
    repl: Callable[[re.Pattern, Tuple[Optional[str]], Tuple[int, int], ...], Markup],
    *repl_args: Any,
    **repl_kwargs: Any,
) -> Markup:
    r"""Parses a string into a text/widget markup list.

    Args:
        text: The string to parse.
        patterns: An iterable of RegEx pattern objects.
        repl: A callable to replace a substring of *text* matched by any of the given
          RegEx patterns.
        repl_args: Additional positional arguments to be passed to *repl* whenever it's
          called.
        repl_kwargs: keyword arguments to be passed to *repl* whenever it's called.

    Returns:
        A text/widget markup (see :py:data:`Markup`) that should be compatible with
        :py:class:`TextEmbed` and/or :py:class:`urwid.Text`, depending on the values
        returned by *repl*.

    Raises:
        TypeError: An argument is of an unexpected type.
        ValueError: *patterns* is empty.
        ValueError: A given pattern object was not compiled from a :py:class:`str`
          instance.

    Whenever any of the given RegEx patterns matches a **non-empty** substring of
    *text*, *repl* is called with the following arguments (in the given order):

    - the :py:class:`re.Pattern` object that matched the substring
    - a tuple containing the match groups

      - starting with the whole match,
      - followed by the all the subgroups of the match, from 1 up to however many
        groups are in the pattern, if any (``None`` for each group that didn't
        participate in the match)

    - a tuple containing the indexes of the start and end of the substring
    - *repl_args* unpacked
    - *repl_kwargs* unpacked

    and *should* return a valid text/widget markup (see :py:data:`Markup`). If the
    value returned is *false* (such as ``None`` or an empty string), it is omitted
    from the result.

    Example::

        import re
        from urwid import Filler
        from urwidgets import Hyperlink, TextEmbed, parse_text

        MARKDOWN = {
            re.compile(r"\*\*(.+?)\*\*"): lambda g: ("bold", g[1]),
            re.compile("https://[^ ]+"): (
                lambda g: (min(len(g[0]), 14), Filler(Hyperlink(g[0], "blue")))
            ),
            re.compile(r"\[(.+)\]\((.+)\)"): (
                lambda g: (len(g[1]), Filler(Hyperlink(g[2], "blue", g[1])))
            ),
        }

        link = "https://urwid.org"
        text = f"[This]({link}) is a **link** to {link}"
        print(text)
        # Output: [This](https://urwid.org) is a **link** to https://urwid.org

        markup = parse_text(
            text, MARKDOWN, lambda pattern, groups, span: MARKDOWN[pattern](groups)
        )
        print(markup)
        # Output:
        # [
        #   (4, <Filler box widget <Hyperlink flow widget>>),
        #   ' is a ',
        #   ('bold', 'link'),
        #   ' to ',
        #   (14, <Filler box widget <Hyperlink flow widget>>),
        # ]

        text_widget = TextEmbed(markup)
        canv = text_widget.render(text_widget.pack()[:1])
        print(canv.text[0].decode())
        # Output: This is a link to https://urwid…
        # The hyperlinks will be clickable if supported

    NOTE:
        In the case of overlapping matches, the substring that occurs first is matched
        and if they start at the same index, the pattern that appears first in
        *patterns* takes precedence.
    """
    if not isinstance(text, str):
        raise TypeError(f"Tnvalid type for 'text' (got: {type(text).__name__!r})")
    if not text:
        return text

    patterns = tuple(patterns)
    if not patterns:
        raise ValueError("No RegEx patterns")

    combined_pattern, indexed_patterns = combine_patterns(patterns)
    full_markup = []
    ptr = 0
    for match in combined_pattern.finditer(text):
        span = match.span()
        if ptr < span[0]:
            full_markup.append(text[ptr : span[0]])
        if match.group():
            pattern_index = match.lastindex
            pattern = indexed_patterns[pattern_index]
            markup = repl(
                pattern,
                match.groups()[pattern_index - 1 : pattern_index + pattern.groups],
                span,
                *repl_args,
                **repl_kwargs,
            )
            if markup:
                full_markup.append(markup)
        ptr = span[1]
    if ptr < len(text):
        full_markup.append(text[ptr:])

    return full_markup[0] if len(full_markup) == 1 else full_markup


# Private

RE_INLINE_FLAGS = {re.A: "a", re.I: "i", re.L: "L", re.M: "m", re.S: "s", re.X: "x"}


@lru_cache
def combine_patterns(
    patterns: Tuple[re.Pattern],
) -> Tuple[re.Pattern, Dict[int, re.Pattern]]:
    """Combines multiple RegEx patterns with their respective flags into a single OR-ed
    pattern.

    Returns:
        A tuple containing

        - the combined RegEx pattern
        - a dictionary mapping the index of the group in the combined pattern
          corresponding to each given pattern to the pattern
    """
    grouped_patterns = []
    indexed_patterns = {}  # <index of group in combined pattern>: <pattern>
    group_index = 1
    for pattern in patterns:
        pattern_string = pattern.pattern
        if not isinstance(pattern_string, str):
            raise ValueError(f"Pattern not compiled from `str` (got: {pattern!r})")

        inline_flags = get_inline_flags(pattern.flags)
        grouped_patterns.append(
            f"(?{inline_flags}:({pattern_string}))"
            if inline_flags
            else f"({pattern_string})"
        )
        indexed_patterns[group_index] = pattern
        group_index += pattern.groups + 1

    return re.compile("|".join(grouped_patterns)), indexed_patterns


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


@cache  # Only 511 (zero is excluded) unique bit patterns (and not even all can occur)
def get_inline_flags(flags: int) -> str:
    """Converts a RegEx integer flag into the corresponding set of inline flags"""
    return "".join([inline for flag, inline in RE_INLINE_FLAGS.items() if flag & flags])
