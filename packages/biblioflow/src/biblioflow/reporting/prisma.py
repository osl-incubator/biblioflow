"""
title: Lightweight PRISMA-inspired diagram support for biblioflow reports.
"""

from __future__ import annotations

from html import escape
from pathlib import Path
from typing import Any

from biblioflow.reporting.models import PrismaFlow, ReportWarning


def validate_prisma(flow: PrismaFlow | None) -> list[ReportWarning]:
    """
    title: Validate PRISMA counts and return structured warnings.
    parameters:
      flow:
        type: PrismaFlow | None
    returns:
      type: list[ReportWarning]
    """
    if flow is None:
        return [
            ReportWarning(
                code="prisma_missing",
                message=(
                    "No PRISMA counts were provided; the report will include "
                    "a placeholder flow."
                ),
            )
        ]
    warnings: list[ReportWarning] = []
    identified = flow.identified
    duplicates = flow.duplicates_removed or 0
    screened = flow.screened
    excluded = flow.excluded_screening or 0
    full_text = flow.full_text_assessed
    full_text_excluded = flow.full_text_excluded
    included = flow.included

    if identified is not None and screened is not None:
        expected_screened = max(identified + (flow.other_sources or 0) - duplicates, 0)
        if screened != expected_screened:
            warnings.append(
                ReportWarning(
                    code="prisma_screened_mismatch",
                    message=(
                        "PRISMA screened count does not equal identified plus "
                        "other sources minus duplicates removed."
                    ),
                    details={"expected": expected_screened, "actual": screened},
                )
            )
    if screened is not None and full_text is not None:
        expected_full_text = max(screened - excluded, 0)
        if full_text != expected_full_text:
            warnings.append(
                ReportWarning(
                    code="prisma_full_text_mismatch",
                    message=(
                        "PRISMA full-text assessed count does not equal "
                        "screened minus screening exclusions."
                    ),
                    details={"expected": expected_full_text, "actual": full_text},
                )
            )
    if full_text is not None and included is not None:
        excluded_total = full_text_excluded
        if excluded_total is None and flow.full_text_exclusion_reasons:
            excluded_total = sum(flow.full_text_exclusion_reasons.values())
        if excluded_total is not None:
            expected_included = max(full_text - excluded_total, 0)
            if included != expected_included:
                warnings.append(
                    ReportWarning(
                        code="prisma_included_mismatch",
                        message=(
                            "PRISMA included count does not equal full-text "
                            "assessed minus full-text exclusions."
                        ),
                        details={"expected": expected_included, "actual": included},
                    )
                )
    if (
        full_text_excluded is not None
        and flow.full_text_exclusion_reasons
        and full_text_excluded != sum(flow.full_text_exclusion_reasons.values())
    ):
        warnings.append(
            ReportWarning(
                code="prisma_exclusion_reason_mismatch",
                message=(
                    "Full-text exclusion reasons do not sum to the full-text "
                    "excluded count."
                ),
                details={
                    "expected": full_text_excluded,
                    "actual": sum(flow.full_text_exclusion_reasons.values()),
                },
            )
        )
    return warnings


def default_prisma(records: int) -> PrismaFlow:
    """
    title: Return a conservative PRISMA flow when only corpus size is known.
    parameters:
      records:
        type: int
    returns:
      type: PrismaFlow
    """
    return PrismaFlow(
        identified=records,
        duplicates_removed=0,
        screened=records,
        excluded_screening=0,
        full_text_assessed=records,
        full_text_excluded=0,
        included=records,
    )


def prisma_rows(flow: PrismaFlow | None) -> list[dict[str, Any]]:
    """
    title: Return table rows for PRISMA counts.
    parameters:
      flow:
        type: PrismaFlow | None
    returns:
      type: list[dict[str, Any]]
    """
    if flow is None:
        return []
    rows = [
        ("Records identified", flow.identified),
        ("Additional records from other sources", flow.other_sources),
        ("Duplicates removed", flow.duplicates_removed),
        ("Records screened", flow.screened),
        ("Records excluded during screening", flow.excluded_screening),
        ("Full-text reports assessed", flow.full_text_assessed),
        ("Full-text reports excluded", flow.full_text_excluded),
        ("Studies/reports included", flow.included),
    ]
    result = [
        {"stage": label, "count": count} for label, count in rows if count is not None
    ]
    for reason, count in flow.full_text_exclusion_reasons.items():
        result.append({"stage": f"Full-text exclusion: {reason}", "count": count})
    return result


def write_prisma_svg(
    flow: PrismaFlow | None,
    path: str | Path,
    *,
    title: str = "PRISMA flow",
) -> Path:
    """
    title: Write a professional lightweight PRISMA-inspired SVG diagram.
    parameters:
      flow:
        type: PrismaFlow | None
      path:
        type: str | Path
      title:
        type: str
    returns:
      type: Path
    """
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(render_prisma_svg(flow, title=title), encoding="utf-8")
    return target


