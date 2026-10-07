"""Load maps/<chapter>/dialogue.json and choose which entry to play.

A key (an NPC's dialogue_key, or a door's locked_key) maps to a list of
entries. Each entry looks like:

    {"requires": ["some_flag"], "sets": ["another_flag"], "lines": ["Hello."]}

requires: flags that must already be true. A missing flag counts as false.
sets: flags to turn on when the conversation finishes (the game does that).
lines: the text, one string per box.

The first entry whose requires are all met is the one that plays. Put the
more specific entries first. An entry with "requires": [] matches anyone,
so an "after" line has to come before the "before" line.
"""
import json
import os

import settings


def dialogue_path(chapter=None):
    """maps/<chapter>/dialogue.json. chapter defaults to settings.CHAPTER."""
    if chapter is None:
        chapter = settings.CHAPTER
    return os.path.join(settings.MAPS_ROOT, chapter, "dialogue.json")


def load_dialogue(chapter=None):
    with open(dialogue_path(chapter), encoding="utf-8") as f:
        return json.load(f)


def pick_entry(entries, flags):
    """Return the first entry whose requires are all true, or None."""
    for entry in entries:
        required = entry.get("requires") or []
        if all(flags.get(name) for name in required):
            return entry
    return None
