"""Editing service for generating color correction proposals."""

from __future__ import annotations

from pathlib import Path

from PIL import Image
from sqlalchemy.ext.asyncio import AsyncSession

from app.lib.color_ops import apply_corrections
from app.repositories.asset import AssetRepository
from app.repositories.edit_version import EditVersionRepository


class ColorProposal:
    """A color correction proposal."""

    def __init__(
        self,
        preset_name: str,
        adjustments: dict,
        preview_path: str | None = None,
    ):
        self.preset_name = preset_name
        self.adjustments = adjustments
        self.preview_path = preview_path


class EditingService:
    """Service for generating and applying edits."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.asset_repo = AssetRepository(db)
        self.edit_repo = EditVersionRepository(db)

    async def propose_colors_local(self, asset_id: str) -> list[ColorProposal]:
        """Generate 3 local color correction proposals."""
        asset = await self.asset_repo.get_by_id(asset_id)
        if not asset or not asset.preview_path:
            return []

        proposals = []

        try:
            # Load preview image
            preview = Image.open(asset.preview_path).convert("RGB")

            # Proposal 1: Golden Hour Warm
            golden_corrections = {
                "exposure": 0.1,
                "saturation": -0.05,
                "white_balance": {"temp": 20, "tint": 0},
            }
            golden_preview = apply_corrections(preview.copy(), golden_corrections)
            golden_path = self._save_proposal_preview(asset_id, "golden_hour", golden_preview)
            proposals.append(
                ColorProposal(
                    preset_name="Golden Hour Warm",
                    adjustments=golden_corrections,
                    preview_path=golden_path,
                )
            )

            # Proposal 2: Editorial Neutral
            neutral_corrections = {
                "contrast": 0.2,
                "saturation": 0.05,
            }
            neutral_preview = apply_corrections(preview.copy(), neutral_corrections)
            neutral_path = self._save_proposal_preview(
                asset_id, "editorial_neutral", neutral_preview
            )
            proposals.append(
                ColorProposal(
                    preset_name="Editorial Neutral",
                    adjustments=neutral_corrections,
                    preview_path=neutral_path,
                )
            )

            # Proposal 3: Cinematic Moody
            moody_corrections = {
                "exposure": -0.15,
                "contrast": 0.3,
                "saturation": 0.15,
                "white_balance": {"temp": -15, "tint": 0},
            }
            moody_preview = apply_corrections(preview.copy(), moody_corrections)
            moody_path = self._save_proposal_preview(asset_id, "cinematic_moody", moody_preview)
            proposals.append(
                ColorProposal(
                    preset_name="Cinematic Moody",
                    adjustments=moody_corrections,
                    preview_path=moody_path,
                )
            )

        except Exception as e:
            print(f"Error generating color proposals: {e}")
            return []

        return proposals

    def _save_proposal_preview(self, asset_id: str, preset_name: str, image: Image.Image) -> str:
        """Save proposal preview image and return path."""
        proposal_dir = Path("/data/edits") / asset_id / "proposals"
        proposal_dir.mkdir(parents=True, exist_ok=True)

        output_path = proposal_dir / f"{preset_name}.jpg"
        image.save(str(output_path), "JPEG", quality=85)

        return str(output_path)

    async def render_changes_log(self, corrections: dict) -> str:
        """Render corrections as human-readable Spanish text."""
        lines = []

        if "exposure" in corrections:
            exp = corrections["exposure"]
            if exp > 0:
                lines.append(f"- Exposure: +{exp:.1f} (brighter)")
            else:
                lines.append(f"- Exposure: {exp:.1f} (darker)")

        if "contrast" in corrections:
            con = corrections["contrast"]
            if con > 0:
                lines.append(f"- Contrast: +{con:.1f} (increased)")
            else:
                lines.append(f"- Contrast: {con:.1f} (decreased)")

        if "saturation" in corrections:
            sat = corrections["saturation"]
            if sat > 0:
                lines.append(f"- Saturation: +{sat:.1f} (increased)")
            else:
                lines.append(f"- Saturation: {sat:.1f} (decreased)")

        if "white_balance" in corrections:
            wb = corrections["white_balance"]
            temp = wb.get("temp", 0)
            tint = wb.get("tint", 0)
            if temp > 0:
                lines.append(f"- Temperature: +{temp:.0f}K (warmer)")
            elif temp < 0:
                lines.append(f"- Temperature: {temp:.0f}K (cooler)")
            if tint > 0:
                lines.append("- Hue: towards magenta")
            elif tint < 0:
                lines.append("- Hue: towards green")

        if "highlights" in corrections or "shadows" in corrections:
            highlights = corrections.get("highlights", 0)
            shadows = corrections.get("shadows", 0)
            if highlights != 0:
                lines.append(f"- Highlights: {highlights:.1f}")
            if shadows != 0:
                lines.append(f"- Shadows: {shadows:.1f}")

        return "\n".join(lines) if lines else "No changes"
