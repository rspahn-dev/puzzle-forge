"""Built-in word banks used when no Anthropic API key is configured.

Not a substitute for live LLM generation — just enough curated themes
(plus a generic fallback) to make the app usable with zero setup.
"""
import random

THEME_BANKS = {
    "animals": ["TIGER", "ELEPHANT", "GIRAFFE", "MONKEY", "RABBIT", "PANDA", "CHEETAH", "DOLPHIN",
                "KANGAROO", "ZEBRA", "LEOPARD", "OTTER", "BEAVER", "RACCOON", "HEDGEHOG"],
    "ocean": ["WHALE", "DOLPHIN", "OCTOPUS", "STARFISH", "CORAL", "SHARK", "JELLYFISH", "SEAHORSE",
              "LOBSTER", "PLANKTON", "STINGRAY", "URCHIN", "ANCHOR", "HARBOR", "TIDEPOOL"],
    "space": ["GALAXY", "PLANET", "COMET", "METEOR", "ROCKET", "NEBULA", "ASTEROID", "SATELLITE",
              "ECLIPSE", "ORBIT", "TELESCOPE", "SUPERNOVA", "GRAVITY", "MOONDUST", "STARLIGHT"],
    "sports": ["SOCCER", "TENNIS", "HOCKEY", "BASEBALL", "BASKETBALL", "SWIMMING", "CYCLING",
               "WRESTLING", "ARCHERY", "BOWLING", "SPRINTER", "REFEREE", "STADIUM", "TROPHY"],
    "food": ["PASTA", "PIZZA", "BURRITO", "PANCAKE", "SANDWICH", "NOODLES", "DUMPLING", "OMELETTE",
             "CASSEROLE", "BAGUETTE", "PRETZEL", "WAFFLE", "CUPCAKE", "LASAGNA"],
    "fruits and vegetables": ["APPLE", "BANANA", "CARROT", "BROCCOLI", "PUMPKIN", "SPINACH",
                               "AVOCADO", "PINEAPPLE", "CUCUMBER", "RADISH", "ARTICHOKE", "ZUCCHINI"],
    "halloween": ["PUMPKIN", "SKELETON", "VAMPIRE", "ZOMBIE", "WEREWOLF", "GOBLIN", "COSTUME",
                  "CAULDRON", "PHANTOM", "CANDLE", "SPIDERWEB", "GRAVEYARD", "LANTERN"],
    "christmas": ["REINDEER", "SLEIGH", "GARLAND", "MISTLETOE", "CANDYCANE", "SNOWFLAKE", "ORNAMENT",
                  "CHIMNEY", "STOCKING", "TINSEL", "WREATH", "CAROLING", "GINGERBREAD"],
    "weather": ["THUNDER", "LIGHTNING", "BLIZZARD", "DROUGHT", "RAINBOW", "HURRICANE", "TORNADO",
                "FORECAST", "HUMIDITY", "SUNSHINE", "OVERCAST", "FROSTBITE"],
    "dinosaurs": ["TRICERATOPS", "VELOCIRAPTOR", "STEGOSAURUS", "PTERODACTYL", "FOSSIL", "JURASSIC",
                  "PREHISTORIC", "REPTILE", "EXTINCT", "SKELETON", "CARNIVORE", "HERBIVORE"],
    "music": ["GUITAR", "TRUMPET", "VIOLIN", "DRUMKIT", "CLARINET", "PIANO", "MELODY", "RHYTHM",
              "ORCHESTRA", "CONCERT", "HARMONY", "BALLAD", "TROMBONE", "SAXOPHONE"],
    "school": ["PENCIL", "NOTEBOOK", "TEACHER", "CLASSROOM", "HOMEWORK", "BACKPACK", "SCIENCE",
               "HISTORY", "LIBRARY", "CALENDAR", "CHALKBOARD", "RECESS", "SEMESTER"],
    "vehicles": ["BICYCLE", "AIRPLANE", "HELICOPTER", "SUBMARINE", "MOTORCYCLE", "TRACTOR", "SCOOTER",
                 "FREIGHT", "CARAVAN", "SAILBOAT", "MONORAIL", "BULLDOZER"],
    "birds": ["EAGLE", "SPARROW", "FLAMINGO", "PENGUIN", "PARROT", "TOUCAN", "OSTRICH", "PEACOCK",
              "FALCON", "PELICAN", "WOODPECKER", "HUMMINGBIRD"],
    "flowers": ["DAISY", "TULIP", "ORCHID", "SUNFLOWER", "LAVENDER", "MARIGOLD", "PETUNIA",
                "HIBISCUS", "CARNATION", "MAGNOLIA", "BUTTERCUP", "DANDELION"],
}

THEME_KEYWORDS = {
    "animals": ["animal", "zoo", "wildlife", "safari", "pet"],
    "ocean": ["ocean", "sea", "marine", "underwater", "beach", "aquatic"],
    "space": ["space", "astronomy", "galaxy", "cosmic", "universe", "star"],
    "sports": ["sport", "athletic", "game", "olympic"],
    "food": ["food", "cooking", "kitchen", "meal", "cuisine", "restaurant"],
    "fruits and vegetables": ["fruit", "vegetable", "produce", "garden food"],
    "halloween": ["halloween", "spooky", "scary", "horror"],
    "christmas": ["christmas", "holiday", "xmas", "santa", "winter holiday"],
    "weather": ["weather", "climate", "storm", "meteorology"],
    "dinosaurs": ["dinosaur", "dino", "prehistoric"],
    "music": ["music", "band", "instrument", "song"],
    "school": ["school", "classroom", "education", "study"],
    "vehicles": ["vehicle", "car", "transport", "transportation"],
    "birds": ["bird", "avian"],
    "flowers": ["flower", "plant", "botanical", "garden"],
}

GENERIC_BANK = [
    "SUNSET", "MOUNTAIN", "JOURNEY", "CANDLE", "WHISPER", "HARBOR", "MEADOW", "LANTERN",
    "COMPASS", "RIVER", "SHADOW", "GARDEN", "THUNDER", "CRYSTAL", "VELVET", "HORIZON",
    "ISLAND", "PUZZLE", "BREEZE", "ECHO", "FOREST", "GLACIER", "ORCHARD", "TWILIGHT",
]


def get_offline_word_list(theme: str, count: int = 12, min_len: int = 4, max_len: int = 10) -> list[str]:
    theme_lower = theme.strip().lower()

    bank_key = None
    if theme_lower in THEME_BANKS:
        bank_key = theme_lower
    else:
        for key, keywords in THEME_KEYWORDS.items():
            if any(kw in theme_lower or theme_lower in kw for kw in keywords):
                bank_key = key
                break

    words = list(THEME_BANKS[bank_key]) if bank_key else list(GENERIC_BANK)

    filtered = [w for w in words if min_len <= len(w) <= max_len]
    random.shuffle(filtered)

    if len(filtered) < count:
        extra = [w for w in GENERIC_BANK if w not in filtered and min_len <= len(w) <= max_len]
        random.shuffle(extra)
        filtered.extend(extra)

    return filtered[:count]
