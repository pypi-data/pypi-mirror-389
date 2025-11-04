"""
Public API for ShadeSorter color family classification.
Provides functions for each color space and a combined function.
"""

import colorsys
import math
from shade_sorter.classifier import classify

try:
    from tintelligence_color_utils import (
        hex_to_hsv,
        hex_to_rgb,
        lab_to_lch,
        rgb01_to_hsl,
        rgb_to_lab,
        xyz_to_lab,
        rgb_to_xyz,
    )
except ImportError:
    raise ImportError(
        "tintelligence-color-utils is required. Install with: pip install tintelligence-color-utils"
    )


def _hsl_to_rgb(h: float, s: float, l: float) -> tuple[float, float, float]:
    """Convert HSL (h in 0-360 degrees, s/l in 0-1) to RGB (0-1)."""
    # colorsys uses HLS (hue, lightness, saturation), so swap s and l
    h_01 = (h % 360) / 360.0 if h is not None else 0.0
    return colorsys.hls_to_rgb(h_01, l, s)


def _hsv_to_rgb(h: float, s: float, v: float) -> tuple[float, float, float]:
    """Convert HSV (h in 0-360 degrees, s/v in 0-1) to RGB (0-1)."""
    h_01 = (h % 360) / 360.0 if h is not None else 0.0
    return colorsys.hsv_to_rgb(h_01, s, v)


def _rgb_to_hsv(r: float, g: float, b: float) -> tuple[float, float, float]:
    """Convert RGB (0-1) to HSV (h in 0-360 degrees, s/v in 0-1)."""
    h_01, s, v = colorsys.rgb_to_hsv(r, g, b)
    h = h_01 * 360.0 if h_01 is not None else None
    return h, s, v


def _lab_to_xyz(L: float, a: float, b: float) -> tuple[float, float, float]:
    """Convert Lab to XYZ (reverse of xyz_to_lab)."""
    ref_x, ref_y, ref_z = 95.047, 100.000, 108.883
    
    fy = (L + 16) / 116.0
    fx = a / 500.0 + fy
    fz = fy - b / 200.0
    
    def inv_pivot(c):
        c3 = c * c * c
        if c3 > 0.008856:
            return c3
        return (c - 16 / 116) / 7.787
    
    x = inv_pivot(fx) * ref_x
    y = inv_pivot(fy) * ref_y
    z = inv_pivot(fz) * ref_z
    return x, y, z


def _xyz_to_rgb(x: float, y: float, z: float) -> tuple[float, float, float]:
    """Convert XYZ to normalized RGB (0-1) (reverse of rgb_to_xyz)."""
    # sRGB D65 matrix (inverse)
    x, y, z = x / 100.0, y / 100.0, z / 100.0
    r = x * 3.2406 + y * -1.5372 + z * -0.4986
    g = x * -0.9689 + y * 1.8758 + z * 0.0415
    b = x * 0.0557 + y * -0.2040 + z * 1.0570
    
    def inv_pivot(c):
        return ((c + 0.055) / 1.055) ** (1 / 2.4) if c > 0.04045 else c * 12.92
    
    r = inv_pivot(r)
    g = inv_pivot(g)
    b = inv_pivot(b)
    return max(0.0, min(1.0, r)), max(0.0, min(1.0, g)), max(0.0, min(1.0, b))


def _lab_to_rgb(L: float, a: float, b: float) -> tuple[float, float, float]:
    """Convert Lab to normalized RGB (0-1)."""
    x, y, z = _lab_to_xyz(L, a, b)
    return _xyz_to_rgb(x, y, z)


def _lch_to_lab(L: float, C: float, H: float) -> tuple[float, float, float]:
    """Convert LCH to Lab (reverse of lab_to_lch)."""
    H_rad = math.radians(H % 360)
    a = C * math.cos(H_rad)
    b = C * math.sin(H_rad)
    return L, a, b


