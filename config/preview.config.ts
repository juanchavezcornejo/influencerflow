// config/preview.config.ts
// =============================================================================
// InfluencerFlow — Preview Resolution Configuration
// =============================================================================
// Controls how originals are downscaled for UI and AI analysis.
// Aspect ratio is ALWAYS preserved. We only cap the longest side.
// =============================================================================

export type PreviewTier = "thumbnail" | "preview" | "hiPreview" | "original";

export interface PreviewTierConfig {
  /** Maximum length of the longest side in pixels. `null` = no resize. */
  maxLongestSide: number | null;
  /** JPEG quality (1–100). Ignored for original. */
  jpegQuality: number;
  /** Output format. `"keep"` preserves original extension for original. */
  format: "jpeg" | "webp" | "keep";
  /** Primary use case (documentation only). */
  useCase: string;
  /** Relative token cost vs thumbnail (rough estimate). */
  relativeTokenCost: number;
}

export const PREVIEW_CONFIG: Record<PreviewTier, PreviewTierConfig> = {
  thumbnail: {
    maxLongestSide: 384,
    jpegQuality: 80,
    format: "jpeg",
    useCase: "UI grid, list views, quick lookups",
    relativeTokenCost: 1,
  },
  preview: {
    maxLongestSide: 1024,
    jpegQuality: 85,
    format: "jpeg",
    useCase: "AI grouping, labeling, description generation (DEFAULT for AI)",
    relativeTokenCost: 3,
  },
  hiPreview: {
    maxLongestSide: 1536,
    jpegQuality: 88,
    format: "jpeg",
    useCase: "Detailed composition analysis, opt-in only",
    relativeTokenCost: 6,
  },
  original: {
    maxLongestSide: null,
    jpegQuality: 100,
    format: "keep",
    useCase: "Final export only. Never sent to AI.",
    relativeTokenCost: 0,
  },
};

/** Default tier for AI vision calls. Change here to affect the whole app. */
export const DEFAULT_AI_TIER: PreviewTier = "preview";

/** Tile-packing config for Claude Vision (group multiple thumbs into one image). */
export const TILE_PACK_CONFIG = {
  /** Max thumbnails per packed image. */
  maxPerTile: 9,
  /** Grid columns (3x3 for 9, 3x2 for 6). */
  columns: 3,
  /** Padding between tiles in pixels. */
  padding: 8,
  /** Background color for padding. */
  backgroundColor: "#000000",
  /** Use this tier's source for tile packing. */
  sourceTier: "thumbnail" as PreviewTier,
};

/** Rules the processor must follow. */
export const PREVIEW_RULES = {
  preserveAspectRatio: true,
  stripExifOnPreview: false, // keep EXIF on previews (need GPS/date)
  stripExifOnThumbnail: true, // strip EXIF on thumbs (save bytes)
  // When re-generating previews on Resync, skip if file already exists
  // AND its source mtime hasn't changed.
  skipIfUnchanged: true,
};
