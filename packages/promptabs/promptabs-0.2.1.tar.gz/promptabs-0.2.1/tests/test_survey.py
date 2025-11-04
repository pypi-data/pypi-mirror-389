"""Tests for SurveyRunner class"""

import pytest
from promptabs.survey import SurveyRunner
from promptabs.types import Question, Survey


def create_sample_survey():
    """Helper to create sample survey"""
    return Survey(
        questions=[
            Question(
                id="q1",
                title="Question 1",
                question="What is option 1?",
                options=["A", "B", "C"],
            ),
            Question(
                id="q2",
                title="Question 2",
                question="What is option 2?",
                options=["X", "Y"],
            ),
        ]
    )


def test_survey_creation():
    """Test survey creation"""
    survey_obj = create_sample_survey()
    runner = SurveyRunner(survey_obj)
    assert len(runner.questions) == 2
    assert runner.current_tab_index == 0


def test_survey_validation_empty_questions():
    """Test that empty questions list raises ValueError"""
    with pytest.raises(ValueError):
        SurveyRunner(Survey(questions=[]))


def test_survey_tab_navigation():
    """Test moving to next and previous tabs (circular navigation)"""
    survey_obj = create_sample_survey()
    runner = SurveyRunner(survey_obj)
    num_tabs = len(survey_obj.questions) + 1  # 2 questions + 1 submit tab = 3 tabs

    # Start at tab 0
    assert runner.current_tab_index == 0

    # Move to next tab
    runner._move_to_next_tab()
    assert runner.current_tab_index == 1

    # Move to next tab again (reaches submit tab)
    runner._move_to_next_tab()
    assert runner.current_tab_index == 2
    assert runner._is_submit_tab()

    # Move to next tab wraps around to first tab
    runner._move_to_next_tab()
    assert runner.current_tab_index == 0

    # Move to previous tab
    runner._move_to_previous_tab()
    assert runner.current_tab_index == 2  # Wraps to submit tab
    assert runner._is_submit_tab()

    # Move to previous tab
    runner._move_to_previous_tab()
    assert runner.current_tab_index == 1


def test_survey_option_navigation():
    """Test moving between options"""
    survey_obj = create_sample_survey()
    runner = SurveyRunner(survey_obj)

    q_id = survey_obj.questions[0].id

    # Start at option 0
    assert runner.current_option_index[q_id] == 0

    # Move to next option
    runner._move_to_next_option()
    assert runner.current_option_index[q_id] == 1

    # Move to next option
    runner._move_to_next_option()
    assert runner.current_option_index[q_id] == 2

    # Can't move beyond last option
    runner._move_to_next_option()
    assert runner.current_option_index[q_id] == 2

    # Move to previous option
    runner._move_to_previous_option()
    assert runner.current_option_index[q_id] == 1

    # Move to previous option
    runner._move_to_previous_option()
    assert runner.current_option_index[q_id] == 0

    # Can't move before first option
    runner._move_to_previous_option()
    assert runner.current_option_index[q_id] == 0


def test_survey_confirm_selection():
    """Test confirming a selection"""
    survey_obj = create_sample_survey()
    runner = SurveyRunner(survey_obj)

    # Confirm selection for first question
    runner._confirm_selection()

    # Should be in responses
    assert "q1" in runner.responses
    assert runner.responses["q1"] == "A"  # First option

    # Should move to next tab
    assert runner.current_tab_index == 1


def test_survey_selection_with_different_option():
    """Test confirming a non-default selection"""
    survey_obj = create_sample_survey()
    runner = SurveyRunner(survey_obj)

    # Move to second option
    runner._move_to_next_option()
    runner._move_to_next_option()

    # Confirm selection
    runner._confirm_selection()

    # Should be in responses with correct value
    assert runner.responses["q1"] == "C"


def test_survey_submit_tab_detection():
    """Test submit tab detection"""
    survey_obj = create_sample_survey()
    runner = SurveyRunner(survey_obj)

    # Start: not on submit tab
    assert not runner._is_submit_tab()

    # After all questions: on submit tab
    runner.current_tab_index = len(survey_obj.questions)
    assert runner._is_submit_tab()


def test_survey_missing_required():
    """Test detection of missing required answers"""
    survey_obj = Survey(
        questions=[
            Question(
                id="q1",
                title="Required Q",
                question="Is this required?",
                options=["A", "B"],
                required=True,
            ),
            Question(
                id="q2",
                title="Optional Q",
                question="Is this optional?",
                options=["X", "Y"],
                required=False,
            ),
        ]
    )
    runner = SurveyRunner(survey_obj)

    # No answers yet
    missing = runner._get_missing_required()
    assert len(missing) == 1
    assert "q1" in missing

    # Answer required question
    runner.responses["q1"] = "A"
    missing = runner._get_missing_required()
    assert len(missing) == 0

    # Optional question still unanswered, but not in missing
    assert "q2" not in missing


