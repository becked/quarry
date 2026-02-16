# Web Data Requirements

Two issues in quarry's output need to be addressed before the web layer can fully render game text.

## 1. Recursive Text Resolution

**Problem:** The text resolver performs single-level resolution. When a resolved string itself contains `{TEXT_*}` references, those are passed through verbatim.

**Example:** Resolving `TEXT_GUIDE_TECH_STONECUTTING_BONUS_STONE` produces:

```
This card will give you a one-off bonus of +200 link(YIELD_STONE,1) when
researched, a useful boost for building link(IMPROVEMENT_FORT,2),
link(CONCEPT_WONDER,2), or other large projects. {TEXT_GUIDE_TECH_BONUS_DISCARD}
```

`{TEXT_GUIDE_TECH_BONUS_DISCARD}` should resolve to: "If a bonus card is not researched when it appears, it is permanently trashed once discarded and will not appear again."

**Scope:** ~65 instances across the output. Almost all are `{TEXT_GUIDE_TECH_BONUS_DISCARD}` in `technologies.json`, plus a handful in `yields.json`, `concepts.json`, and `tutorials.json`.

**Fix:** After resolving a text key, scan the result for `{TEXT_*}` patterns and resolve them recursively. Cap recursion depth to guard against cycles.

## 2. Text Forms Index

**Problem:** The `link(ID, index)` markup in game text uses a numeric index to select a grammatical form. Text entries store multiple forms separated by `~`:

```xml
<!-- text-nation.xml -->
<zType>TEXT_NATION_ROME</zType>
<en-US>Rome~Roman~a Roman~Romans</en-US>
```

So `link(NATION_ROME,1)` should display "Roman" and `link(NATION_ROME,3)` should display "Romans". The web layer needs this form data to render links with the correct display text.

The game's C# parser is in `Reference/Source/Base/Game/GameCore/Text/TextEntry.cs` (lines 200-213) — it splits on `~` and selects by index, defaulting to index 0 if out of range.

**Fix:** Quarry should produce a supplementary output file (e.g., `_text-forms.json`) mapping text keys to their array of forms:

```json
{
  "TEXT_NATION_ROME": ["Rome", "Roman", "a Roman", "Romans"],
  "TEXT_MISSION_TRADE_MISSION": ["Trade Mission", "a Trade Mission", "Trade Missions"],
  ...
}
```

This keeps all XML parsing in quarry and gives the web layer a clean data contract for resolving `link()` display text. The `_` prefix distinguishes it from category output files.
