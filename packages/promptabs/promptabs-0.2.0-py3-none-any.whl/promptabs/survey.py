"""
SurveyRunner class for managing and running surveys
"""

import json
from typing import List, Dict, Union
from .types import Question, Results, Survey
from .terminal import TerminalRenderer, TabRenderer
from .input_handler import InputHandler
from .state import SurveyState
from .page import QuestionPage, SubmitPage


class SurveyRunner:
    """Main survey conductor for managing questions and collecting responses"""

    def __init__(self, survey: Survey):
        """
        Initialize a survey runner with a Survey object

        Args:
            survey: Survey object containing questions and metadata
        """
        if not survey.questions:
            raise ValueError("Survey must contain at least one question")

        self.survey = survey
        self.questions = survey.questions
        self.renderer = TerminalRenderer()
        self.tab_renderer = TabRenderer(self.renderer)
        self.input_handler = InputHandler()

        # Initialize centralized state
        self.state = SurveyState(len(self.questions))
        question_ids = [q.id for q in self.questions]
        multiple_choice_ids = [q.id for q in self.questions if q.type == "multiple_choice"]
        self.state.initialize_question_state(question_ids, multiple_choice_ids)

        # Initialize pages
        self.pages = self._create_pages()

    # Backward compatibility properties to access state attributes
    @property
    def current_tab_index(self) -> int:
        """Get current tab index from state"""
        return self.state.current_tab_index

    @current_tab_index.setter
    def current_tab_index(self, value: int):
        """Set current tab index in state"""
        self.state.current_tab_index = value

    @property
    def responses(self) -> Dict[str, Union[str, List[str]]]:
        """Get responses from state"""
        return self.state.responses

    @property
    def current_option_index(self) -> Dict[str, int]:
        """Get current option index from state"""
        return self.state.current_option_index

    @property
    def submit_option_index(self) -> int:
        """Get submit option index from state"""
        return self.state.submit_option_index

    @submit_option_index.setter
    def submit_option_index(self, value: int):
        """Set submit option index in state"""
        self.state.submit_option_index = value

    @property
    def feedback_input_active(self) -> bool:
        """Get feedback input active flag from state"""
        return self.state.feedback_input_active

    @property
    def selected_options(self) -> Dict[str, set]:
        """Get selected options from state"""
        return self.state.selected_options

    @staticmethod
    def from_json_file(filepath: str) -> "SurveyRunner":
        """
        Create a SurveyRunner from a JSON file

        Args:
            filepath: Path to JSON file containing survey

        Returns:
            SurveyRunner instance

        Example:
            runner = SurveyRunner.from_json_file('survey.json')
            responses = runner.run()
        """
        with open(filepath) as f:
            data = json.load(f)
        survey = Survey.model_validate(data)
        return SurveyRunner(survey)

    @staticmethod
    def from_json_string(json_string: str) -> "SurveyRunner":
        """
        Create a SurveyRunner from a JSON string

        Args:
            json_string: JSON string containing survey

        Returns:
            SurveyRunner instance

        Example:
            json_str = '''
            {
              "questions": [
                {
                  "id": "q1",
                  "title": "Your question?",
                  "question": "Please select an option",
                  "options": ["Option A", "Option B"]
                }
              ]
            }
            '''
            runner = SurveyRunner.from_json_string(json_str)
            responses = runner.run()
        """
        survey = Survey.model_validate_json(json_string)
        return SurveyRunner(survey)

    def run(self) -> Results:
        """
        Run the interactive survey

        Returns:
            Results object containing responses and optional feedback
        """
        try:
            self.renderer.hide_cursor()
            self._render_survey()

            # Main event loop - continues until successful submit
            while True:
                key = self.input_handler.read_single_key()

                # Get current page and handle key
                page = self.pages[self.state.current_tab_index]
                should_continue = page.handle_key(key, self.state, self.questions)

                if not should_continue:
                    # Submit was successful
                    responses_dict = self.state.finalize_responses()
                    # Extract feedback if present
                    feedback = responses_dict.pop('feedback', None)
                    # Create and return Results object
                    return Results(answers=responses_dict, feedback=feedback)

                # Re-render after handling key
                self._render_survey()

        finally:
            self.renderer.show_cursor()
            self.renderer.clear_screen()

    def _create_pages(self) -> List:
        """Create page instances for all questions and submit page"""
        pages = []
        for i, question in enumerate(self.questions):
            page = QuestionPage(i, self.tab_renderer, self.renderer)
            pages.append(page)

        # Add submit page
        pages.append(SubmitPage(self.tab_renderer, self.renderer))
        return pages

    def _render_survey(self):
        """Render the current survey state"""
        self.renderer.clear_screen()
        page = self.pages[self.state.current_tab_index]
        page.render(self.renderer, self.tab_renderer, self.state, self.questions)

    # Backward compatibility methods
    def _is_submit_tab(self) -> bool:
        """Check if we're on the submit/review tab"""
        return self.state.is_submit_tab()

    def _move_to_next_tab(self):
        """Move to the next tab (circular navigation)"""
        self.state.move_next_tab()

    def _move_to_previous_tab(self):
        """Move to the previous tab (circular navigation)"""
        self.state.move_previous_tab()

    def _move_to_next_option(self):
        """Move to the next option in current question"""
        if self._is_submit_tab():
            return

        current_question = self.questions[self.current_tab_index]
        max_index = len(current_question.options) - 1
        current_index = self.state.current_option_index.get(current_question.id, 0)
        if current_index < max_index:
            self.state.current_option_index[current_question.id] = current_index + 1

    def _move_to_previous_option(self):
        """Move to the previous option in current question"""
        if self._is_submit_tab():
            return

        current_question = self.questions[self.current_tab_index]
        current_index = self.state.current_option_index.get(current_question.id, 0)
        if current_index > 0:
            self.state.current_option_index[current_question.id] = current_index - 1

    def _submit_move_up(self):
        """Move up in submit options (circular navigation)"""
        self.state.submit_option_index = (self.state.submit_option_index - 1) % 3

    def _submit_move_down(self):
        """Move down in submit options (circular navigation)"""
        self.state.submit_option_index = (self.state.submit_option_index + 1) % 3

    def _confirm_selection(self):
        """Confirm the current selection and move to next question"""
        if self._is_submit_tab():
            return

        current_question = self.questions[self.current_tab_index]
        selected_index = self.state.current_option_index.get(current_question.id, 0)
        selected_option = current_question.options[selected_index]
        self.state.set_question_response(current_question.id, selected_option)
        self._move_to_next_tab()

    def _submit_confirm(self):
        """Handle submit button confirmation"""
        if not self._is_submit_tab():
            return

        if self.state.submit_option_index == 0:  # Submit button
            missing = self._get_missing_required()
            if missing:
                return False
            return True
        elif self.state.submit_option_index == 1:  # Cancel button
            return "cancel"
        elif self.state.submit_option_index == 2:  # Feedback field
            return False

    def _get_missing_required(self) -> List[str]:
        """Get list of required questions that haven't been answered"""
        missing = []
        for question in self.questions:
            if not question.required:
                continue

            if question.id in self.state.responses:
                continue

            if question.type == "multiple_choice":
                if question.id in self.state.selected_options and self.state.selected_options[question.id]:
                    continue

            missing.append(question.id)
        return missing

    def _toggle_option_selection(self):
        """Toggle selection of current option for multiple choice questions"""
        if self._is_submit_tab():
            return

        current_question = self.questions[self.current_tab_index]
        if current_question.type != "multiple_choice":
            return

        selected_index = self.state.current_option_index.get(current_question.id, 0)
        selected_option = current_question.options[selected_index]
        self.state.toggle_option_selection(current_question.id, selected_option)
