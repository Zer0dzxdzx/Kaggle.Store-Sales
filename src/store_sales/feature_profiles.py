from __future__ import annotations

from dataclasses import dataclass, replace

from store_sales.config import PipelineConfig


@dataclass(frozen=True, slots=True)
class FeatureProfile:
    name: str
    description: str
    sales_lags: tuple[int, ...]
    sales_windows: tuple[int, ...]
    promo_lags: tuple[int, ...]
    promo_windows: tuple[int, ...]
    recent_history_start: str | None = None


FEATURE_PROFILES: dict[str, FeatureProfile] = {
    "compact": FeatureProfile(
        name="compact",
        description="Fast feature set for smoke tests and quick comparisons.",
        sales_lags=(1, 7, 14),
        sales_windows=(7, 14, 28),
        promo_lags=(1, 7),
        promo_windows=(7,),
    ),
    "baseline": FeatureProfile(
        name="baseline",
        description="Main feature set used by the project baseline.",
        sales_lags=(1, 7, 14, 28),
        sales_windows=(7, 14, 28, 56),
        promo_lags=(1, 7, 14),
        promo_windows=(7, 14),
    ),
    "extended": FeatureProfile(
        name="extended",
        description="Adds longer seasonal lags and promotion windows for offline experiments.",
        sales_lags=(1, 7, 14, 28, 56, 364),
        sales_windows=(7, 14, 28, 56, 112),
        promo_lags=(1, 7, 14, 28),
        promo_windows=(7, 14, 28),
    ),
}


def available_feature_profiles() -> tuple[str, ...]:
    return tuple(FEATURE_PROFILES)


def apply_feature_profile(config: PipelineConfig, profile_name: str) -> PipelineConfig:
    if profile_name not in FEATURE_PROFILES:
        available = ", ".join(available_feature_profiles())
        raise ValueError(f"Unknown feature profile: {profile_name}. Available profiles: {available}.")

    profile = FEATURE_PROFILES[profile_name]
    return replace(
        config,
        feature_profile=profile.name,
        sales_lags=profile.sales_lags,
        sales_windows=profile.sales_windows,
        promo_lags=profile.promo_lags,
        promo_windows=profile.promo_windows,
        recent_history_start=profile.recent_history_start,
    )
