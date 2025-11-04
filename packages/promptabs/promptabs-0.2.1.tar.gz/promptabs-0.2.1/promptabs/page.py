"""
Page abstraction for survey pages
"""

from abc import ABC, abstractmethod
from typing import List
from .state import SurveyState
from .types import Question
from .terminal import TerminalRenderer, TabRenderer
from .input_handler import InputHandler


class Page(ABC):
    """Abstract base class for survey pages"""

    @abstractmethod
    def render(self, renderer: TerminalRenderer, tab_renderer: TabRenderer,
               state: SurveyState, questions: List[Question]):
        """
        Render the page.

        Args:
            renderer: Terminal renderer
            tab_renderer: Tab renderer
            state: Current survey state
            questions: List of all questions
        """
        pass

    @abstractmethod
    def handle_key(self, key: str, state: SurveyState,
                   questions: List[Question]) -> bool:
        """
        Handle keyboard input.

        Args:
            key: The key pressed
            state: Current survey state
            questions: List of all questions

        Returns:
            True to continue the event loop, False to exit
        """
        pass


class QuestionPage(Page):
    """Page for displaying a question and its options"""

    def __init__(self, question_index: int, tab_renderer: TabRenderer,
                 renderer: TerminalRenderer):
        """
        Initialize question page.

        Args:
            question_index: Index of the question to display
            tab_renderer: Tab renderer instance
            renderer: Terminal renderer instance
        """
        self.question_index = question_index
        self.tab_renderer = tab_renderer
        self.renderer = renderer

    def render(self, renderer: TerminalRenderer, tab_renderer: TabRenderer,
               state: SurveyState, questions: List[Question]):
        """Render the question page"""
        self.renderer = renderer
        self.tab_renderer = tab_renderer

        # Get tab titles (including Submit)
        tab_titles = [q.title for q in questions] + ["Submit"]

        # Render tab header
        tab_header = self.tab_renderer.render_tab_header(
            tab_titles,
            state.current_tab_index,
        )
        print(tab_header)
        print()

        # Render current question
        current_question = questions[state.current_tab_index]
        self._render_question(current_question, state)

    def handle_key(self, key: str, state: SurveyState,
                   questions: List[Question]) -> bool:
        """Handle keyboard input for question page"""
        if not questions:
            return False

        current_question = questions[state.current_tab_index]

        if key == InputHandler.ARROW_LEFT:
            state.move_previous_tab()
        elif key == InputHandler.ARROW_RIGHT:
            # For multiple choice, right arrow confirms selection
            if current_question.type == "multiple_choice":
                self._confirm_selection(current_question, state)
            else:
                state.move_next_tab()
        elif key == InputHandler.ARROW_UP:
            self._move_to_previous_option(current_question, state)
        elif key == InputHandler.ARROW_DOWN:
            self._move_to_next_option(current_question, state)
        elif key == InputHandler.SPACE or key == InputHandler.ENTER:
            # Space/Enter behavior depends on question type
            if current_question.type == "multiple_choice":
                self._toggle_option_selection(current_question, state)
            else:
                self._confirm_selection(current_question, state)
        elif key == InputHandler.CTRL_C or key == InputHandler.ESC:
            raise KeyboardInterrupt

        return True

    def _render_question(self, question: Question, state: SurveyState):
        """Render a single question with its options"""
        # Note: title is already shown in the tab header, so we skip it here
        print(self.renderer.render_text(question.question, color=self.renderer.DIM))
        print()

        # Render options
        selected_index = state.current_option_index.get(question.id, 0)

        # For multiple choice, pass selected options
        if question.type == "multiple_choice":
            options_display = self.tab_renderer.render_options(
                question.options,
                selected_index,
                selected_options=state.selected_options.get(question.id, set()),
            )
        else:
            options_display = self.tab_renderer.render_options(
                question.options,
                selected_index,
            )
        print(options_display)

        print()
        if question.type == "multiple_choice":
            print(
                self.renderer.render_text(
                    "Use ↑↓ to select · Space/Enter to toggle · → to continue · ← → to navigate tabs · Esc to cancel",
                    color=self.renderer.DIM,
                )
            )
        else:
            print(
                self.renderer.render_text(
                    "Use ↑↓ to select · ← → to navigate tabs · Enter to confirm · Esc to cancel",
                    color=self.renderer.DIM,
                )
            )

    def _move_to_next_option(self, question: Question, state: SurveyState):
        """Move to the next option in current question"""
        max_index = len(question.options) - 1
        current_index = state.current_option_index.get(question.id, 0)
        if current_index < max_index:
            state.current_option_index[question.id] = current_index + 1

    def _move_to_previous_option(self, question: Question, state: SurveyState):
        """Move to the previous option in current question"""
        current_index = state.current_option_index.get(question.id, 0)
        if current_index > 0:
            state.current_option_index[question.id] = current_index - 1

    def _confirm_selection(self, question: Question, state: SurveyState):
        """Confirm the current selection and move to next question"""
        selected_index = state.current_option_index.get(question.id, 0)
        selected_option = question.options[selected_index]
        state.set_question_response(question.id, selected_option)
        state.move_next_tab()

    def _toggle_option_selection(self, question: Question, state: SurveyState):
        """Toggle selection of current option for multiple choice questions"""
        if question.type != "multiple_choice":
            return

        selected_index = state.current_option_index.get(question.id, 0)
        selected_option = question.options[selected_index]
        state.toggle_option_selection(question.id, selected_option)


