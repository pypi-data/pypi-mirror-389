from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple


def normalize_hebrew_text(text: Optional[str]) -> str:
    """Normalize Hebrew punctuation, quotes, hyphens, and collapse whitespace.

    - Map fancy quotes to plain '"'
    - Map various hyphens (en dash, em dash, maqaf) to '-'
    - Remove directional marks, normalize spaces
    - Strip
    """
    if text is None:
        return ""
    s = str(text)
    # Quotes
    s = s.replace("״", '"').replace("׳", "'").replace("”", '"').replace("“", '"').replace("’", "'").replace("‘", "'")
    # Hyphens / dashes / maqaf
    s = s.replace("–", "-").replace("—", "-").replace("‑", "-").replace("־", "-")
    # Directional marks and non-printing
    s = re.sub(r"[\u200E\u200F\u202A-\u202E]", "", s)
    # Normalize multiple spaces
    s = re.sub(r"\s+", " ", s).strip()
    return s


def normalize_number_text(number_text: Optional[str]) -> str:
    """Normalize number_text forms like '((א))', '(א)', 'א', and numeric '3'/'(3)'."""
    if not number_text:
        return ""
    s = normalize_hebrew_text(number_text)
    # Remove outer dup parentheses styles
    s = s.replace("((", "(").replace("))", ")")
    # Remove extraneous dashes in front like '-(1)'
    s = s.lstrip("-")
    return s


def numbers_equal(a: Optional[str], b: Optional[str]) -> bool:
    return normalize_number_text(a) == normalize_number_text(b)


def _iter_components_with_parent(children: List[Dict[str, Any]], parent_list: Optional[List[Dict[str, Any]]] = None):
    if children is None:
        return
    for idx, comp in enumerate(children):
        yield comp, parent_list if parent_list is not None else children, idx
        if comp.get("children"):
            yield from _iter_components_with_parent(comp["children"], comp["children"]) 


def find_component_fuzzy(
    root: Dict[str, Any],
    target_type: Optional[str] = None,
    target_number: Optional[str] = None,
    target_header_contains: Optional[str] = None,
    target_body_contains: Optional[str] = None,
) -> Tuple[Optional[Dict[str, Any]], Optional[List[Dict[str, Any]]], int]:
    """Fuzzy search a component by type/number/header/body with Hebrew normalization.

    Returns (component, parent_children_list, index) or (None, None, -1).
    """
    root_children = root.get("children") if isinstance(root, dict) else None
    if not isinstance(root_children, list):
        return None, None, -1

    norm_header_q = normalize_hebrew_text(target_header_contains) if target_header_contains else None
    norm_body_q = normalize_hebrew_text(target_body_contains) if target_body_contains else None
    norm_num_q = normalize_number_text(target_number) if target_number else None

    for comp, parent_list, idx in _iter_components_with_parent(root_children):
        if target_type and comp.get("type") != target_type:
            continue
        if norm_num_q and not numbers_equal(comp.get("number_text"), norm_num_q):
            continue
        if norm_header_q:
            if not comp.get("header_text"):
                continue
            if norm_header_q not in normalize_hebrew_text(comp["header_text"]):
                continue
        if norm_body_q:
            if not comp.get("body_text"):
                continue
            if norm_body_q not in normalize_hebrew_text(comp["body_text"]):
                continue

        return comp, parent_list, idx

    return None, None, -1


def _section_number_key(number_text: str) -> tuple:
    """Key for sorting section number_text values (supports Hebrew letter suffixes like '7א')."""
    s = normalize_hebrew_text(number_text)
    # extract leading digits
    m = re.match(r"^(\d+)([א-ת]?)$", s)
    if not m:
        return (0, "")
    base = int(m.group(1))
    suf = m.group(2) or ""
    return (base, suf)


def allocate_section_number(existing_numbers: List[str], preferred: Optional[str] = None) -> str:
    """Allocate a unique section number.

    - If preferred is unused, return it.
    - Else, if preferred is numeric like '7', return '7א', '7ב', ... until unused.
    - Else, pick max existing numeric and return next integer.
    """
    normalized = {normalize_hebrew_text(n) for n in existing_numbers if n}

    if preferred:
        pref_norm = normalize_hebrew_text(preferred)
        if pref_norm not in normalized:
            return preferred
        # Try alef-bet suffixes
        m = re.match(r"^(\d+)$", pref_norm)
        if m:
            base = m.group(1)
            for letter in list("אבגדהוזחטיכלמנסעפצקרשת"):
                candidate = f"{base}{letter}"
                if candidate not in normalized:
                    return candidate

    # No preferred or can't use it; choose next numeric
    numeric = [int(m.group(1)) for n in normalized for m in [re.match(r"^(\d+)$", n)] if m]
    next_num = (max(numeric) + 1) if numeric else 1
    return str(next_num)


def collect_section_numbers(root: Dict[str, Any]) -> List[str]:
    """Collect existing section number_text values from the law tree (top-level and nested)."""
    numbers: List[str] = []
    root_children = root.get("children") if isinstance(root, dict) else None
    if not isinstance(root_children, list):
        return numbers
    for comp, _, _ in _iter_components_with_parent(root_children):
        if comp.get("type") == "Section" and comp.get("number_text"):
            numbers.append(str(comp["number_text"]))
    return numbers


