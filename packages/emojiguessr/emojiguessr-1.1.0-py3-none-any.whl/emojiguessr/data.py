import random

_EMOJI_BANK = {
    "food": [
        ("🍕", "pizza"),
        ("🍣", "sushi"),
        ("🍔", "burger"),
        ("🍟", "fries"),
        ("🌮", "taco"),
        ("🍜", "ramen"),
        ("🥐", "croissant"),
        ("🍩", "donut"),
        ("🍎", "apple"),
        ("🍰", "cake"),
    ],
    "animals": [
        ("🐶", "dog"),
        ("🐱", "cat"),
        ("🐼", "panda"),
        ("🦁", "lion"),
        ("🐸", "frog"),
        ("🐧", "penguin"),
        ("🦊", "fox"),
        ("🐘", "elephant"),
        ("🐢", "turtle"),
        ("🦄", "unicorn"),
    ],
    "movies": [
        ("🧙‍♂️💍", "lord of the rings"),
        ("🚢🧊", "titanic"),
        ("🦖🏞️", "jurassic park"),
        ("👸🏼❄️", "frozen"),
        ("🧔⚡", "harry potter"),
        ("👨‍🚀🌕", "space movie"),
        ("🦸‍♂️", "superman"),
        ("🚗💨", "fast and furious"),
    ],
    "games": [
        ("🎮", "video game"),
        ("♟️", "chess"),
        ("🃏", "card game"),
        ("🎯", "darts"),
        ("🕹️", "arcade"),
        ("🎲", "board game"),
    ],
    "cities": [
        ("🇺🇸🗽", "new york"),
        ("🇫🇷🗼", "paris"),
        ("🇬🇧🎡", "london"),
        ("⛩️🌸", "kyoto"),
        ("🇯🇵🗼", "tokyo"),
        ("🇦🇺🌉", "sydney"),
        ("🇮🇹🏛️", "rome"),
        ("🇪🇬🕌", "cairo"),
        ("🇧🇷🎭", "rio de janeiro"),
        ("🇨🇳🐼", "chengdu"),
    ],
    "feelings": [
        ("😀", "happy"),
        ("😢", "sad"),
        ("😡", "angry"),
        ("🤔", "thinking"),
        ("🥱", "tired"),
        ("🤒", "sick"),
        ("😎", "cool"),
        ("🥳", "celebrating"),
    ],
    "dev": [
        ("💻☕", "coding"),
        ("🐍📦", "python package"),
        ("🐛🔍", "debugging"),
        ("📦⬆️", "deploy"),
        ("🧪✅", "tests passing"),
        ("⚠️🐛", "bug"),
    ],
}


def random_emojis(count=3, theme="food"):
    items = _EMOJI_BANK.get(theme)
    if not items:
        all_emoji = [e for v in _EMOJI_BANK.values() for (e, _) in v]
        random.shuffle(all_emoji)
        return all_emoji[: min(count, len(all_emoji))]
    emojis = [e for (e, _) in items]
    random.shuffle(emojis)
    return emojis[:count]


def get_theme_item(theme="food"):
    items = _EMOJI_BANK.get(theme)
    if not items:
        items = _EMOJI_BANK["food"]
    return random.choice(items)