def render_prisma_svg(flow: PrismaFlow | None, *, title: str = "PRISMA flow") -> str:
    """
    title: Render a PRISMA-inspired flow diagram as SVG.
    parameters:
      flow:
        type: PrismaFlow | None
      title:
        type: str
    returns:
      type: str
    """
    if flow is None:
        flow = PrismaFlow()
    main_boxes = [
        _box_text("Identification", "Records identified", flow.identified),
        _box_text("Deduplication", "Duplicates removed", flow.duplicates_removed),
        _box_text("Screening", "Records screened", flow.screened),
        _box_text("Eligibility", "Full-text assessed", flow.full_text_assessed),
        _box_text("Included", "Studies/reports included", flow.included),
    ]
    side_boxes = [
        _box_text("Other sources", "Additional records", flow.other_sources),
        _box_text("Excluded", "Screening exclusions", flow.excluded_screening),
        _box_text("Excluded", "Full-text exclusions", flow.full_text_excluded),
    ]
    reason_lines = [
        f"{reason}: {count}"
        for reason, count in flow.full_text_exclusion_reasons.items()
    ]
    width = 920
    height = 780 if reason_lines else 690
    svg: list[str] = [
        (
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" '
            f'height="{height}" viewBox="0 0 {width} {height}" role="img" '
            f'aria-label="{escape(title)}">'
        ),
        "<defs>",
        (
            '<filter id="shadow" x="-20%" y="-20%" width="140%" '
            'height="140%"><feDropShadow dx="0" dy="6" stdDeviation="8" '
            'flood-color="#1F2937" flood-opacity="0.18"/></filter>'
        ),
        "</defs>",
        '<rect width="100%" height="100%" fill="#FFFFFF"/>',
        (
            '<text x="460" y="46" text-anchor="middle" '
            'font-family="Inter, Arial, sans-serif" font-size="28" '
            f'font-weight="700" fill="#1F2937">{escape(title)}</text>'
        ),
        (
            '<text x="460" y="76" text-anchor="middle" '
            'font-family="Inter, Arial, sans-serif" font-size="13" '
            'fill="#6B7280">PRISMA-inspired project evidence flow</text>'
        ),
    ]
    x = 270
    y_positions = [115, 225, 335, 445, 555]
    for index, text in enumerate(main_boxes):
        svg.extend(_svg_box(x, y_positions[index], 380, 78, text, accent=index == 4))
        if index < len(y_positions) - 1:
            svg.append(
                _arrow(460, y_positions[index] + 78, 460, y_positions[index + 1])
            )
    if flow.other_sources is not None:
        svg.extend(_svg_box(45, 115, 185, 78, side_boxes[0], muted=True))
        svg.append(_arrow(230, 154, 270, 154))
    if flow.excluded_screening is not None:
        svg.extend(_svg_box(690, 335, 185, 78, side_boxes[1], muted=True))
        svg.append(_arrow(650, 374, 690, 374))
    if flow.full_text_excluded is not None:
        svg.extend(_svg_box(690, 445, 185, 78, side_boxes[2], muted=True))
        svg.append(_arrow(650, 484, 690, 484))
    if reason_lines:
        svg.extend(
            _svg_box(
                215,
                655,
                490,
                72 + (len(reason_lines) * 18),
                ["Full-text exclusion reasons", *reason_lines],
                muted=True,
            )
        )
        svg.append(_arrow(460, 633, 460, 655))
    svg.append("</svg>")
    return "\n".join(svg) + "\n"


def _box_text(stage: str, label: str, value: int | None) -> list[str]:
    """
    title: Build display lines for one PRISMA box.
    parameters:
      stage:
        type: str
      label:
        type: str
      value:
        type: int | None
    returns:
      type: list[str]
    """
    count = "Not provided" if value is None else f"n = {value:,}"
    return [stage, label, count]


def _svg_box(
    x: int,
    y: int,
    width: int,
    height: int,
    lines: list[str],
    *,
    accent: bool = False,
    muted: bool = False,
) -> list[str]:
    """
    title: Render one diagram box as SVG elements.
    parameters:
      x:
        type: int
      y:
        type: int
      width:
        type: int
      height:
        type: int
      lines:
        type: list[str]
      accent:
        type: bool
      muted:
        type: bool
    returns:
      type: list[str]
    """
    fill = "#E6FFFB" if accent else ("#F3F6FA" if muted else "#FFFFFF")
    stroke = "#00A6A6" if accent else ("#CBD5E1" if muted else "#1F4E79")
    text_color = "#1F2937"
    output = [
        (
            f'<rect x="{x}" y="{y}" width="{width}" height="{height}" '
            f'rx="14" fill="{fill}" stroke="{stroke}" stroke-width="2" '
            'filter="url(#shadow)"/>'
        )
    ]
    for index, line in enumerate(lines):
        size = 15 if index == 0 else 13
        weight = "700" if index == 0 else "500"
        fill_color = "#1F4E79" if index == 0 else text_color
        output.append(
            f'<text x="{x + width / 2:.1f}" '
            f'y="{y + 24 + index * 19}" text-anchor="middle" '
            'font-family="Inter, Arial, sans-serif" '
            f'font-size="{size}" font-weight="{weight}" '
            f'fill="{fill_color}">{escape(line)}</text>'
        )
    return output


def _arrow(x1: int, y1: int, x2: int, y2: int) -> str:
    """
    title: Render an SVG arrow path between two points.
    parameters:
      x1:
        type: int
      y1:
        type: int
      x2:
        type: int
      y2:
        type: int
    returns:
      type: str
    """
    if x1 == x2:
        head = f"M {x2 - 5} {y2 - 7} L {x2} {y2} L {x2 + 5} {y2 - 7}"
    else:
        head = f"M {x2 - 7} {y2 - 5} L {x2} {y2} L {x2 - 7} {y2 + 5}"
    return (
        f'<path d="M {x1} {y1} L {x2} {y2} {head}" fill="none" '
        'stroke="#1F4E79" stroke-width="2.5" stroke-linecap="round" '
        'stroke-linejoin="round"/>'
    )
