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

**M2: Interaction**
- [ ] Dialogue box (typewriter text, Z to advance, blocks movement), Developer
- [ ] `dialogue.json` + loader (`requires` / `sets` / `lines`), Developer
- [ ] Flags dict hooked up to NPCs, plus a debug key, Developer
- [x] Flag-gated doors (`requires_flag`, `locked_key`), Mapmaker
- [ ] Chapter 1 maps: `slums1` (alleyways) and `slums2` (main road), Mapmaker
- [ ] Chapter 1 dialogue chain for the slums NPCs, Planner drafts, Dyllan approves
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
  Chamber) were placeholders. Keep them for testing or reuse them in a later chapter.
