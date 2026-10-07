"""Load data/<chapter>/intro.json.

The file looks like {"title": "Chapter One: ...", "pages": ["...", "..."]}.
New Game shows the title card, then the pages. Load Game skips it.
Later chapters add their own data/<chapter>/intro.json; nothing else changes.
"""
import json
import os

import settings


def intro_path(chapter=None):
    """data/<chapter>/intro.json. chapter defaults to settings.CHAPTER."""
    if chapter is None:
        chapter = settings.CHAPTER
    return os.path.join(settings.DATA_ROOT, chapter, "intro.json")


def load_intro(chapter=None):
    """Return (title, pages) for this chapter."""
    with open(intro_path(chapter), encoding="utf-8") as f:
        data = json.load(f)
    return data["title"], list(data["pages"])
