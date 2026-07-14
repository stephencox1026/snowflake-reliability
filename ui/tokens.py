"""Design tokens — single source of truth for the reliability dashboard."""

from __future__ import annotations

# Accent (one only) — used sparingly for nav/focus
ACCENT = "#2563EB"

# Semantic
SUCCESS = "#15803D"
WARNING = "#B45309"
DANGER = "#B91C1C"

# Neutral scale — neutrals do 90% of the work (no pure black/white surfaces)
NEUTRAL = {
    50: "#F8FAFC",
    100: "#F1F5F9",
    200: "#E2E8F0",
    400: "#64748B",
    700: "#334155",
    900: "#0F172A",
}

SPACE = {1: 4, 2: 8, 3: 12, 4: 16, 5: 24, 6: 32, 7: 48, 8: 64}

FONT_UI = "Inter, system-ui, -apple-system, sans-serif"
FONT_MONO = "'JetBrains Mono', ui-monospace, SFMono-Regular, monospace"

FONT_SIZE = {
    "xs": 12,
    "sm": 13,
    "base": 14,
    "md": 16,
    "lg": 22,
}

RADIUS = 4
SHADOW = "none"

CATEGORY_COLORS: dict[str, str] = {
    "critical": DANGER,
    "Critical": DANGER,
    "high": WARNING,
    "High": WARNING,
    "medium": NEUTRAL[400],
    "Medium": NEUTRAL[400],
    "low": NEUTRAL[200],
    "Low": NEUTRAL[200],
    "HIGH": DANGER,
    "MEDIUM": WARNING,
    "LOW": SUCCESS,
}

NUMERIC_COLUMNS = {
    "Failure probability",
    "Signal value",
    "failure_probability",
    "top_feature_value",
    "precision_score",
    "recall_score",
    "f1_score",
    "roc_auc",
    "duration_minutes",
    "rows_processed",
    "row_count",
    "Precision",
    "Recall",
    "F1",
    "ROC AUC",
    "Duration (min)",
    "Rows processed",
}

CHART_MARGIN = dict(l=0, r=24, t=32, b=0)
CHART_HEIGHT = 220
GRID_OPACITY = 0.08
