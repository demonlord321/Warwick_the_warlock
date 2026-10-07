# Warwick the Warlock — Project Plan

A top-down 2D RPG about Warwick's rise to power. Story driven, with individual
character growth, split into chapters. Python + Pygame, maps as text grids,
turn-based combat, simple graphics.

Each chapter = new area(s) + a new combat ability for Warwick + a closing boss
or turning point. Finish Chapter 1 fully before planning later chapters in detail.

---

## Chapter 1: The Master

**Setting:** the slums, the dark, dreary, poor part of town.

- `slums1`: a maze of narrow alleyways.
- `slums2`: a main road running through, buildings on either side.

**Story beats:** _to be filled in by Dyllan (who is The Master? how does Warwick meet them? how does the chapter end?)_

### Engine milestones (built inside Chapter 1)

**M1: World and movement**
- [x] Window and 60 FPS game loop
- [ ] State manager (overworld / dialogue / battle / menu), Developer
- [x] Text maps parsed and drawn as coloured tiles
- [x] Tile-by-tile movement with wall collision
- [x] Camera that follows the player and clamps at the edges
- [x] Multiple maps loaded by name, doors linking both ways
- [x] Code split into modules with `settings.py`
- [ ] Smooth movement (parked until polish)

**M1.5: Main menu**
- [ ] Title screen state: game title "Warwick the Warlock" over a dark slums-themed background, Developer
- [ ] Menu with New Game, Load Game, Quit; arrow keys/WASD to move, Z/Enter to pick, Developer
- [ ] New Game resets flags, then plays the chapter intro (below), then starts in `slums1`
- [ ] Load Game greyed out until a save exists; loads `save.json` (chapter, map, position, flags)
- [ ] Minimal save to `save.json` from save points (`S` tiles), pulled forward from M5
- [ ] Quit exits cleanly; Esc in-game returns to the menu

**M1.6: Chapter intro screen**
- [ ] Chapter intro state: chapter title card ("Chapter One: The Master"), then a few pages of story text (fade in, Z to advance), then load the first map, Developer
- [ ] Esc skips the intro; Load Game bypasses it
- [ ] Intro text stored as data in `data/chapter1/intro.json` (`title`, `pages`), so it can be rewritten without touching code
- [ ] Intro text drafted by Planner, approved by Dyllan

**M2: Interaction**
- [ ] Dialogue box (typewriter text, Z to advance, blocks movement), Developer
- [ ] `dialogue.json` + loader (`requires` / `sets` / `lines`), Developer
- [ ] Flags dict hooked up to NPCs, plus a debug key, Developer
- [x] Flag-gated doors (`requires_flag`, `locked_key`), Mapmaker
- [x] Chapter 1 maps: `slums1` (alleyways) and `slums2` (main road), Mapmaker. Gate on the east wall of slums1 uses placeholder flag `slums_gate_open` (message `slums_gate_locked`); rename once beats are set
- [x] Base NPCs placed in the slums, Mapmaker (slums1: beggar, urchin, drunk, gate_watcher; slums2: fruit_seller, street_guard, old_woman, thug)
- [ ] Base dialogue for those 8 NPCs (before/after gate states), Planner drafts, Dyllan approves
- [ ] The Master's dialogue chain, waiting on story beats from Dyllan
- [ ] Smoke tests for flags and locks

**M3: Turn-based combat**
- [ ] Stats (HP, MP, attack, defence, speed) and turn order by speed
- [ ] Battle menu: Attack, Defend, Item, Run
- [ ] Damage formula, basic enemy AI, win/lose, XP and levelling
- [ ] Abilities unlocked by flags (e.g. `learned_<ability>`), Warwick's Chapter 1 ability

**M4: Depth**
- [ ] Skills with MP cost, status effects
- [ ] Inventory: healing items and equipment
- [ ] Encounters in the slums

**M5: Chapter 1 complete**
- [ ] Chapter 1 boss / turning point
- [ ] Save and load (flags, position, chapter, inventory) to JSON
- [ ] Sound, transitions, smooth movement, playtest and balance

---

## Later chapters
Outlined once Chapter 1 is done. Maps go in `maps/chapterN/`; the current
chapter is stored in the game state next to `flags`.

## Parked
- The original prototype maps (Willowbrook, house, Mossy Caverns, Warden's
  Chamber) now live in `maps/parked/` for testing or reuse in a later chapter.