def classify_from_hex(hex_str: str):
    """
    Classify color family from HEX color string.

    Args:
        hex_str: HEX color string (e.g., "#FF0000" or "FF0000")

    Returns:
        dict with keys: family_id (int), family_name (str), scores (dict)
    """
    hex_str = hex_str.strip()
    if not hex_str.startswith("#"):
        hex_str = "#" + hex_str

    # Convert HEX to all color spaces
    try:
        r01, g01, b01 = hex_to_rgb(hex_str)
        h01, s01, v01 = hex_to_hsv(hex_str)
    except ValueError as e:
        raise ValueError(f"Invalid HEX color: {hex_str}") from e

    # RGB -> HSL
    h_h, s_h, l_h = rgb01_to_hsl(r01, g01, b01)
    hsl_h = h_h if h_h is not None else None

    # RGB -> LAB
    lab_l, lab_a, lab_b = rgb_to_lab(r01, g01, b01)

    # LAB -> LCH
    lch_l, lch_c, lch_h = lab_to_lch(lab_l, lab_a, lab_b)

    # HSV (already from hex_to_hsv)
    hsv_h = h01 * 360.0
    hsv_s = s01
    hsv_v = v01

    return classify(
        h=hsl_h,
        s=s_h,  # Already 0-1
        l=l_h,  # Already 0-1
        L=lab_l,
        a=lab_a,
        b=lab_b,
        lch_l=lch_l,
        lch_c=lch_c,
        lch_h=lch_h,
        hsv_h=hsv_h,
        hsv_s=hsv_s,
        hsv_v=hsv_v,
    )


def classify_from_hsl(h: float | None, s: float, l: float):
    """
    Classify color family from HSL values.

    Args:
        h: HSL hue in degrees (0-360), can be None for greys
        s: HSL saturation (0-1)
        l: HSL lightness (0-1)

    Returns:
        dict with keys: family_id (int), family_name (str), scores (dict)
    """
    # Convert HSL -> RGB -> LAB
    r01, g01, b01 = _hsl_to_rgb(h if h is not None else 0.0, s, l)

    # RGB -> LAB
    lab_l, lab_a, lab_b = rgb_to_lab(r01, g01, b01)

    # LAB -> LCH
    lch_l, lch_c, lch_h = lab_to_lch(lab_l, lab_a, lab_b)

    # RGB -> HSV
    hsv_h, hsv_s, hsv_v = _rgb_to_hsv(r01, g01, b01)

    return classify(
        h=h,
        s=s,
        l=l,
        L=lab_l,
        a=lab_a,
        b=lab_b,
        lch_l=lch_l,
        lch_c=lch_c,
        lch_h=lch_h,
        hsv_h=hsv_h,
        hsv_s=hsv_s,
        hsv_v=hsv_v,
    )


def classify_from_hsv(h: float | None, s: float, v: float):
    """
    Classify color family from HSV values.

    Args:
        h: HSV hue in degrees (0-360), can be None for greys
        s: HSV saturation (0-1)
        v: HSV value (0-1)

    Returns:
        dict with keys: family_id (int), family_name (str), scores (dict)
    """
    # Convert HSV -> RGB -> HSL, LAB
    r01, g01, b01 = _hsv_to_rgb(h if h is not None else 0.0, s, v)

    # RGB -> HSL
    h_h, s_h, l_h = rgb01_to_hsl(r01, g01, b01)
    hsl_h = h_h if h_h is not None else None

    # RGB -> LAB
    lab_l, lab_a, lab_b = rgb_to_lab(r01, g01, b01)

    # LAB -> LCH
    lch_l, lch_c, lch_h = lab_to_lch(lab_l, lab_a, lab_b)

    return classify(
        h=hsl_h,
        s=s_h,
        l=l_h,
        L=lab_l,
        a=lab_a,
        b=lab_b,
        lch_l=lch_l,
        lch_c=lch_c,
        lch_h=lch_h,
        hsv_h=h,
        hsv_s=s,
        hsv_v=v,
    )


def classify_from_lab(L: float, a: float, b: float):
    """
    Classify color family from LAB values.

    Args:
        L: LAB lightness (0-100)
        a: LAB a component (can be negative)
        b: LAB b component (can be negative)

    Returns:
        dict with keys: family_id (int), family_name (str), scores (dict)
    """
    # LAB -> LCH
    lch_l, lch_c, lch_h = lab_to_lch(L, a, b)

    # LAB -> RGB (for HSL/HSV)
    r01, g01, b01 = _lab_to_rgb(L, a, b)

    # RGB -> HSL
    h_h, s_h, l_h = rgb01_to_hsl(r01, g01, b01)
    hsl_h = h_h if h_h is not None else None

    # RGB -> HSV
    hsv_h, hsv_s, hsv_v = _rgb_to_hsv(r01, g01, b01)

    return classify(
        h=hsl_h,
        s=s_h,
        l=l_h,
        L=L,
        a=a,
        b=b,
        lch_l=lch_l,
        lch_c=lch_c,
        lch_h=lch_h,
        hsv_h=hsv_h,
        hsv_s=hsv_s,
        hsv_v=hsv_v,
    )


