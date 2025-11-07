"""
Survey state management - Centralized state container
"""

from typing import Dict, Union, List, Set, Optional


class SurveyState:
    """
    Centralized state container for survey management.

    Replaces the 12 scattered state variables in the original Survey class.
    """

    def __init__(self, num_questions: int):
        """
        Initialize the survey state.

        Args:
            num_questions: Total number of questions in the survey
        """
        # Tab navigation
        self.current_tab_index: int = 0

        # Responses storage
        self.responses: Dict[str, Union[str, List[str]]] = {}

        # Multiple choice selections (question_id -> set of selected options)
        self.selected_options: Dict[str, Set[str]] = {}

        # Feedback field
        self.feedback: str = ""
        self.feedback_cursor_pos: int = 0
        self.feedback_input_active: bool = False

        # Question navigation
        self.current_option_index: Dict[str, int] = {}

        # Custom input state (question_id -> custom input text)
        self.custom_input_text: Dict[str, str] = {}
        self.custom_input_active: Dict[str, bool] = {}
        self.custom_input_cursor_pos: Dict[str, int] = {}

        # Submit page navigation
        self.submit_option_index: int = 0

        # Store number of questions for validation
        self._num_questions = num_questions

    def reset_submit_tab_state(self):
        """Reset state when entering the submit tab"""
        self.submit_option_index = 0
        self.feedback_input_active = False

    def reset_feedback(self):
        """Reset feedback-related state"""
        self.feedback = ""
        self.feedback_cursor_pos = 0
        self.feedback_input_active = False

    def enter_custom_input_mode(self, question_id: str):
        """Enter custom input edit mode for a question"""
        self.custom_input_active[question_id] = True
        if question_id not in self.custom_input_text:
            self.custom_input_text[question_id] = ""
        # Initialize cursor at the end of text
        self.custom_input_cursor_pos[question_id] = len(self.custom_input_text[question_id])

    def exit_custom_input_mode(self, question_id: str):
        """Exit custom input edit mode for a question"""
        self.custom_input_active[question_id] = False

    def add_custom_input_char(self, question_id: str, char: str):
        """Add a character to custom input text"""
        if question_id not in self.custom_input_text:
            self.custom_input_text[question_id] = ""
        self.custom_input_text[question_id] += char

    def backspace_custom_input(self, question_id: str):
        """Remove last character from custom input text"""
        if question_id in self.custom_input_text and self.custom_input_text[question_id]:
            self.custom_input_text[question_id] = self.custom_input_text[question_id][:-1]

    def clear_custom_input(self, question_id: str):
        """Clear custom input text for a question"""
        self.custom_input_text[question_id] = ""
        self.custom_input_active[question_id] = False
        self.custom_input_cursor_pos[question_id] = 0

    def get_custom_input(self, question_id: str) -> str:
        """Get custom input text for a question"""
        return self.custom_input_text.get(question_id, "")

    def move_custom_input_cursor_left(self, question_id: str):
        """Move cursor left in custom input text"""
        if question_id not in self.custom_input_cursor_pos:
            self.custom_input_cursor_pos[question_id] = 0
        if self.custom_input_cursor_pos[question_id] > 0:
            self.custom_input_cursor_pos[question_id] -= 1

    def move_custom_input_cursor_right(self, question_id: str):
        """Move cursor right in custom input text"""
        if question_id not in self.custom_input_cursor_pos:
            self.custom_input_cursor_pos[question_id] = 0
        text_length = len(self.custom_input_text.get(question_id, ""))
        if self.custom_input_cursor_pos[question_id] < text_length:
            self.custom_input_cursor_pos[question_id] += 1

    def insert_custom_input_char_at_cursor(self, question_id: str, char: str):
        """Insert a character at cursor position in custom input text"""
        if question_id not in self.custom_input_text:
            self.custom_input_text[question_id] = ""
        if question_id not in self.custom_input_cursor_pos:
            self.custom_input_cursor_pos[question_id] = 0

        cursor_pos = self.custom_input_cursor_pos[question_id]
        text = self.custom_input_text[question_id]
        self.custom_input_text[question_id] = text[:cursor_pos] + char + text[cursor_pos:]
        self.custom_input_cursor_pos[question_id] += 1

    def delete_custom_input_char_at_cursor(self, question_id: str):
        """Delete character at cursor position (backspace behavior)"""
        if question_id not in self.custom_input_text:
            return
        if question_id not in self.custom_input_cursor_pos:
            self.custom_input_cursor_pos[question_id] = len(self.custom_input_text[question_id])

        if self.custom_input_cursor_pos[question_id] > 0:
            cursor_pos = self.custom_input_cursor_pos[question_id]
            text = self.custom_input_text[question_id]
            # Delete character before cursor (backspace)
            self.custom_input_text[question_id] = text[:cursor_pos - 1] + text[cursor_pos:]
            self.custom_input_cursor_pos[question_id] -= 1

    def initialize_question_state(self, question_ids: List[str],
                                 multiple_choice_ids: List[str]):
        """
        Initialize state for questions.

        Args:
            question_ids: List of all question IDs
            multiple_choice_ids: List of question IDs for multiple choice questions
        """
        self.current_option_index = {q_id: 0 for q_id in question_ids}
        self.selected_options = {q_id: set() for q_id in multiple_choice_ids}
        self.custom_input_text = {q_id: "" for q_id in question_ids}
        self.custom_input_active = {q_id: False for q_id in question_ids}
        self.custom_input_cursor_pos = {q_id: 0 for q_id in question_ids}

    def get_num_tabs(self) -> int:
        """Get total number of tabs (questions + submit tab)"""
        return self._num_questions + 1

    def is_submit_tab(self) -> bool:
        """Check if current tab is the submit tab"""
        return self.current_tab_index >= self._num_questions

    def move_next_tab(self):
        """Move to next tab with circular navigation"""
        self.current_tab_index = (self.current_tab_index + 1) % self.get_num_tabs()
        if self.is_submit_tab():
            self.reset_submit_tab_state()

    def move_previous_tab(self):
        """Move to previous tab with circular navigation"""
        self.current_tab_index = (self.current_tab_index - 1) % self.get_num_tabs()
        if self.is_submit_tab():
            self.reset_submit_tab_state()

    def set_question_response(self, question_id: str, response: str):
        """Set response for a single-choice question"""
        self.responses[question_id] = response

    def toggle_option_selection(self, question_id: str, option: str):
        """Toggle selection for a multiple-choice option"""
        if question_id not in self.selected_options:
            self.selected_options[question_id] = set()

        if option in self.selected_options[question_id]:
            self.selected_options[question_id].remove(option)
        else:
            self.selected_options[question_id].add(option)

    def get_display_responses(self) -> Dict[str, Union[str, List[str]]]:
        """Get responses formatted for display/submission"""
        display_responses = self.responses.copy()

        # Add multiple choice selections
        for q_id, selected_set in self.selected_options.items():
            if selected_set:  # Only include if something is selected
                display_responses[q_id] = sorted(list(selected_set))

        return display_responses

    def finalize_responses(self) -> Dict[str, Union[str, List[str]]]:
        """Get final responses including feedback if provided"""
        responses = self.get_display_responses()

        # Add feedback if provided
        if self.feedback and self.feedback.strip():
            responses['feedback'] = self.feedback.strip()

        return responses
