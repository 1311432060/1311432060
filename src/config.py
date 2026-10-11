import os

GITHUB_API = "https://api.github.com"
GITHUB_GRAPHQL_API = "https://api.github.com/graphql"

USERNAME = os.getenv("GH_USERNAME", "1311432060")

TOKEN = os.getenv("GH_TOKEN") or os.getenv("GITHUB_TOKEN") or ""

OUTPUT_DIR = os.getenv("OUTPUT_DIR", "output")
STATS_IMAGE = os.getenv("STATS_IMAGE", "stats.png")
LANGS_IMAGE = os.getenv("LANGS_IMAGE", "languages.png")

ASSETS_DIR = os.getenv("ASSETS_DIR", "assets")
BACKGROUND_IMAGE = os.getenv("BACKGROUND_IMAGE", "background.png")
LANGS_BACKGROUND_IMAGE = os.getenv("LANGS_BACKGROUND_IMAGE", BACKGROUND_IMAGE)
BACKGROUND_BLUR = int(os.getenv("BACKGROUND_BLUR", "2"))
BACKGROUND_OVERLAY = int(os.getenv("BACKGROUND_OVERLAY", "150"))

THEME_NAME = os.getenv("THEME", "dark")

EXCLUDE_REPOS = {
    name.strip()
    for name in os.getenv("EXCLUDE_REPOS", "").split(",")
    if name.strip()
}

EXCLUDE_LANGS = {
    name.strip().lower()
    for name in os.getenv("EXCLUDE_LANGS", "").split(",")
    if name.strip()
}

INCLUDE_FORKS = os.getenv("INCLUDE_FORKS", "false").lower() == "true"

TOP_LANGUAGES = int(os.getenv("TOP_LANGUAGES", "6"))

THEMES = {
    "dark": {
        "bg": (13, 17, 23),
        "border": (48, 54, 61),
        "title": (88, 166, 255),
        "text": (201, 209, 217),
        "muted": (139, 148, 158),
        "accent": (63, 185, 80),
        "overlay": (0, 0, 0),
    },
    "light": {
        "bg": (255, 255, 255),
        "border": (208, 215, 222),
        "title": (9, 105, 218),
        "text": (36, 41, 47),
        "muted": (101, 109, 118),
        "accent": (26, 127, 55),
        "overlay": (255, 255, 255),
    },
    "dracula": {
        "bg": (40, 42, 54),
        "border": (68, 71, 90),
        "title": (255, 121, 198),
        "text": (248, 248, 242),
        "muted": (152, 157, 180),
        "accent": (80, 250, 123),
        "overlay": (20, 21, 28),
    },
}

LANGUAGE_COLORS = {
    "python": (53, 114, 165),
    "java": (176, 114, 25),
    "kotlin": (169, 123, 255),
    "javascript": (241, 224, 90),
    "typescript": (49, 120, 198),
    "c": (85, 85, 85),
    "c++": (243, 75, 125),
    "c#": (23, 134, 0),
    "html": (227, 76, 38),
    "css": (86, 61, 124),
    "scss": (198, 83, 140),
    "vue": (65, 184, 131),
    "go": (0, 173, 216),
    "rust": (222, 165, 132),
    "php": (79, 93, 149),
    "ruby": (112, 21, 22),
    "shell": (137, 224, 81),
    "swift": (240, 81, 56),
    "dart": (0, 180, 171),
    "lua": (0, 0, 128),
    "batchfile": (193, 241, 46),
    "dockerfile": (56, 77, 84),
    "makefile": (66, 120, 25),
    "jupyter notebook": (218, 91, 11),
}

DEFAULT_LANGUAGE_COLOR = (130, 140, 150)


def theme() -> dict:
    return THEMES.get(THEME_NAME.lower(), THEMES["dark"])


def language_color(name: str) -> tuple:
    return LANGUAGE_COLORS.get(name.lower(), DEFAULT_LANGUAGE_COLOR)


def background_path(filename: str) -> str:
    if not filename:
        return ""
    if os.path.isabs(filename) or os.path.dirname(filename):
        path = filename
    else:
        path = os.path.join(ASSETS_DIR, filename)
    return path if os.path.exists(path) else ""