def classify_from_lch(L: float, C: float, H: float):
    """
    Classify color family from LCH values.

    Args:
        L: LCH lightness (0-100)
        C: LCH chroma (>=0)
        H: LCH hue in degrees (0-360)

    Returns:
        dict with keys: family_id (int), family_name (str), scores (dict)
    """
    # LCH -> LAB
    lab_l, lab_a, lab_b = _lch_to_lab(L, C, H)

    # LAB -> RGB (for HSL/HSV)
    r01, g01, b01 = _lab_to_rgb(lab_l, lab_a, lab_b)

    # RGB -> HSL
    h_h, s_h, l_h = rgb01_to_hsl(r01, g01, b01)
    hsl_h = h_h if h_h is not None else None

    # RGB -> HSV
    hsv_h, hsv_s, hsv_v = _rgb_to_hsv(r01, g01, b01)

    return classify(
        h=hsl_h,
        s=s_h,
        l=l_h,
        L=lab_l,
        a=lab_a,
        b=lab_b,
        lch_l=L,
        lch_c=C,
        lch_h=H,
        hsv_h=hsv_h,
        hsv_s=hsv_s,
        hsv_v=hsv_v,
    )


def classify_from_all(
    hsl=None,
    hsv=None,
    lab=None,
    lch=None,
):
    """
    Classify color family from all available color spaces.
    Requires at least one color space to be provided.

    Args:
        hsl: Tuple (h, s, l) where h in degrees (0-360), s/l in 0-1
        hsv: Tuple (h, s, v) where h in degrees (0-360), s/v in 0-1
        lab: Tuple (L, a, b) where L in 0-100, a/b can be negative
        lch: Tuple (L, C, H) where L in 0-100, C>=0, H in degrees (0-360)

    Returns:
        dict with keys: family_id (int), family_name (str), scores (dict)

    Raises:
        ValueError: If no color space is provided or if LAB cannot be determined
    """
    # Extract values from tuples
    hsl_h, hsl_s, hsl_l = (None, None, None)
    hsv_h, hsv_s, hsv_v = (None, None, None)
    lab_l, lab_a, lab_b = (None, None, None)
    lch_l, lch_c, lch_h = (None, None, None)

    if hsl is not None:
        hsl_h, hsl_s, hsl_l = hsl
    if hsv is not None:
        hsv_h, hsv_s, hsv_v = hsv
    if lab is not None:
        lab_l, lab_a, lab_b = lab
    if lch is not None:
        lch_l, lch_c, lch_h = lch

    # We need LAB as a minimum - compute if missing
    if lab_l is None:
        if lch is not None:
            # LCH -> LAB
            lab_l, lab_a, lab_b = _lch_to_lab(lch_l, lch_c, lch_h)
        elif hsl is not None:
            # HSL -> RGB -> LAB
            r01, g01, b01 = _hsl_to_rgb(hsl_h if hsl_h is not None else 0.0, hsl_s, hsl_l)
            lab_l, lab_a, lab_b = rgb_to_lab(r01, g01, b01)
        elif hsv is not None:
            # HSV -> RGB -> LAB
            r01, g01, b01 = _hsv_to_rgb(hsv_h if hsv_h is not None else 0.0, hsv_s, hsv_v)
            lab_l, lab_a, lab_b = rgb_to_lab(r01, g01, b01)
        else:
            raise ValueError("At least one color space must be provided")

    # Fill in missing spaces if we have LAB
    if hsl_s is None and hsl_l is None:
        # LAB -> RGB -> HSL
        r01, g01, b01 = _lab_to_rgb(lab_l, lab_a, lab_b)
        h_h, s_h, l_h = rgb01_to_hsl(r01, g01, b01)
        if hsl_h is None:
            hsl_h = h_h if h_h is not None else None
        if hsl_s is None:
            hsl_s = s_h
        if hsl_l is None:
            hsl_l = l_h

    if hsv_s is None and hsv_v is None:
        # LAB -> RGB -> HSV
        r01, g01, b01 = _lab_to_rgb(lab_l, lab_a, lab_b)
        h_h, s_h, v_h = _rgb_to_hsv(r01, g01, b01)
        if hsv_h is None:
            hsv_h = h_h
        if hsv_s is None:
            hsv_s = s_h
        if hsv_v is None:
            hsv_v = v_h

    if lch_l is None and lch_c is None and lch_h is None:
        # LAB -> LCH
        lch_l, lch_c, lch_h = lab_to_lch(lab_l, lab_a, lab_b)

    return classify(
        h=hsl_h,
        s=hsl_s,
        l=hsl_l,
        L=lab_l,
        a=lab_a,
        b=lab_b,
        lch_l=lch_l,
        lch_c=lch_c,
        lch_h=lch_h,
        hsv_h=hsv_h,
        hsv_s=hsv_s,
        hsv_v=hsv_v,
    )

