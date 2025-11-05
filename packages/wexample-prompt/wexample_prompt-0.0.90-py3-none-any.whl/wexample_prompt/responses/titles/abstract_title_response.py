from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from wexample_helpers.classes.field import public_field
from wexample_helpers.decorator.base_class import base_class

from wexample_prompt.responses.messages.abstract_message_response import (
    AbstractMessageResponse,
)

if TYPE_CHECKING:
    from wexample_prompt.common.prompt_context import PromptContext
    from wexample_prompt.common.prompt_response_segment import PromptResponseSegment
    from wexample_prompt.enums.terminal_color import TerminalColor
    from wexample_prompt.enums.verbosity_level import VerbosityLevel


@base_class
class AbstractTitleResponse(AbstractMessageResponse):
    """Base class for title-like responses that render:
    "❯ <text> ⫻⫻⫻⫻⫻⫻⫻⫻⫻⫻" with configurable fill character and width.
    """

    DEFAULT_PREFIX: ClassVar[str] = "❯"
    DEFAULT_CHARACTER: ClassVar[str] = "⫻"
    character: str | None = public_field(
        default=DEFAULT_CHARACTER,
        description="Character used to fill the remaining line",
    )
    fill_segment: PromptResponseSegment = public_field(
        description="The trailing fill characters segment"
    )
    prefix_segment: PromptResponseSegment = public_field(
        description="The prefix segment displayed before the title text"
    )
    text_segment: PromptResponseSegment = public_field(
        description="The title text segment"
    )
    width: int | None = public_field(
        default=None, description="Optional fixed width; if not set uses context width"
    )

    @classmethod
    def _create_title(
        cls,
        text: str,
        color: TerminalColor | None = None,
        character: str | None = None,
        width: int | None = None,
        verbosity: VerbosityLevel = None,
    ) -> AbstractTitleResponse:
        from wexample_prompt.common.prompt_response_line import PromptResponseLine
        from wexample_prompt.common.prompt_response_segment import PromptResponseSegment

        prefix = PromptResponseSegment(
            text=f"{cls.DEFAULT_PREFIX} ",
            color=color,
        )
        text_seg = PromptResponseSegment(
            text=f"{text} ",
            color=color,
        )
        fill = PromptResponseSegment(
            text="",
            color=color,
        )

        return cls(
            prefix_segment=prefix,
            text_segment=text_seg,
            fill_segment=fill,
            width=width,
            character=character or cls.DEFAULT_CHARACTER,
            lines=[
                PromptResponseLine(
                    segments=[
                        prefix,
                        text_seg,
                        fill,
                    ]
                )
            ],
            verbosity=verbosity,
        )

    def render(self, context: PromptContext | None = None) -> str | None:
        from wexample_prompt.common.prompt_context import PromptContext
        from wexample_prompt.helper.terminal import terminal_get_visible_width

        context = PromptContext.create_if_none(context=context)

        # Prefer provided context, else defer to super to resolve any defaulting
        width = self.width or context.get_width()
        # Compute remaining space after prefix + text and indentation
        remaining = context.get_available_width(width, minimum=0)

        remaining -= terminal_get_visible_width(self.prefix_segment.text)
        remaining -= terminal_get_visible_width(self.text_segment.text)

        target_width = max(0, remaining)
        fill_pattern = self.character or self.DEFAULT_CHARACTER
        if target_width:
            pattern_width = terminal_get_visible_width(fill_pattern)
            if pattern_width <= 0:
                fill_pattern = self.DEFAULT_CHARACTER
                pattern_width = terminal_get_visible_width(fill_pattern) or 1

            repeats = target_width // pattern_width if pattern_width else 0
            fill_text = fill_pattern * repeats
            visible = repeats * pattern_width

            if visible < target_width:
                fill_text += " " * (target_width - visible)
        else:
            fill_text = ""

        self.fill_segment.text = fill_text

        return super().render(context=context)
