# docs/PROMPTS.md — Claude Prompt Library

> Centralized collection of prompts used by InfluencerFlow.
> Each prompt has: purpose, model, inputs, expected output, token budget, and template.

---

## Table of Contents
1. [Grouping Refinement](#1-grouping-refinement)
2. [Color Correction Suggestion](#2-color-correction-suggestion)
3. [Composition/Crop Suggestion](#3-compositioncrop-suggestion)
4. [Object Removal Mask Suggestion](#4-object-removal-mask-suggestion)
5. [Description Generation](#5-description-generation)
6. [Best Photo Selection (within near-duplicates)](#6-best-photo-selection)

---

## 1. Grouping Refinement

**Purpose:** After deterministic grouping (date + GPS), ask Claude to refine groupings based on visual similarity and narrative cohesion.

**Model:** `claude-haiku-4-5` (cheaper; grouping doesn't need the smartest model).
**Input:** Tile-packed thumbnail images (up to 9 per tile), minimal EXIF context.
**Output:** JSON with suggested regroupings.
**Token budget:** ~500 input + 300 output per tile.

### Template

```text
You are helping an Instagram content creator group travel photos into cohesive carousel posts.

I'll show you a tile containing {N} numbered thumbnails from the same day. They were shot at these approximate locations and times:

{asset_metadata_list}

Your task: suggest how to group them into Instagram carousels (1–10 photos per carousel). A good carousel tells one mini-story or captures one location/moment.

Output strict JSON only, no prose:
{
  "groups": [
    {
      "carousel_name": "short descriptive name",
      "asset_indices": [1, 3, 5],
      "reasoning": "one short sentence"
    }
  ]
}
```

---

## 2. Color Correction Suggestion

**Purpose:** Suggest a color correction style for a single photo that would make it more Instagram-ready.

**Model:** `claude-haiku-4-5`.
**Input:** Single preview (1024px), EXIF (camera, time, lighting if available).
**Output:** JSON with 3 style proposals + per-channel params.
**Token budget:** ~1200 input + 500 output.

### Template

```text
You are a photo colorist specializing in travel photography for Instagram.

Analyze this photo and propose 3 color correction styles that would each work for a different mood. For each, provide concrete adjustment values that can be applied programmatically with Pillow or a LUT.

Consider: time of day, existing color temperature, dominant colors, subject matter.

Output strict JSON:
{
  "proposals": [
    {
      "name": "e.g. Golden Hour Warm",
      "mood": "one word",
      "adjustments": {
        "temperature_kelvin_delta": 0,
        "tint_delta": 0,
        "exposure_stops": 0.0,
        "contrast_delta": 0,
        "highlights_delta": 0,
        "shadows_delta": 0,
        "whites_delta": 0,
        "blacks_delta": 0,
        "saturation_delta": 0,
        "vibrance_delta": 0
      },
      "changes_log_bullet": "human-readable description for the changes log"
    }
  ]
}
```

---

## 3. Composition / Crop Suggestion

**Purpose:** Suggest a crop that improves composition.

**Model:** `claude-sonnet-4-6` (needs better spatial reasoning).
**Input:** Single preview (1024px).
**Output:** JSON with normalized crop box + reasoning.
**Token budget:** ~1200 input + 300 output.

### Template

```text
You are a composition expert. Propose a crop for this photo that follows the rule of thirds or a strong alternative composition (centered, symmetry, leading lines).

The photo's dimensions are {width}x{height}. Propose the crop as normalized coordinates (0.0–1.0) for x, y, width, height of the crop rectangle within the original.

Also specify target aspect ratio from: 1:1, 4:5, 9:16. Pick what best fits Instagram.

Output strict JSON:
{
  "crop": { "x": 0.0, "y": 0.0, "width": 1.0, "height": 1.0 },
  "aspect_ratio": "4:5",
  "composition_technique": "rule_of_thirds | symmetry | leading_lines | centered",
  "reasoning": "one sentence",
  "changes_log_bullet": "human-readable description"
}
```

---

## 4. Object Removal Mask Suggestion

**Purpose:** Identify distracting elements (people in background, trash, signs) that could be removed with inpainting.

**Model:** `claude-sonnet-4-6`.
**Input:** Single preview.
**Output:** JSON with bounding boxes for candidates + confidence.
**Token budget:** ~1200 input + 400 output.

### Template

```text
You are helping clean up a travel photo for Instagram. Identify up to 5 distracting elements that could be cleanly removed (strangers in background, trash, distracting signs, photobombs, lens flare artifacts).

DO NOT suggest removing the main subject or essential elements of the scene.

For each, provide a normalized bounding box (0.0–1.0) and a brief justification.

Output strict JSON:
{
  "candidates": [
    {
      "label": "stranger walking in background",
      "bbox": { "x": 0.0, "y": 0.0, "width": 0.0, "height": 0.0 },
      "confidence": 0.0,
      "recommend_remove": true
    }
  ]
}
```

The backend will pass selected bboxes to LaMa on Replicate for actual removal.

---

## 5. Description Generation

**Purpose:** Generate engagement-focused Instagram caption that sounds like Juan, not like AI.

**Model:** `claude-sonnet-4-6`.
**Input:** Tile-packed previews of final carousel + EXIF (location, date) + user's custom prompt + up to 5 previous captions as style reference.
**Output:** Plain-text caption.
**Token budget:** ~2000 input + 400 output.

### Template

```text
You are writing an Instagram caption for a travel carousel. Your goal: sound like the creator, not like AI. Drive engagement without clickbait or emoji overload.

CREATOR'S RECENT CAPTIONS (style reference — match tone, length, voice):
---
{past_captions}
---

CARROUSEL INFO:
- Location: {location}
- Date: {date}
- Number of photos: {n_photos}
- Photos attached as a tile below.

CREATOR'S CUSTOM GUIDANCE FOR THIS POST:
"{user_custom_prompt}"

Rules:
- Match the creator's existing voice (length, emoji usage, tone).
- Include one curious or specific detail about the location that shows the creator was actually there.
- 1–2 relevant hashtags only, never more.
- No generic travel clichés ("wanderlust", "blessed", "views for days").
- Output caption text only. No preamble, no quotes, no commentary.
```

---

## 6. Best Photo Selection

**Purpose:** When pHash detects near-duplicates, choose the strongest one.

**Model:** `claude-haiku-4-5`.
**Input:** Tile with the duplicates.
**Output:** Index of the winner + reason.
**Token budget:** ~800 input + 150 output.

### Template

```text
These {N} thumbnails are near-duplicates of the same moment. Pick the ONE that is strongest for Instagram based on: sharpness, subject expression (if people), composition, exposure.

Output strict JSON:
{
  "winner_index": 1,
  "reason": "short sentence"
}
```

---

## Cost Guardrails (applied across all prompts)

1. **Cache by input hash.** Same image + same prompt version = return cached response.
2. **Prompt versioning.** Every prompt has a version number; cache invalidates on change.
3. **Haiku for structured extraction**, Sonnet for creative/spatial reasoning.
4. **Tile-pack for batch vision tasks** (grouping, duplicate selection).
5. **User confirmation required** before any call (with token + $ estimate shown).
6. **Log every call** to `cost_log` table with: prompt_name, version, tokens_in, tokens_out, cost_usd.

---

## Prompt Versioning Convention

Each prompt lives in code as:
```python
PROMPT_GROUPING_V1 = """..."""
PROMPT_COLOR_V1 = """..."""
```

When editing, increment version and keep the old one commented out for reference until the next release.
