"""Reusable nesting demo classes for examples."""

from __future__ import annotations

from wexample_helpers.decorator.base_class import base_class
from wexample_prompt.enums.indentation_style import IndentationStyle
from wexample_prompt.enums.terminal_color import TerminalColor
from wexample_prompt.mixins.with_io_methods import WithIoMethods


@base_class
class ParentTask(WithIoMethods):
    """Parent task demonstrating basic nesting."""

    def execute(self, method_name: str = "log") -> None:
        """Execute parent task.

        Args:
            method_name: IO method to use (log, list, etc.)
        """
        self._output_message(method_name, "Parent task started")
        self._output_message(method_name, "Processing parent operations...")

        # Create child with automatic indentation
        child = ChildTask(parent_io_handler=self)
        child.execute(method_name)

        self._output_message(method_name, "Parent task completed")

    def _output_message(self, method_name: str, message: str) -> None:
        """Output a message using the appropriate method."""
        if method_name == "list":
            self.list(items=[message])
        else:
            method = getattr(self, method_name)
            method(message=message)


@base_class
class ChildTask(WithIoMethods):
    """Child task with prefix."""

    def execute(self, method_name: str = "log") -> None:
        """Execute child task.

        Args:
            method_name: IO method to use (log, list, etc.)
        """
        self._output_message(method_name, "Child task started")
        self._output_message(method_name, "Processing child operations...")

        # Create grandchild with automatic indentation
        grandchild = GrandchildTask(parent_io_handler=self)
        grandchild.execute(method_name)

        self._output_message(method_name, "Child task completed")

    def get_io_context_prefix(self) -> str:
        return "child"

    def _output_message(self, method_name: str, message: str) -> None:
        """Output a message using the appropriate method."""
        if method_name == "list":
            self.list(items=[message])
        else:
            method = getattr(self, method_name)
            method(message=message)


@base_class
class GrandchildTask(WithIoMethods):
    """Grandchild task with custom indentation style and prefix format."""

    def execute(self, method_name: str = "log") -> None:
        """Execute grandchild task.

        Args:
            method_name: IO method to use (log, list, etc.)
        """
        self._output_message(method_name, "Grandchild task started (vertical style)")
        self._output_message(method_name, "Processing grandchild operations...")
        self._output_message(method_name, "Grandchild task completed")

    def get_io_context_indentation_character(self) -> str:
        return "│"

    def get_io_context_indentation_style(self):
        return IndentationStyle.VERTICAL

    def get_io_context_indentation_text_color(self):
        return TerminalColor.CYAN

    def get_io_context_prefix(self) -> str:
        return "grandchild"

    def get_io_context_prefix_format(self) -> str:
        return "({prefix}) "  # Custom format with parentheses

    def _output_message(self, method_name: str, message: str) -> None:
        """Output a message using the appropriate method."""
        if method_name == "list":
            self.list(items=[message])
        else:
            method = getattr(self, method_name)
            method(message=message)
