import pytest
from unittest.mock import patch
from emojiguessr.quiz import make_quiz_item, check_answer


def test_make_quiz_item():
    """
    Makes sure the quiz item comes back as a proper dictionary with all the right keys.
    
    Also checks that it actually uses whatever theme we pass in.
    """
    with patch("emojiguessr.quiz.get_theme_item") as mock_get_theme_item:
        mock_get_theme_item.return_value = ("🍔", "burger")
        
        result = make_quiz_item(theme="food")
        
        # Should give us a dictionary with clue, answer, and theme
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
    Runs through all the different ways check_answer can work - with and without
    case sensitivity, with and without partial matches. Want to make sure it handles
    all these combinations properly.
    """
    # By default, it should be case-insensitive and allow partial matches
    assert check_answer("burger", "bur") == True, "Expected 'bur' to match 'burger' (case-insensitive, partial)"
    assert check_answer("Burger", "bur") == True, "Expected 'bur' to match 'Burger' (case-insensitive, partial)"
    assert check_answer("burger", "burger") == True, "Expected 'burger' to match 'burger' (case-insensitive, partial)"
    assert check_answer("burger", "hamburger") == False, "Expected 'hamburger' not to match 'burger' (case-insensitive, partial)"
    
    # when partial matching is off, exact matches should still work (case-insensitive)
    assert check_answer("burger", "bur", case_sensitive=False, allow_partial=False) == False, "Expected 'bur' not to match 'burger' (case-insensitive, no partial)"
    assert check_answer("burger", "burger", case_sensitive=False, allow_partial=False) == True, "Expected 'burger' to match 'burger' (case-insensitive, no partial)"
    assert check_answer("Burger", "burger", case_sensitive=False, allow_partial=False) == True, "Expected 'burger' to match 'Burger' (case-insensitive, no partial)"
    
    # Case-sensitive mode should be strict about capitalization
    
    assert check_answer("burger", "bur", case_sensitive=True, allow_partial=True) == True, "Expected 'bur' to match 'burger' (case-sensitive, partial)"
    assert check_answer("Burger", "bur", case_sensitive=True, allow_partial=True) == False, "Expected 'bur' not to match 'Burger' (case-sensitive, partial)"
    assert check_answer("Burger", "Bur", case_sensitive=True, allow_partial=True) == True, "Expected 'Bur' to match 'Burger' (case-sensitive, partial)"
    
    # The strictest mode: case-sensitive and no partial matches
    assert check_answer("burger", "bur", case_sensitive=True, allow_partial=False) == False, "Expected 'bur' not to match 'burger' (case-sensitive, no partial)"
    assert check_answer("burger", "burger", case_sensitive=True, allow_partial=False) == True, "Expected 'burger' to match 'burger' (case-sensitive, no partial)"
    assert check_answer("Burger", "burger", case_sensitive=True, allow_partial=False) == False, "Expected 'burger' not to match 'Burger' (case-sensitive, no partial)"


def test_make_quiz_item_default_theme():
    """
    When you don't specify a theme, it should default to "food". 
    Just making sure the default behavior works as expected.
    """
    
    with patch("emojiguessr.quiz.get_theme_item") as mock_get_theme_item:
        mock_get_theme_item.return_value = ("🍕", "pizza")
        
        result = make_quiz_item()
        
        # Should default to "food" theme when nothing is passed
        assert result["theme"] == "food", f"Expected default theme to be 'food', got {result['theme']}"
        mock_get_theme_item.assert_called_once_with("food")


def test_check_answer_whitespace_handling():
    """
    Users might accidentally add extra spaces when typing answers. The function
    
    should strip whitespace so " burger " matches "burger". This is important
    for a good user experience.
    """
    # Extra spaces should be trimmed automatically
    
    assert check_answer("burger", " burger ") == True, "Should match even with extra spaces"
    assert check_answer("burger", "  BURGER  ") == True, "Should match with spaces and different case"
    assert check_answer("jurassic park", " jurassic ") == True, "Partial match should work with spaces too"
    
    # But when case-sensitive and no partial, spaces shouldn't matter
    assert check_answer("burger", " burger ", case_sensitive=False, allow_partial=False) == True, "Exact match should work with spaces"


def test_make_quiz_item_different_themes():
    """
    The quiz should work with any theme, not just food. Let's test a couple
    different themes to make sure it's flexible.
    """
    with patch("emojiguessr.quiz.get_theme_item") as mock_get_theme_item:
        # Test with movies theme
        mock_get_theme_item.return_value = ("🎬", "movie")
        result = make_quiz_item(theme="movies")
        assert result["theme"] == "movies", f"Expected theme to be 'movies', got {result['theme']}"
        assert result["clue"] == "🎬", f"Expected clue to be '🎬', got {result['clue']}"
        mock_get_theme_item.assert_called_with("movies")
        
        # Test with animals theme
        mock_get_theme_item.return_value = ("🐶", "dog")
        result = make_quiz_item(theme="animals")
        assert result["theme"] == "animals", f"Expected theme to be 'animals', got {result['theme']}"
        assert result["answer"] == "dog", f"Expected answer to be 'dog', got {result['answer']}"


def test_check_answer_multi_word_partial():
    """
    Multi-word answers like "jurassic park" should work with partial matching.
    Users might just type "jurassic" and that should count as correct.
    """
    
    assert check_answer("jurassic park", "jurassic") == True, "Partial match should work for multi-word answers"
    assert check_answer("jurassic park", "Jurassic") == True, "Case shouldn't matter for partial matches"
    assert check_answer("jurassic park", "jurassic park") == True, "Full match should obviously work"
    assert check_answer("jurassic park", "park") == False, "Should only match from the start, not the middle"


def test_check_answer_edge_cases():
    """
    Edge cases that might cause issues - empty strings, longer guesses, etc.
    Better to catch these now than when users find them.
    """
    # Empty string with partial matching - technically starts with empty string
    assert check_answer("burger", "") == True, "Empty string should match with partial (everything starts with '')"
    assert check_answer("burger", "", allow_partial=False) == False, "Empty string shouldn't match without partial"
    
    # Guess longer than answer shouldn't match
    assert check_answer("burger", "burger king") == False, "Guess longer than answer shouldn't match"
    assert check_answer("burger", "burger king", case_sensitive=True) == False, "Should still fail even case-sensitive"
    
    # Exact match should work even if guess has extra words conceptually
    assert check_answer("burger", "burger") == True, "Exact match should work"
    
    # Numbers and special characters should work
    assert check_answer("3d", "3d") == True, "Should handle numbers"
    
    assert check_answer("e-mail", "e-mail") == True, "Should handle hyphens"

