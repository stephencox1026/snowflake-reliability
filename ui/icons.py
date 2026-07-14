"""Lucide icon SVGs — single icon set, inline only."""

from __future__ import annotations

import html

# Lucide paths (ISC license) — 16px, stroke-based
_ICONS: dict[str, str] = {
    "activity": '<path d="M22 12h-4l-3 9L9 3l-3 9H2"/>',
    "alert-triangle": '<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3"/><path d="M12 9v4"/><path d="M12 17h.01"/>',
    "check-circle": '<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><path d="m9 11 3 3L22 4"/>',
    "info": '<circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/>',
}


def lucide(name: str, *, size: int = 16, color: str = "currentColor") -> str:
    path = _ICONS.get(name)
    if not path:
        return ""
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
        f'viewBox="0 0 24 24" fill="none" stroke="{html.escape(color)}" '
        f'stroke-width="2" stroke-linecap="round" stroke-linejoin="round" '
        f'aria-hidden="true" style="vertical-align:-2px;margin-right:6px;">{path}</svg>'
    )
