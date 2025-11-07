"""Reusable building blocks for constructing Lark interactive cards.

This module exposes small, composable helpers that return block dictionaries
compatible with Lark's interactive card schema. Templates can compose these
blocks to build complete cards in a predictable, extensible way.

All functions return plain dicts; callers may further compose or wrap them.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional


Block = Dict[str, Any]


def markdown(
    content: str,
    *,
    text_align: str = "left",
    text_size: str = "normal",
    margin: str = "0px 0px 0px 0px",
) -> Block:
    """Create a markdown block.

    Args:
        content: Markdown content string
        text_align: Text alignment
        text_size: Text size key (e.g., "normal", "normal_v2")
        margin: CSS-like margin string
    """
    return {
        "tag": "markdown",
        "content": content,
        "text_align": text_align,
        "text_size": text_size,
        "margin": margin,
    }


def text_tag(text: str, color: str) -> Block:
    """Create a text tag descriptor for card headers."""
    return {
        "tag": "text_tag",
        "text": {"tag": "plain_text", "content": text},
        "color": color,
    }


def header(
    *,
    title: str,
    template: str,
    subtitle: Optional[str] = None,
    text_tag_list: Optional[List[Block]] = None,
    padding: Optional[str] = None,
) -> Block:
    """Create a card header block.

    Only includes optional fields if provided to preserve exact output for
    existing templates.
    """
    h: Block = {
        "title": {"tag": "plain_text", "content": title},
        "template": template,
    }
    if subtitle is not None:
        h["subtitle"] = {"tag": "plain_text", "content": subtitle}
    if text_tag_list:
        h["text_tag_list"] = text_tag_list
    if padding is not None:
        h["padding"] = padding
    return h


def body(elements: Iterable[Block], *, direction: str = "vertical") -> Block:
    """Create a card body wrapper."""
    return {
        "direction": direction,
        "elements": list(elements),
    }


def config_textsize_normal_v2() -> Block:
    """Create the config block used by some templates for responsive text sizing."""
    return {
        "update_multi": True,
        "style": {
            "text_size": {
                "normal_v2": {
                    "default": "normal",
                    "pc": "normal",
                    "mobile": "heading",
                }
            }
        },
    }


def column(
    elements: Iterable[Block],
    *,
    width: str = "auto",
    vertical_spacing: str = "8px",
    horizontal_align: str = "left",
    vertical_align: str = "top",
    weight: Optional[int] = None,
) -> Block:
    """Create a column block."""
    col: Block = {
        "tag": "column",
        "width": width,
        "elements": list(elements),
        "vertical_spacing": vertical_spacing,
        "horizontal_align": horizontal_align,
        "vertical_align": vertical_align,
    }
    if weight is not None:
        col["weight"] = weight
    return col


def column_set(
    columns: Iterable[Block],
    *,
    background_style: str = "grey-100",
    horizontal_spacing: str = "12px",
    horizontal_align: str = "left",
    margin: str = "0px 0px 0px 0px",
) -> Block:
    """Create a column_set wrapper with common defaults."""
    return {
        "tag": "column_set",
        "background_style": background_style,
        "horizontal_spacing": horizontal_spacing,
        "horizontal_align": horizontal_align,
        "columns": list(columns),
        "margin": margin,
    }


def collapsible_panel(
    title_markdown_content: str,
    elements: Iterable[Block],
    *,
    expanded: bool = False,
    background_color: str = "grey-200",
    border_color: str = "grey",
    corner_radius: str = "5px",
    vertical_spacing: str = "8px",
    padding: str = "8px 8px 8px 8px",
) -> Block:
    """Create a collapsible panel block with a markdown title and standard icon."""
    return {
        "tag": "collapsible_panel",
        "expanded": expanded,
        "header": {
            "title": {
                "tag": "markdown",
                "content": title_markdown_content,
            },
            "background_color": background_color,
            "vertical_align": "center",
            "icon": {
                "tag": "standard_icon",
                "token": "down-small-ccm_outlined",
                "color": "",
                "size": "16px 16px",
            },
            "icon_position": "right",
            "icon_expanded_angle": -180,
        },
        "border": {"color": border_color, "corner_radius": corner_radius},
        "vertical_spacing": vertical_spacing,
        "padding": padding,
        "elements": list(elements),
    }


def card(
    *,
    elements: Iterable[Block],
    header: Block,
    schema: str = "2.0",
    config: Optional[Block] = None,
) -> Block:
    """Assemble a full card from header + body (+ optional config)."""
    card_obj: Block = {
        "schema": schema,
        "body": body(elements),
        "header": header,
    }
    if config is not None:
        card_obj["config"] = config
    return card_obj


def template_reference(
    *,
    template_id: str,
    template_version_name: str,
    template_variable: Dict[str, Any],
) -> Block:
    """Create a reference to a published Lark template by ID/version."""
    return {
        "type": "template",
        "data": {
            "template_id": template_id,
            "template_version_name": template_version_name,
            "template_variable": template_variable,
        },
    }