def test_survey_submit_options_navigation():
    """Test navigating submit options (circular navigation)"""
    survey_obj = create_sample_survey()
    runner = SurveyRunner(survey_obj)

    # Move to submit tab
    runner.current_tab_index = len(survey_obj.questions)

    # Start at Submit button (index 0)
    assert runner.submit_option_index == 0

    # Move down to Cancel (index 1)
    runner._submit_move_down()
    assert runner.submit_option_index == 1

    # Move down to Feedback (index 2)
    runner._submit_move_down()
    assert runner.submit_option_index == 2

    # Move down wraps back to Submit (index 0)
    runner._submit_move_down()
    assert runner.submit_option_index == 0

    # Move up from Submit wraps to Feedback (index 2)
    runner._submit_move_up()
    assert runner.submit_option_index == 2

    # Move up to Cancel (index 1)
    runner._submit_move_up()
    assert runner.submit_option_index == 1

    # Move up to Submit (index 0)
    runner._submit_move_up()
    assert runner.submit_option_index == 0


def test_survey_navigate_back_from_submit():
    """Test that left arrow on submit tab returns to previous question"""
    survey_obj = create_sample_survey()
    runner = SurveyRunner(survey_obj)

    # Move to submit tab
    runner.current_tab_index = len(survey_obj.questions)
    assert runner._is_submit_tab()

    # Move left (back to previous question)
    runner._move_to_previous_tab()

    # Should be on the last question, not submit tab
    assert not runner._is_submit_tab()
    assert runner.current_tab_index == len(survey_obj.questions) - 1


def test_survey_circular_navigation_forward():
    """Test circular navigation going forward (right arrow)"""
    survey_obj = create_sample_survey()
    runner = SurveyRunner(survey_obj)

    # From first question, going right multiple times
    num_tabs = len(survey_obj.questions) + 1  # questions + submit tab

    for _ in range(num_tabs):
        runner._move_to_next_tab()

    # Should wrap back to first question
    assert runner.current_tab_index == 0


def test_survey_circular_navigation_backward():
    """Test circular navigation going backward (left arrow)"""
    survey_obj = create_sample_survey()
    runner = SurveyRunner(survey_obj)

    # From first question, going left wraps to submit tab
    runner.current_tab_index = 0
    runner._move_to_previous_tab()

    assert runner._is_submit_tab()
    assert runner.current_tab_index == len(survey_obj.questions)


def test_survey_submit_with_missing_required():
    """Test that submit is prevented when required questions are missing"""
    survey_obj = Survey(
        questions=[
            Question(id="q1", title="Q1", question="Question 1?", options=["A", "B"], required=True),
            Question(id="q2", title="Q2", question="Question 2?", options=["X", "Y"], required=True),
        ]
    )
    runner = SurveyRunner(survey_obj)

    # Move to submit tab
    runner.current_tab_index = len(survey_obj.questions)
    runner.submit_option_index = 0  # On Submit button

    # Try to submit without answering
    result = runner._submit_confirm()

    # Should return False (submission blocked)
    assert result is False


def test_survey_submit_with_all_required():
    """Test that submit succeeds when all required questions answered"""
    survey_obj = Survey(
        questions=[
            Question(id="q1", title="Q1", question="Question 1?", options=["A", "B"], required=True),
            Question(id="q2", title="Q2", question="Question 2?", options=["X", "Y"], required=True),
        ]
    )
    runner = SurveyRunner(survey_obj)

    # Answer all required questions
    runner.responses["q1"] = "A"
    runner.responses["q2"] = "X"

    # Move to submit tab
    runner.current_tab_index = len(survey_obj.questions)
    runner.submit_option_index = 0  # On Submit button

    # Try to submit
    result = runner._submit_confirm()

    # Should return True (submission allowed)
    assert result is True


def test_survey_multiple_choice_selection():
    """Test multiple choice question selection toggling"""
    survey_obj = Survey(
        questions=[
            Question(
                id="q1",
                title="Languages",
                question="Which programming languages do you know?",
                options=["Python", "JavaScript", "Go"],
                type="multiple_choice",
                required=True,
            ),
        ]
    )
    runner = SurveyRunner(survey_obj)

    # Toggle first option
    runner._toggle_option_selection()
    assert "Python" in runner.selected_options["q1"]
    assert len(runner.selected_options["q1"]) == 1

    # Move to next option and toggle
    runner._move_to_next_option()
    runner._toggle_option_selection()
    assert "JavaScript" in runner.selected_options["q1"]
    assert len(runner.selected_options["q1"]) == 2

    # Toggle first option again to deselect it
    runner._move_to_previous_option()
    runner._toggle_option_selection()
    assert "Python" not in runner.selected_options["q1"]
    assert "JavaScript" in runner.selected_options["q1"]
    assert len(runner.selected_options["q1"]) == 1


def test_survey_multiple_choice_with_missing_required():
    """Test that multiple choice validates as required"""
    survey_obj = Survey(
        questions=[
            Question(
                id="q1",
                title="Options",
                question="Select options",
                options=["A", "B"],
                type="multiple_choice",
                required=True,
            ),
        ]
    )
    runner = SurveyRunner(survey_obj)

    # No options selected yet
    missing = runner._get_missing_required()
    assert "q1" in missing

    # Select one option
    runner.selected_options["q1"].add("A")
    missing = runner._get_missing_required()
    assert "q1" not in missing

    # Deselect option
    runner.selected_options["q1"].remove("A")
    missing = runner._get_missing_required()
    assert "q1" in missing