class SubmitPage(Page):
    """Page for reviewing answers and submitting"""

    def __init__(self, tab_renderer: TabRenderer, renderer: TerminalRenderer):
        """
        Initialize submit page.

        Args:
            tab_renderer: Tab renderer instance
            renderer: Terminal renderer instance
        """
        self.tab_renderer = tab_renderer
        self.renderer = renderer

    def render(self, renderer: TerminalRenderer, tab_renderer: TabRenderer,
               state: SurveyState, questions: List[Question]):
        """Render the submit page"""
        self.renderer = renderer
        self.tab_renderer = tab_renderer

        # Get tab titles (including Submit)
        tab_titles = [q.title for q in questions] + ["Submit"]

        # Render tab header with Submit tab highlighted
        tab_header = self.tab_renderer.render_tab_header(
            tab_titles,
            len(questions),  # Submit tab index
        )
        print(tab_header)
        print()

        # Render review content with all responses
        missing_required = self._get_missing_required(state, questions)
        display_responses = state.get_display_responses()
        review_content = self.tab_renderer.render_review_page(
            display_responses,
            questions,
            missing_required,
        )
        print(review_content)

        # Render feedback field
        print()
        self._render_feedback_field(state)

        # Render submit options
        print()
        submit_options = ["Submit answers", "Cancel"]
        options_display = self.tab_renderer.render_options(
            submit_options,
            state.submit_option_index if state.submit_option_index < 2 else 0
        )
        print(options_display)

        print()
        if missing_required:
            warning_msg = self.renderer.render_text(
                "⚠ Cannot submit: Please answer all required questions",
                color=self.renderer.YELLOW,
            )
            print(warning_msg)
        else:
            print(
                self.renderer.render_text(
                    "Use ↑↓ to select · ← → to navigate tabs · Enter to confirm · Esc to cancel",
                    color=self.renderer.DIM,
                )
            )

    def handle_key(self, key: str, state: SurveyState,
                   questions: List[Question]) -> bool:
        """Handle keyboard input for submit page"""
        if state.feedback_input_active:
            return self._handle_feedback_input(key, state)
        else:
            return self._handle_submit_navigation(key, state, questions)

    def _handle_feedback_input(self, key: str, state: SurveyState) -> bool:
        """Handle keyboard input while editing feedback"""
        if key == InputHandler.ENTER:
            # Confirm feedback and move to Submit button
            state.feedback_input_active = False
            state.feedback_cursor_pos = 0
            state.submit_option_index = 0
        elif key == InputHandler.ARROW_LEFT:
            # Move cursor left
            if state.feedback_cursor_pos > 0:
                state.feedback_cursor_pos -= 1
        elif key == InputHandler.ARROW_RIGHT:
            # Move cursor right
            if state.feedback and state.feedback_cursor_pos < len(state.feedback):
                state.feedback_cursor_pos += 1
        elif key == InputHandler.BACKSPACE:
            # Delete character at cursor position
            if state.feedback and state.feedback_cursor_pos > 0:
                state.feedback = (state.feedback[:state.feedback_cursor_pos - 1] +
                                 state.feedback[state.feedback_cursor_pos:])
                state.feedback_cursor_pos -= 1
        elif key == InputHandler.ESC or key == InputHandler.CTRL_C:
            # Cancel feedback input
            state.feedback_input_active = False
            state.feedback_cursor_pos = 0
        elif key and len(key) == 1 and ord(key) >= 32:
            # Insert printable character at cursor position
            state.feedback = (state.feedback[:state.feedback_cursor_pos] + key +
                             state.feedback[state.feedback_cursor_pos:])
            state.feedback_cursor_pos += 1

        return True

    def _handle_submit_navigation(self, key: str, state: SurveyState,
                                 questions: List[Question]) -> bool:
        """Handle keyboard input for submit button/feedback navigation"""
        if key == InputHandler.ARROW_LEFT:
            state.move_previous_tab()
        elif key == InputHandler.ARROW_RIGHT:
            state.move_next_tab()
        elif key == InputHandler.ARROW_UP:
            self._submit_move_up(state)
        elif key == InputHandler.ARROW_DOWN:
            self._submit_move_down(state)
        elif key == InputHandler.ENTER:
            # Check which option is selected
            if state.submit_option_index == 2:
                # Feedback field is selected - activate input mode
                state.feedback_input_active = True
            else:
                # Submit or Cancel button
                result = self._submit_confirm(state, questions)
                if result is True:
                    # Successfully submitted, return responses
                    return False
                elif result == "cancel":
                    # Cancel button - exit the survey
                    raise KeyboardInterrupt
        elif key == InputHandler.CTRL_C or key == InputHandler.ESC:
            raise KeyboardInterrupt

        return True

    def _render_feedback_field(self, state: SurveyState):
        """Render the feedback field"""
        if state.feedback_input_active:
            feedback_prompt = self.renderer.render_text(
                "还有其他想补充的信息吗？ (可选)",
                color=self.renderer.BOLD
            )
            print(feedback_prompt)
            # Show feedback with cursor position
            if state.feedback:
                # Insert cursor indicator at current position
                feedback_display = (state.feedback[:state.feedback_cursor_pos] + "|" +
                                  state.feedback[state.feedback_cursor_pos:])
            else:
                feedback_display = "|"
            feedback_input = f"  {feedback_display}"
            print(self.renderer.render_text(feedback_input, color=self.renderer.DIM))
        else:
            if state.submit_option_index == 2:
                feedback_prompt = self.renderer.render_text(
                    "还有其他想补充的信息吗？ (可选) [已选中]",
                    color=self.renderer.BOLD if state.submit_option_index == 2 else self.renderer.DIM
                )
            else:
                feedback_prompt = self.renderer.render_text(
                    "还有其他想补充的信息吗？ (可选)",
                    color=self.renderer.DIM
                )
            print(feedback_prompt)
            if state.feedback:
                print(f"  {self.renderer.render_text(state.feedback, color=self.renderer.BOLD)}")
            else:
                print(self.renderer.render_text("  (未填写)", color=self.renderer.DIM))

    def _submit_move_up(self, state: SurveyState):
        """Move up in submit options (circular navigation)"""
        # Navigate: Submit (0) ↔ Cancel (1) ↔ Feedback (2)
        state.submit_option_index = (state.submit_option_index - 1) % 3

    def _submit_move_down(self, state: SurveyState):
        """Move down in submit options (circular navigation)"""
        # Navigate: Submit (0) ↔ Cancel (1) ↔ Feedback (2)
        state.submit_option_index = (state.submit_option_index + 1) % 3

    def _submit_confirm(self, state: SurveyState,
                       questions: List[Question]) -> bool:
        """Handle submit button confirmation"""
        if state.submit_option_index == 0:  # Submit button
            missing = self._get_missing_required(state, questions)
            if missing:
                # Has missing required questions - don't submit
                return False
            # All required questions answered
            return True
        elif state.submit_option_index == 1:  # Cancel button
            return "cancel"
        elif state.submit_option_index == 2:  # Feedback field
            return False

    def _get_missing_required(self, state: SurveyState,
                            questions: List[Question]) -> List[str]:
        """Get list of required questions that haven't been answered"""
        missing = []
        for question in questions:
            if not question.required:
                continue

            # Check if question has been answered
            if question.id in state.responses:
                continue

            # For multiple choice, also check selected_options
            if question.type == "multiple_choice":
                if question.id in state.selected_options and state.selected_options[question.id]:
                    continue

            missing.append(question.id)
        return missing
