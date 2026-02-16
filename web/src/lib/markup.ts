import { getTextForms, getTypeIndex, getEntry, url } from "./data";

/**
 * Convert game text markup to HTML.
 *
 * - link(TYPE_ID) and link(TYPE_ID,index) → <a> or <span>
 * - icon(), int(), Goods(), {YIELD_*}, {0}, {bullet}, etc. → stripped
 */
export function renderMarkup(text: string): string {
  // 1. link(TYPE_ID) and link(TYPE_ID,index)
  text = text.replace(
    /link\(([A-Z_][A-Z0-9_]+)(?:,(\d+))?\)/g,
    (_match, typeId: string, indexStr?: string) => {
      const index = indexStr ? parseInt(indexStr, 10) : 0;
      const displayText = resolveDisplayText(typeId, index);
      const category = getTypeIndex().get(typeId);
      if (category) {
        return `<a href="${url(`/${category}/${typeId}/`)}" class="text-blue-700 hover:text-blue-900 underline decoration-blue-300">${escapeHtml(displayText)}</a>`;
      }
      return `<span class="font-medium">${escapeHtml(displayText)}</span>`;
    },
  );

  // 2. Strip icon()
  text = text.replace(/icon\([^)]*\)/g, "");

  // 3. Strip int()
  text = text.replace(/int\([^)]*\)/g, "");

  // 4. Strip Goods() but keep inner text
  text = text.replace(/Goods\(([^)]*)\)/g, "$1");

  // 5. Strip {YIELD_*} inline icon placeholders
  text = text.replace(/\{YIELD_[A-Z_]+\}/g, "");

  // 6. Strip other brace patterns ({0}, {bullet}, {lowercase:...}, etc.)
  text = text.replace(/\{[^}]*\}/g, "");

  // 7. Collapse extra whitespace
  text = text.replace(/ {2,}/g, " ").trim();

  // 8. Newlines/tabs to HTML
  text = text.replace(/\n/g, "<br>").replace(/\t/g, "");

  return text;
}

/**
 * Strip all markup to plain text (for <title>, breadcrumbs, etc.).
 */
export function stripMarkup(text: string): string {
  // Resolve link() to just display text
  text = text.replace(
    /link\(([A-Z_][A-Z0-9_]+)(?:,(\d+))?\)/g,
    (_match, typeId: string, indexStr?: string) => {
      const index = indexStr ? parseInt(indexStr, 10) : 0;
      return resolveDisplayText(typeId, index);
    },
  );

  // Strip everything else
  text = text.replace(/icon\([^)]*\)/g, "");
  text = text.replace(/int\([^)]*\)/g, "");
  text = text.replace(/Goods\(([^)]*)\)/g, "$1");
  text = text.replace(/\{[^}]*\}/g, "");
  text = text.replace(/ {2,}/g, " ").trim();

  return text;
}

/**
 * Resolve display text for a type ID at a given form index.
 *
 * Priority: text forms → entry name → humanized ID.
 */
function resolveDisplayText(typeId: string, index: number): string {
  const forms = getTextForms();
  const textKey = `TEXT_${typeId}`;
  const formArray = forms[textKey];
  if (formArray) {
    const safeIndex = index < formArray.length ? index : 0;
    // Strip icon() from form text too (some forms include it)
    return formArray[safeIndex].replace(/icon\([^)]*\)/g, "").trim();
  }

  // Try entry name
  const category = getTypeIndex().get(typeId);
  if (category) {
    const entry = getEntry(category, typeId);
    if (entry && typeof entry.name === "string") {
      return entry.name.replace(/link\([^)]*\)/g, "").replace(/\{[^}]*\}/g, "").trim();
    }
  }

  // Fallback: humanize type ID — TECH_IRONWORKING → "Ironworking"
  return typeId
    .replace(/^[A-Z]+_/, "")
    .replace(/_/g, " ")
    .split(" ")
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase())
    .join(" ");
}

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}
