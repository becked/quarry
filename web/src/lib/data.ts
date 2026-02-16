import fs from "node:fs";
import path from "node:path";

const OUTPUT_DIR = path.resolve(import.meta.dirname, "../../../output");

// ── Types ────────────────────────────────────────────────────────────

export interface CategoryMeta {
  category: string;
  language: string;
  extractedAt: string;
}

export interface CategoryFile {
  meta: CategoryMeta;
  entries: Record<string, Record<string, unknown>>;
}

export interface CategorySummary {
  name: string;
  displayName: string;
  entryCount: number;
}

// ── Caches (module-scope, populated once per build) ──────────────────

let _allCategories: Map<string, CategoryFile> | null = null;
let _textForms: Record<string, string[]> | null = null;
let _typeIndex: Map<string, string> | null = null;

// ── Loaders ──────────────────────────────────────────────────────────

function loadAllCategories(): Map<string, CategoryFile> {
  if (_allCategories) return _allCategories;
  _allCategories = new Map();
  const files = fs
    .readdirSync(OUTPUT_DIR)
    .filter((f) => f.endsWith(".json") && !f.startsWith("_"));
  for (const file of files) {
    const raw = fs.readFileSync(path.join(OUTPUT_DIR, file), "utf-8");
    const data: CategoryFile = JSON.parse(raw);
    _allCategories.set(data.meta.category, data);
  }
  return _allCategories;
}

export function getTextForms(): Record<string, string[]> {
  if (_textForms) return _textForms;
  const raw = fs.readFileSync(
    path.join(OUTPUT_DIR, "_text-forms.json"),
    "utf-8",
  );
  _textForms = JSON.parse(raw);
  return _textForms!;
}

/** Map every type ID to its category name. */
export function getTypeIndex(): Map<string, string> {
  if (_typeIndex) return _typeIndex;
  _typeIndex = new Map();
  const cats = loadAllCategories();
  for (const [catName, catFile] of cats) {
    for (const typeId of Object.keys(catFile.entries)) {
      _typeIndex.set(typeId, catName);
    }
  }
  return _typeIndex;
}

export function getAllCategories(): CategorySummary[] {
  const cats = loadAllCategories();
  return Array.from(cats.entries())
    .map(([name, file]) => ({
      name,
      displayName: formatDisplayName(name),
      entryCount: Object.keys(file.entries).length,
    }))
    .sort((a, b) => a.displayName.localeCompare(b.displayName));
}

export function getCategory(name: string): CategoryFile | undefined {
  return loadAllCategories().get(name);
}

export function getEntry(
  category: string,
  typeId: string,
): Record<string, unknown> | undefined {
  return loadAllCategories().get(category)?.entries[typeId];
}

// ── URL helpers ──────────────────────────────────────────────────────

const BASE = import.meta.env.BASE_URL.replace(/\/$/, "");

/** Prefix a path with the site base URL. */
export function url(path: string): string {
  return `${BASE}${path}`;
}

// ── Display names ────────────────────────────────────────────────────

const DISPLAY_OVERRIDES: Record<string, string> = {
  difficultyLevels: "Difficulty Levels",
  familyClasses: "Family Classes",
  nationalAmbitions: "National Ambitions",
  religiousImprovements: "Religious Improvements",
  specialImprovements: "Special Improvements",
  traitsAdjectives: "Adjective Traits",
  traitsItems: "Item Traits",
  unitEffects: "Unit Effects",
  victoryTypes: "Victory Types",
};

function formatDisplayName(name: string): string {
  if (DISPLAY_OVERRIDES[name]) return DISPLAY_OVERRIDES[name];
  // camelCase → Title Case
  return name
    .replace(/([A-Z])/g, " $1")
    .replace(/^./, (s) => s.toUpperCase())
    .trim();
}
