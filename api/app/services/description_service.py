"""Description generation service."""

from pathlib import Path

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.integrations.claude import ClaudeClient
from app.lib.tile_pack import pack_thumbnails
from app.models.asset import Asset
from app.models.description import Description
from app.models.group import GroupAsset
from app.repositories.asset import AssetRepository
from app.repositories.description import DescriptionRepository
from app.repositories.group import GroupRepository


class DescriptionService:
    """Generate descriptions for groups."""

    def __init__(self, session: AsyncSession, anthropic_api_key: str | None = None):
        self.session = session
        self.desc_repo = DescriptionRepository(session)
        self.asset_repo = AssetRepository(session)
        self.group_repo = GroupRepository(session)
        self.claude = ClaudeClient(api_key=anthropic_api_key)

    async def generate(
        self,
        group_id: str,
        custom_prompt: str | None = None,
    ) -> Description:
        """
        Generate a description for a group.

        Steps:
        1. Load group + assets
        2. Verify access (group belongs to user's session)
        3. Build tile-packed preview
        4. Extract location + date from EXIF
        5. Load past captions (style seed)
        6. Call Claude with PROMPT_DESCRIPTION_V1
        7. Save to descriptions table
        8. Unset is_current on prior descriptions for group
        """
        # Load group
        group = await self.group_repo.get_by_id(group_id)
        if not group:
            raise ValueError(f"Group {group_id} not found")

        # Load assets in group via GroupAsset join table
        result = await self.session.execute(
            select(Asset)
            .join(GroupAsset, GroupAsset.asset_id == Asset.id)
            .where(GroupAsset.group_id == group_id)
            .order_by(Asset.taken_at)
        )
        assets = result.scalars().all()
        if not assets:
            raise ValueError(f"No assets in group {group_id}")

        # Build location + date from EXIF
        location = self._extract_location(assets)
        date_str = self._extract_date(assets)

        # Pack thumbnails
        thumbnail_paths = [asset.thumbnail_path for asset in assets if asset.thumbnail_path]
        if not thumbnail_paths:
            raise ValueError("No thumbnails available for packing")

        tile_bytes = pack_thumbnails(thumbnail_paths, cols=3, padding=8)

        # Load past captions for style reference
        past_captions = self._load_style_seed()

        # Call Claude
        prompt = self._build_prompt(
            tile_bytes,
            location,
            date_str,
            len(assets),
            past_captions,
            custom_prompt,
        )

        claude_result = await self.claude.call(
            prompt_name="DESCRIPTION_V1",
            prompt_version="1",
            variables={"prompt_text": prompt},
            model="claude-sonnet-4-6",
        )

        # Extract text from response
        description_text = claude_result.get("text", "").strip()
        tokens_in = claude_result.get("tokens_in")
        tokens_out = claude_result.get("tokens_out")

        # Unset prior is_current
        prior = await self.desc_repo.get_by_group(group_id)
        for p in prior:
            if p.is_current:
                await self.session.execute(
                    update(Description).where(Description.id == p.id).values(is_current=False)
                )

        # Save to DB
        desc = await self.desc_repo.create(
            group_id=group_id,
            text=description_text,
            custom_prompt=custom_prompt,
            model_used="claude-sonnet-4-6",
            tokens_in=tokens_in,
            tokens_out=tokens_out,
        )

        await self.session.commit()
        return desc

    def _extract_location(self, assets: list[Asset]) -> str:
        """Extract location from EXIF data."""
        locations = set()
        for asset in assets:
            if asset.exif_json:
                loc = asset.exif_json.get("location")
                if loc:
                    locations.add(loc)

        if locations:
            return ", ".join(sorted(locations))
        return "Unknown location"

    def _extract_date(self, assets: list[Asset]) -> str:
        """Extract date from EXIF data."""
        if assets and assets[0].taken_at:
            return assets[0].taken_at.strftime("%B %d, %Y")
        return "Unknown date"

    def _load_style_seed(self) -> str:
        """Load past captions from style_seed.txt."""
        seed_path = Path(__file__).parent.parent / "assets" / "style_seed.txt"
        if seed_path.exists():
            try:
                with open(seed_path) as f:
                    return f.read().strip()
            except Exception:
                return ""
        return ""

    def _build_prompt(
        self,
        tile_bytes: bytes,
        location: str,
        date: str,
        n_photos: int,
        past_captions: str,
        custom_prompt: str | None,
    ) -> str:
        """Build the description generation prompt."""
        custom_section = ""
        if custom_prompt:
            custom_section = f'\nCREATOR\'S CUSTOM GUIDANCE FOR THIS POST:\n"{custom_prompt}"\n'

        prompt = f"""You are writing an Instagram caption for a travel carousel. Your goal: sound like the creator, not like AI. Drive engagement without clickbait or emoji overload.

CREATOR'S RECENT CAPTIONS (style reference — match tone, length, voice):
---
{past_captions}
---

CAROUSEL INFO:
- Location: {location}
- Date: {date}
- Number of photos: {n_photos}
- Photos attached as a tile below.
{custom_section}
Rules:
- Match the creator's existing voice (length, emoji usage, tone).
- Include one curious or specific detail about the location that shows the creator was actually there.
- 1-2 relevant hashtags only, never more.
- No generic travel clichés ("wanderlust", "blessed", "views for days").
- Output caption text only. No preamble, no quotes, no commentary."""

        return prompt
