import pytest
from unittest.mock import patch
from emojiguessr.quiz import make_quiz_item, check_answer


def test_make_quiz_item():
    """
    Verify make_quiz_item() function returns a dictionary with correct structure
    and uses the theme parameter correctly.
    """
    with patch("emojiguessr.quiz.get_theme_item") as mock_get_theme_item:
        mock_get_theme_item.return_value = ("🍔", "burger")
        
        result = make_quiz_item(theme="food")
        
        assert isinstance(result, dict), "Expected make_quiz_item() to return a dictionary"
        assert "clue" in result, "Expected 'clue' key in result"
        assert "answer" in result, "Expected 'answer' key in result"
        assert "theme" in result, "Expected 'theme' key in result"
        assert result["clue"] == "🍔", f"Expected clue to be '🍔', got {result['clue']}"
        assert result["answer"] == "burger", f"Expected answer to be 'burger', got {result['answer']}"
        assert result["theme"] == "food", f"Expected theme to be 'food', got {result['theme']}"
        mock_get_theme_item.assert_called_once_with("food")


def test_check_answer():
    """
    Verify check_answer() function correctly validates answers with different
    combinations of case_sensitive and allow_partial parameters.
    """
    # Test case-insensitive, partial matching (default)
    assert check_answer("burger", "bur") == True, "Expected 'bur' to match 'burger' (case-insensitive, partial)"
    assert check_answer("Burger", "bur") == True, "Expected 'bur' to match 'Burger' (case-insensitive, partial)"
    assert check_answer("burger", "burger") == True, "Expected 'burger' to match 'burger' (case-insensitive, partial)"
    assert check_answer("burger", "hamburger") == False, "Expected 'hamburger' not to match 'burger' (case-insensitive, partial)"
    
    # Test case-insensitive, no partial matching
    assert check_answer("burger", "bur", case_sensitive=False, allow_partial=False) == False, "Expected 'bur' not to match 'burger' (case-insensitive, no partial)"
    assert check_answer("burger", "burger", case_sensitive=False, allow_partial=False) == True, "Expected 'burger' to match 'burger' (case-insensitive, no partial)"
    assert check_answer("Burger", "burger", case_sensitive=False, allow_partial=False) == True, "Expected 'burger' to match 'Burger' (case-insensitive, no partial)"
    
    # Test case-sensitive, partial matching
    assert check_answer("burger", "bur", case_sensitive=True, allow_partial=True) == True, "Expected 'bur' to match 'burger' (case-sensitive, partial)"
    assert check_answer("Burger", "bur", case_sensitive=True, allow_partial=True) == False, "Expected 'bur' not to match 'Burger' (case-sensitive, partial)"
    assert check_answer("Burger", "Bur", case_sensitive=True, allow_partial=True) == True, "Expected 'Bur' to match 'Burger' (case-sensitive, partial)"
    
    # Test case-sensitive, no partial matching
    assert check_answer("burger", "bur", case_sensitive=True, allow_partial=False) == False, "Expected 'bur' not to match 'burger' (case-sensitive, no partial)"
    assert check_answer("burger", "burger", case_sensitive=True, allow_partial=False) == True, "Expected 'burger' to match 'burger' (case-sensitive, no partial)"
    assert check_answer("Burger", "burger", case_sensitive=True, allow_partial=False) == False, "Expected 'burger' not to match 'Burger' (case-sensitive, no partial)"

