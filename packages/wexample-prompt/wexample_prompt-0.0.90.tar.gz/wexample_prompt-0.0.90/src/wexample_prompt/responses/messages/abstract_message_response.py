from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

from wexample_helpers.decorator.base_class import base_class
from wexample_prompt.responses.abstract_prompt_response import AbstractPromptResponse

if TYPE_CHECKING:
    from wexample_prompt.const.types import LineMessage
    from wexample_prompt.enums.terminal_color import TerminalColor


@base_class
class AbstractMessageResponse(AbstractPromptResponse):
    # Symbol to display before the message, override in subclasses
    SYMBOL: ClassVar[str] = ""

    @classmethod
    def apply_prefix_to_kwargs(
        cls, prefix: str, args: tuple, kwargs: dict, symbol: str | None = None
    ) -> tuple[tuple, dict]:
        """Apply prefix and optional symbol to message parameter."""
        effective_symbol = symbol if symbol is not None else cls.SYMBOL

        full_prefix = prefix
        if effective_symbol:
            full_prefix += f"{effective_symbol} "

        if "message" in kwargs:
            kwargs["message"] = full_prefix + kwargs["message"]
        elif len(args) > 0 and isinstance(args[0], str):
            args = (full_prefix + args[0],) + args[1:]

        return args, kwargs

    @classmethod
    def _create_symbol_message(
        cls,
        text: LineMessage,
        color: TerminalColor,
        symbol: str | None = None,
        **kwargs,
    ) -> AbstractMessageResponse:
        """Create a message with a symbol"""
        from wexample_prompt.common.prompt_response_line import PromptResponseLine

        # Build lines from message handling multi-line inputs like PromptResponseLine.create_from_string
        raw_lines = PromptResponseLine.create_from_string(text=text, color=color)

        return cls._create(lines=raw_lines, **kwargs)
