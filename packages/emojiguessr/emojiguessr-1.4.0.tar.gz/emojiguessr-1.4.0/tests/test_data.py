import pytest
from emojiguessr import data

class Tests:
    #
    # Fixtures - these are functions that can do any optional setup or teardown before or after a test function is run.
    #

    @pytest.fixture
    def example_fixture(self):
        """
        An example of a pytest fixture - a function that can be used for setup and teardown before and after test functions are run.
        """

        # place any setup you want to do before any test function that uses this fixture is run

        yield  # at th=e yield point, the test function will run and do its business

        # place with any teardown you want to do after any test function that uses this fixture has completed


    #
    # Test functions
    #

    def test_sanity_check(self, example_fixture):
        """
        Test debugging... making sure that we can run a simple test that always passes.
        Note the use of the example_fixture in the parameter list - any setup and teardown in that fixture will be run before and after this test function executes
        From the main project directory, run the `python3 -m pytest` command to run all tests.
        """
        expected = True  # the value we expect to be present
        actual = True  # the value we see in reality
        assert actual == expected, "Expected True to be equal to True!"

    def test_random_emojis_default(self):
        """
        Verify random_emojis() function and make sure it returns the correct number of emojis.
        """
        # test with default parameters
        actual = data.random_emojis()
        assert (
            len(actual) == 3
        ), f"Expected random_emojis() to return 3 emojis by default. Instead, it returned {len(actual)} emojis."

        # test with counts for food
        default_len_actual = len(data._EMOJI_BANK["food"])
        for i in range(default_len_actual):
            actual = data.random_emojis(i)
            assert (
                len(actual) == i
            ), f"Expected random_emojis({i}) to return {i} emojis. Instead, it returned {len(actual)} emojis."
    
    def test_random_emojis_all(self):
        """
        Verify random_emojis() function when theme is invalid and it returns all emojis
        """
        # test with invalid theme
        all_emoji = [e for v in data._EMOJI_BANK.values() for (e, _) in v]
        all_len_actual = len(all_emoji)
        for i in range(all_len_actual):
            actual = data.random_emojis(i, theme="invalid_theme")
            assert (
                len(actual) == i
            ), f"Expected random_emojis({i}, theme='invalid_theme') to return {i} emojis. Instead, it returned {len(actual)} emojis."
    
    def test_random_emojis_animals(self):
        """
        Verify random_emojis() function for animals theme
        """
        # test with counts for animals
        animals_len_actual = len(data._EMOJI_BANK["animals"])
        for i in range(animals_len_actual):
            actual = data.random_emojis(i, theme="animals")
            assert (
                len(actual) == i
            ), f"Expected random_emojis({i}, theme='animals') to return {i} emojis. Instead, it returned {len(actual)} emojis."

    def test_random_emojis_themes(self):
        """
        Verify random_emojis() function works for all themes
        """

        for theme in data._EMOJI_BANK.keys():
            theme_len_actual = len(data._EMOJI_BANK[theme])
            for i in range(theme_len_actual):
                actual = data.random_emojis(i, theme=theme)
                assert (
                    len(actual) == i
                ), f"Expected random_emojis({i}, theme='{theme}') to return {i} emojis. Instead, it returned {len(actual)} emojis."





    def test_get_theme_item_default(self):
        """
        Verify get_theme_item() function with default parameters
        """

        food_actual = data._EMOJI_BANK["food"]
        actual = data.get_theme_item()
        assert (
            actual in food_actual
        ), f"Expected get_theme_item() to return an item from the food theme. Instead, it returned {actual}."

    def test_get_theme_item_invalid(self):
        """
        Verify get_theme_item() function with invalid theme
        """

        food_actual = data._EMOJI_BANK["food"]
        actual = data.get_theme_item("invalid")
        assert (
            actual in food_actual
        ), f"Expected get_theme_item() to return an item from the food theme. Instead, it returned {actual}."

    def test_get_theme_item_all(self):
        """
        Verify get_theme_item() function works for all themes
        """

        for theme in data._EMOJI_BANK:
            theme_actual = data._EMOJI_BANK[theme]
            actual = data.get_theme_item(theme)
            assert (
                actual in theme_actual
            ) , f"Expected get_theme_item('{theme}') to return an item from the {theme} theme. Instead, it returned {actual}."