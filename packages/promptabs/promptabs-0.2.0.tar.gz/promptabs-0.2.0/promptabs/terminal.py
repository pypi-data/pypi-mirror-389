"""
Terminal rendering and control module
"""

import sys
import os
from typing import Tuple, List, Optional, Set
from .theme import ColorTheme


class TerminalRenderer:
    """Handles terminal rendering and ANSI escape sequences"""

    # ANSI color codes (use theme constants)
    RESET = ColorTheme.RESET
    BOLD = ColorTheme.BOLD
    DIM = ColorTheme.DIM
    BLUE = ColorTheme.BLUE
    GREEN = ColorTheme.GREEN
    YELLOW = ColorTheme.YELLOW
    CYAN = ColorTheme.CYAN

    @staticmethod
    def clear_screen():
        """Clear the terminal screen (cross-platform)"""
        # Works on Windows, macOS, and Linux
        os.system("clear" if os.name == "posix" else "cls")

    @staticmethod
    def move_cursor(row: int, col: int):
        """Move cursor to specific position"""
        sys.stdout.write(f"\033[{row};{col}H")
        sys.stdout.flush()

    @staticmethod
    def hide_cursor():
        """Hide the cursor"""
        sys.stdout.write("\033[?25l")
        sys.stdout.flush()

    @staticmethod
    def show_cursor():
        """Show the cursor"""
        sys.stdout.write("\033[?25h")
        sys.stdout.flush()

    @staticmethod
    def get_terminal_size() -> Tuple[int, int]:
        """Get terminal width and height (cross-platform)

        Works on Windows (Python 3.3+), macOS, and Linux.
        Returns (width, height) tuple.
        """
        try:
            size = os.get_terminal_size()
            return (size.columns, size.lines)
        except (AttributeError, ValueError, OSError):
            # Fallback for edge cases
            return (80, 24)

    @staticmethod
    def render_text(text: str, color: str = "", bold: bool = False) -> str:
        """Render text with optional color and bold"""
        prefix = ""
        if bold:
            prefix += TerminalRenderer.BOLD
        if color:
            prefix += color

        if prefix:
            return prefix + text + TerminalRenderer.RESET
        return text


class TabRenderer:
    """Renders tab headers and content"""

    def __init__(self, renderer: TerminalRenderer):
        self.renderer = renderer

    def render_tab_header(
        self,
        tabs: List[str],
        active_index: int,
        max_width: int = 80,
    ) -> str:
        """
        Render tab header with active tab highlighted

        Args:
            tabs: List of tab titles
            active_index: Index of currently active tab
            max_width: Maximum width for tab header

        Returns:
            Rendered tab header string
        """
        tab_elements = []

        for i, tab in enumerate(tabs):
            if i == active_index:
                # Active tab with checkbox
                styled = self.renderer.render_text(
                    f"☑ {tab}",
                    color=self.renderer.BLUE,
                    bold=True,
                )
            else:
                # Inactive tab with unchecked checkbox
                styled = self.renderer.render_text(f"☐ {tab}", color=self.renderer.DIM)

            tab_elements.append(styled)

        # Join tabs with separators
        header = "  ".join(tab_elements)

        # Add navigation hint
        nav_hint = self.renderer.render_text(" → ", color=self.renderer.YELLOW)
        header += nav_hint

        return header

    def render_options(
        self,
        options: List[str],
        selected_index: int,
        selected_options: Optional[Set[str]] = None,
    ) -> str:
        """
        Render question options with selection indicator

        Args:
            options: List of option strings
            selected_index: Index of currently selected option
            selected_options: Set of selected options (for multiple choice)

        Returns:
            Rendered options string
        """
        lines = []
        for i, option in enumerate(options):
            if i == selected_index:
                # Currently highlighted option
                indicator = self.renderer.render_text("❯ ", color=self.renderer.GREEN, bold=True)
                styled = self.renderer.render_text(option, color=self.renderer.GREEN, bold=True)

                # For multiple choice, add checkbox
                if selected_options is not None:
                    checkbox = "☑ " if option in selected_options else "☐ "
                    lines.append(f"{indicator}{checkbox}{styled}")
                else:
                    lines.append(f"{indicator}{styled}")
            else:
                # Unselected option
                if selected_options is not None:
                    # Multiple choice - show checkbox
                    checkbox = "☑ " if option in selected_options else "☐ "
                    lines.append(f"  {checkbox}{option}")
                else:
                    # Single choice - no checkbox
                    lines.append(f"  {option}")

        return "\n".join(lines)

    def render_review_page(
        self,
        responses: dict,
        questions: list,
        missing_required: list,
    ) -> str:
        """
        Render the review/submit page

        Args:
            responses: Dictionary of responses so far
            questions: List of all questions
            missing_required: List of required question IDs that weren't answered

        Returns:
            Rendered review page string
        """
        lines = [self.renderer.render_text("Review your answers", bold=True)]
        lines.append("")

        if missing_required:
            warning = self.renderer.render_text(
                "⚠ You have not answered all questions",
                color=self.renderer.YELLOW,
                bold=True,
            )
            lines.append(warning)
            lines.append("")

        # Show all answers
        for question in questions:
            if question.id in responses:
                answer = responses[question.id]
                lines.append(f"● {question.title}")

                # Handle both single-choice (str) and multiple-choice (list)
                if isinstance(answer, list):
                    # Multiple choice - show each selected option
                    for selected_option in answer:
                        lines.append(f"  ☑ {selected_option}")
                else:
                    # Single choice or custom input
                    lines.append(f"  → {answer}")
            else:
                # Unanswered question
                status = self.renderer.render_text(
                    "● " + question.title,
                    color=self.renderer.YELLOW if question.required else self.renderer.DIM,
                )
                lines.append(status)
                unanswered = self.renderer.render_text(
                    "  → (not answered)",
                    color=self.renderer.YELLOW if question.required else self.renderer.DIM,
                )
                lines.append(unanswered)

        lines.append("")
        lines.append(self.renderer.render_text("Ready to submit your answers?", bold=True))
        lines.append("")

        return "\n".join(lines)
