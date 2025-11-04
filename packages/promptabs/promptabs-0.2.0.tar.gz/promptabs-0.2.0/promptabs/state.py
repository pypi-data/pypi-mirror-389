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
