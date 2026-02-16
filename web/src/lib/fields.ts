/** Fields that are game engine internals, not useful for a wiki reader. */
const HIDDEN_FIELDS = new Set([
  "iconName",
  "portraitName",
  "backgroundName",
  "assetVariation",
  "assetConstruction",
  "audioSelectionType",
  "audioMovementType",
  "audioAttackType",
  "audioDamagedByProjectileType",
  "audioAmbienceTileLoopComponent",
  "audioSwitchName",
  "audioLoopWhenBuilding",
  "formations",
  "workerAnimation",
  "animNormalMoveDuration",
  "animNormalMoveSpeed",
  "animIntermediateMoveDuration",
  "animIntermediateMoveSpeed",
  "animFastMoveDuration",
  "animFastMoveSpeed",
  "attackDuration",
  "barbarianPortraitName",
  "characterPortraitBackground",
  "characterSelectPortrait",
  "characterPortraits",
  "genderPortraitName",
  "preferredPortrait",
  "crest",
  "teamColor",
  "capitalAsset",
  "cityAsset",
  "urbanAsset",
  "color",
  "mapElementNames",
  "projectAsset",
  "cityWidget",
  "resourceAssetVariation",
  "terrainAssetVariation",
  "heightAsset",
  "mountainSplineAsset",
  "fadeWithPing",
  "fadeWithUnits",
  "liftOnHills",
  "pingOffset",
  "attackPortraitName",
  "portraitBackground",
]);

/** Fields with text markup that should be rendered as rich HTML. */
const TEXT_FIELDS = new Set([
  "name",
  "advice",
  "help",
  "history",
  "description",
  "story",
  "adviceFound",
  "nameRemove",
  "nameCharacter",
  "nameTarget",
  "helpText",
]);

/** Priority for field ordering (lower = earlier). */
const FIELD_ORDER: Record<string, number> = {
  name: 0,
  advice: 1,
  help: 2,
  description: 3,
  history: 4,
  story: 5,
  cost: 10,
  production: 11,
  strength: 12,
  movement: 13,
  hPMax: 14,
};

export type FieldType =
  | "text"
  | "string"
  | "typeId"
  | "number"
  | "boolean"
  | "list"
  | "map"
  | "nestedMap";

export interface FieldInfo {
  key: string;
  displayName: string;
  type: FieldType;
  value: unknown;
}

export function isHidden(key: string): boolean {
  return HIDDEN_FIELDS.has(key);
}

export function classifyField(key: string, value: unknown): FieldType {
  if (TEXT_FIELDS.has(key) && typeof value === "string") return "text";
  if (typeof value === "string") {
    if (/^[A-Z][A-Z0-9]+_[A-Z0-9_]+$/.test(value)) return "typeId";
    return "string";
  }
  if (typeof value === "number") return "number";
  if (typeof value === "boolean") return "boolean";
  if (Array.isArray(value)) return "list";
  if (typeof value === "object" && value !== null) {
    const vals = Object.values(value);
    if (vals.some((v) => typeof v === "object" && v !== null)) return "nestedMap";
    return "map";
  }
  return "string";
}

const DISPLAY_NAME_OVERRIDES: Record<string, string> = {
  hPMax: "Max HP",
};

/** Convert camelCase field key to human-readable label. */
export function fieldDisplayName(key: string): string {
  if (DISPLAY_NAME_OVERRIDES[key]) return DISPLAY_NAME_OVERRIDES[key];
  return key
    .replace(/([A-Z])/g, " $1")
    .replace(/^./, (s) => s.toUpperCase())
    .trim();
}

/** Sort and filter entry fields for display. */
export function prepareFields(entry: Record<string, unknown>): FieldInfo[] {
  return Object.entries(entry)
    .filter(([key]) => !isHidden(key))
    .map(([key, value]) => ({
      key,
      displayName: fieldDisplayName(key),
      type: classifyField(key, value),
      value,
    }))
    .sort((a, b) => {
      const oa = FIELD_ORDER[a.key] ?? 100;
      const ob = FIELD_ORDER[b.key] ?? 100;
      if (oa !== ob) return oa - ob;
      return a.key.localeCompare(b.key);
    });
}
