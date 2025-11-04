"""
Core color family classification logic using multi-color-space scoring.
"""

# Color family IDs and names
FAMILY_ID_TO_NAME = {
    1: "Black",
    2: "White / Off White",
    3: "Grey",
    4: "Brown",
    5: "Green",
    6: "Red",
    7: "Pink",
    8: "Orange",
    9: "Yellow",
    10: "Turquoise / Teal",
    11: "Blue",
    12: "Purple / Violet",
    13: "Unknown",
}


def classify(
    h=None,
    s=None,
    l=None,
    L=None,
    a=None,
    b=None,
    lch_l=None,
    lch_c=None,
    lch_h=None,
    hsv_h=None,
    hsv_s=None,
    hsv_v=None,
):
    """
    Classify color family using multi-color-space scoring system.
    Uses HSL, Lab, LCH, and HSV color spaces for robust classification.
    Each color family is scored based on how many conditions it matches.
    The family with the highest score wins.

    Args:
        h: HSL hue in degrees (0-360)
        s: HSL saturation (0-1)
        l: HSL lightness (0-1)
        L: LAB lightness (0-100)
        a: LAB a component (can be negative)
        b: LAB b component (can be negative)
        lch_l: LCH lightness (0-100)
        lch_c: LCH chroma (>=0)
        lch_h: LCH hue in degrees (0-360)
        hsv_h: HSV hue in degrees (0-360)
        hsv_s: HSV saturation (0-1)
        hsv_v: HSV value (0-1)

    Returns:
        dict with keys: family_id (int), family_name (str), scores (dict of family_id -> score)
    """
    # Color family IDs
    BLACK = 1
    WHITE = 2
    GREY = 3
    BROWN = 4
    GREEN = 5
    RED = 6
    PINK = 7
    ORANGE = 8
    YELLOW = 9
    TURQUOISE_TEAL = 10
    BLUE = 11
    PURPLE_VIOLET = 12
    UNKNOWN = 13

    # Check for None values - if critical values are missing, return Unknown
    if L is None:
        return {
            "family_id": UNKNOWN,
            "family_name": FAMILY_ID_TO_NAME[UNKNOWN],
            "scores": {},
        }

    # Normalize hues to 0-360
    if h is not None:
        h = h % 360
    if lch_h is not None:
        lch_h = lch_h % 360
    if hsv_h is not None:
        hsv_h = hsv_h % 360

    # Helper to check if value is in range (handling None)
    def check(val, min_val, max_val):
        if val is None:
            return False
        return min_val <= val <= max_val

    # Helper to check wrapped hue range
    def hue_wrapped(h_val, min1, max1):
        if h_val is None:
            return False
        if min1 <= max1:
            return min1 <= h_val <= max1
        else:  # Wrapped (e.g., 340-20)
            return h_val >= min1 or h_val <= max1

    # Perplexity scoring functions (each returns a score)
    def check_black():
        score = 0
        # Pure black should score highest
        if L <= 10:
            score += 2  # Higher weight for very dark
        elif L <= 15:
            score += 1
        if l is not None and l < 0.1 and s is not None and s < 0.1:
            score += 1
        if hsv_v is not None and hsv_v < 0.15 and hsv_s is not None and hsv_s < 0.2:
            score += 1
        # Bonus: very low LAB L (< 5) should strongly indicate black
        if L <= 5:
            score += 1
        return score

    def check_white_offwhite():
        score = 0
        if L >= 85:
            score += 1
        if s is not None and s <= 0.15:
            score += 1
        if l is not None and l >= 0.9 and s is not None and s <= 0.15:
            score += 1
        if hsv_v is not None and hsv_v >= 0.9 and hsv_s is not None and hsv_s <= 0.15:
            score += 1
        return score

    def check_grey():
        score = 0
        # Grey requires low saturation in BOTH HSL and HSV
        if s is not None and s <= 0.15:
            score += 1
        else:
            return 0
        if hsv_s is not None and hsv_s <= 0.15:
            score += 1
        else:
            if hsv_s is None or hsv_s > 0.2:
                return 0
        if 15 < L < 85:
            score += 1
        # Exclude very dark (true blacks) from grey; let Black handle them
        if L is not None and L <= 15:
            return 0
        # LAB neutrality: penalize if a or b deviates from 0 significantly (cool/warm greys should not be grey)
        if a is not None and b is not None:
            if -8 <= a <= 8 and -8 <= b <= 8:
                score += 1
                # Stronger weight for very dark neutral greys (e.g., Black Templar)
                if L is not None and 15 < L <= 25 and s is not None and s <= 0.12:
                    score += 2
            else:
                # Penalize colored bias
                if b > 5:
                    score -= 2  # warm bias toward brown/yellow
                if b < -5:
                    score -= 2  # cool bias toward blue/purple
                if a > 10 or a < -10:
                    score -= 1
        if lch_c is not None and lch_c <= 10:
            score += 1
        return max(0, score)

    def check_brown():
        score = 0
        # CRITICAL: Brown requires hue in brown range (15-45°)
        # If hue is NOT in brown range, heavily penalize or disqualify
        if h is not None and 15 <= h <= 45:
            score += 2  # Higher weight for hue match
        else:
            # If hue is not in brown range, it's likely red/orange/yellow/purple
            # Only allow if saturation is very low (muted browns might appear in other hue ranges)
            if s is not None and s < 0.3:
                score += 1  # Low saturation might still be brown-ish
            else:
                return 0  # Disqualify: hue not in range AND saturation too high
        # Slightly extend upper hue bound when saturation is moderate/low (catch orange-browns and hides)
        if h is not None and 45 < h <= 48 and s is not None and s <= 0.35:
            score += 1
        # Extend lower bound slightly when saturation is moderate/low
        if h is not None and 12 <= h < 15 and s is not None and s <= 0.4:
            score += 1
        # Saturation should be moderate for browns (not very high like reds)
        if s is not None and 0.09 <= s <= 0.7:
            score += 1
        elif s is not None and s > 0.7:
            # Very high saturation suggests red/orange, not brown
            score -= 2  # Heavy penalty
        if l is not None and 0.1 <= l <= 0.5:
            score += 1
        # Bright bone/dust/dune colors (higher lightness but still brown)
        if (
            l is not None
            and 0.5 <= l <= 0.75
            and h is not None
            and 15 <= h <= 50
            and a is not None
            and 5 <= a <= 30
            and b is not None
            and 15 <= b <= 50
        ):
            score += 2
        if 15 <= L <= 55:
            score += 1
        # Bright browns (LAB L in higher range)
        if (
            L is not None
            and 55 <= L <= 75
            and a is not None
            and 8 <= a <= 25
            and b is not None
            and 18 <= b <= 45
        ):
            score += 2
        # Key: Both LAB a and b should be positive, but NOT very high
        # Very high LAB a (>30) suggests red, not brown
        # Very high LAB b (>40) suggests yellow/orange, not brown
        if a is not None and b is not None:
            if a > 5 and b > 5:
                if a > 30:
                    score -= 3  # Heavy penalty: very high a = red, not brown
                elif b > 40:
                    score -= 2  # Penalty: very high b = yellow/orange
                else:
                    score += 2  # Both positive and moderate = brown
            elif b is not None and b > 5 and a is not None and a <= 5:
                # Positive b but neutral/low a might be brown (e.g., Sylvaneth Bark)
                if b <= 15:
                    score += 1
                else:
                    score -= 1  # Penalty if b is too high
            elif b is not None and b <= 0:
                return (
                    0  # Negative b disqualifies brown (these are purples/blues/greens)
                )
        # LCH hue should also be in brown range
        if lch_h is not None and 15 <= lch_h <= 45:
            score += 1
        # Boost for typical skin/brown region (helps Bugman's Glow / Tuskgor / Deathclaw / Thondia / Cygor)
        if (
            h is not None
            and 10 <= h <= 38
            and l is not None
            and 0.2 <= l <= 0.6
            and a is not None
            and 5 <= a <= 25
            and b is not None
            and 8 <= b <= 30
        ):
            score += 2
        # Strong cluster for brown irrespective of hue (high a, mid b, medium/dark lightness)
        if (
            L is not None
            and 28 <= L <= 55
            and a is not None
            and 20 <= a <= 40
            and b is not None
            and 15 <= b <= 30
            and l is not None
            and 0.25 <= l <= 0.6
            and s is not None
            and 0.25 <= s <= 0.75
        ):
            score += 4
        # HSV saturation should be moderate
        if hsv_s is not None and 0.15 <= hsv_s <= 0.7:
            score += 1
        elif hsv_s is not None and 0.1 <= hsv_s < 0.15:
            score += 1  # Also catch slightly lower saturation browns
        elif hsv_s is not None and hsv_s > 0.7:
            score -= 1  # Penalty for very high HSV saturation
        if hsv_v is not None and 0.2 <= hsv_v <= 0.6:
            score += 1
        return max(0, score)  # Don't allow negative

    def check_green():
        score = 0
        # Hue
        if h is not None and 75 <= h <= 150:
            score += 2
            if 95 <= h <= 135:
                # Only grant core bonus when not clearly red-biased
                if a is None or a <= 2:
                    score += 1  # core green band
        # Lower saturation threshold to catch muted/olive greens
        if s is not None and s >= 0.05:
            score += 1
            if s >= 0.25:
                score += 1
            if s >= 0.35:
                score += 1
        if l is not None and 0.15 <= l <= 0.85:
            score += 1
        # LAB: Negative a is key for green
        if a is not None and a < -3:
            score += 2
            if a < -10:
                score += 1
        elif a is not None and a < 0:
            score += 1
        # Bias checks
        # Strong blue/teal bias
        if b is not None and b < -10:
            score -= 3
        if a is not None and a > 5:
            score -= 2  # red/brown bias
        # Strong red/orange bias (bones/light browns) — push out of green
        if (
            h is not None
            and 20 <= h <= 45
            and l is not None
            and 0.45 <= l <= 0.9
            and a is not None
            and 8 <= a <= 35
            and b is not None
            and 15 <= b <= 55
        ):
            score -= 5
        # Bright bone/dust/dune with positive a/b (definitely brown, not green)
        if (
            l is not None
            and 0.5 <= l <= 0.75
            and h is not None
            and 15 <= h <= 50
            and a is not None
            and 5 <= a <= 30
            and b is not None
            and 15 <= b <= 50
        ):
            score -= 6
        # Olive green boost (yellowish greens)
        if (
            h is not None
            and 60 <= h <= 95
            and a is not None
            and -10 <= a <= 5
            and b is not None
            and 15 <= b <= 45
        ):
            score += 2
        if lch_h is not None and 90 <= lch_h <= 160:
            score += 1
        # Teal boundary penalty using LCH hue
        if lch_h is not None and 150 <= lch_h <= 195:
            score -= 3
        if h is not None and 150 <= h <= 195:
            score -= 2
        # Gold/Yellow metallic region — push to Yellow/Orange
        if (
            lch_h is not None
            and 45 <= lch_h <= 85
            and ((lch_c is not None and lch_c >= 35) or (b is not None and b >= 45))
        ):
            score -= 5
        # Push yellowish strong hues out of green
        if h is not None and h >= 38 and b is not None and b >= 50:
            score -= 3
        # Red band penalty (e.g., Word Bearers Red accidentally in green)
        if (h is not None and (h >= 340 or h <= 20)) or (
            lch_h is not None and (lch_h >= 340 or lch_h <= 20)
        ):
            if a is not None and a > 20:
                score -= 6
        # Greyish penalty
        if s is not None and s < 0.12 and (lch_c is not None and lch_c < 12):
            score -= 3
        # Neutral grey-like values — push to Grey/Off-white
        if (
            s is not None
            and s < 0.1
            and a is not None
            and -8 <= a <= 8
            and b is not None
            and -8 <= b <= 8
        ):
            score -= 5
        # Very dark greys/black (e.g., Black Templar)
        if (
            L is not None
            and L <= 20
            and s is not None
            and s <= 0.2
            and ((a is not None and -5 <= a <= 5) or (b is not None and -5 <= b <= 5))
        ):
            score -= 6
        # Outside green hue with no negative a -> likely not green
        if h is not None and not (75 <= h <= 150) and (a is not None and a >= -2):
            score -= 2
        # HSV saturation
        if hsv_s is not None and hsv_s >= 0.05:
            score += 1
            if hsv_s >= 0.25:
                score += 1
            if hsv_s >= 0.35:
                score += 1
        if hsv_v is not None and 0.15 <= hsv_v <= 0.85:
            score += 1
        return max(0, score)

    def check_red():
        score = 0
        if h is not None and hue_wrapped(h, 340, 20):
            score += 2  # Higher weight for red hue
        # If hue lies in classic pink band (315-345), reduce red score, especially for lighter tones
        if h is not None and 315 <= h <= 345:
            score -= 2
            if l is not None and l >= 0.55:
                score -= 1
        # Penalize red when LAB b is negative (magenta/purple bias) within pink bands
        if b is not None and b <= -5:
            if (
                (h is not None and 315 <= h <= 345)
                or (lch_h is not None and 315 <= lch_h <= 345)
                or (hsv_h is not None and 315 <= hsv_h <= 345)
            ):
                score -= 4
        # Penalize when hue falls in orange band
        if h is not None and 30 < h <= 55:
            score -= 3
        # Also penalize near-orange band if strong yellow component
        if h is not None and 25 < h <= 30 and b is not None and b > 20:
            score -= 2
        # Penalize low-hue red when yellow component is strong (push to orange)
        if (
            h is not None
            and h < 15
            and b is not None
            and b >= 22
            and a is not None
            and 20 <= a <= 45
        ):
            score -= 3
        if s is not None and s >= 0.5:
            score += 1
            if s >= 0.7:
                score += 1  # Bonus for very high saturation (strong red indicator)
        # Very light reds are likely pinks/skin
        if l is not None and 0.3 <= l <= 0.7:
            score += 1
        elif l is not None and l >= 0.6:
            score -= 2  # Pushes toward pink
        # CRITICAL: Very high LAB a (>30) is strong red indicator
        if a is not None and a > 15:
            score += 2  # Higher weight
            if a > 30:
                score += 2  # Bonus for very high a (definite red)
        # If b is extremely high, this leans orange/yellow
        if b is not None and b > 40:
            score -= 2
        if lch_h is not None and hue_wrapped(lch_h, 340, 20):
            score += 1
        if hsv_s is not None and hsv_s >= 0.5:
            score += 1
            if hsv_s >= 0.7:
                score += 1  # Bonus for very high HSV saturation
        if hsv_v is not None and 0.4 <= hsv_v <= 0.7:
            score += 1
        # Strong red indicator: very low hue, very high a/b and high saturation/value
        if h is not None and h < 12 and a is not None and a >= 50:
            if (
                (s is not None and s >= 0.8) or (hsv_s is not None and hsv_s >= 0.8)
            ) and (
                (b is not None and b >= 35) or (hsv_v is not None and hsv_v >= 0.55)
            ):
                score += 3
        return max(0, score)

    def check_pink():
        score = 0
        if h is not None and (315 <= h <= 345):
            score += 3  # stronger weight for pink band
        if h is not None and (20 < h <= 35):
            score += 2
        # Penalize orange-like hues for pink, especially with high b (yellow component)
        if h is not None and 30 < h <= 55 and b is not None and b > 25:
            score -= 3
        # Stronger penalty for clear orange/yellow signature
        if h is not None and 25 <= h <= 60 and b is not None and b > 20:
            score -= 4
        # Penalize brown-like signature for pink (brown range hue, darker l, positive b)
        if (
            h is not None
            and 15 <= h <= 45
            and l is not None
            and l <= 0.5
            and b is not None
            and b > 5
        ):
            score -= 2
        # Penalize brown/skin cluster irrespective of hue when saturation is low to mid
        if (
            s is not None
            and s <= 0.4
            and l is not None
            and 0.2 <= l <= 0.6
            and a is not None
            and 5 <= a <= 25
            and b is not None
            and 8 <= b <= 30
        ):
            score -= 3
        # Extra penalty for orange-leaning low hue (5-20°) with high b at mid/high lightness
        if (
            h is not None
            and 5 <= h <= 20
            and b is not None
            and b >= 22
            and l is not None
            and l >= 0.5
        ):
            score -= 4
        # Penalty for gold-like range around 20-30° with moderate b when bright
        if (
            h is not None
            and 20 <= h <= 30
            and b is not None
            and b >= 18
            and l is not None
            and l >= 0.55
        ):
            score -= 3
        # Allow magentas slightly earlier (300-315°) when LAB is magenta-like
        if (
            h is not None
            and 300 <= h < 315
            and a is not None
            and a > 20
            and b is not None
            and -10 <= b <= 10
        ):
            score += 2
        # Allow magentas with slightly negative b to count as pink if a is high
        if a is not None and a > 15 and b is not None and -10 <= b <= 25:
            score += 2
        # Strong magenta boost across hue spaces (helps Sigvald Burgundy / Volupus Pink)
        if a is not None and a > 25 and b is not None and -15 <= b <= 5:
            if (h is not None and 300 <= h <= 350) or (
                lch_h is not None and (300 <= lch_h <= 360 or 0 <= lch_h <= 20)
            ) or (hsv_h is not None and 300 <= hsv_h <= 350):
                score += 3
        # Pink/skin tones can have moderate saturation
        if s is not None and s >= 0.25:
            score += 1
            if s >= 0.4:
                score += 1
        # Broaden lightness to include skin/flesh
        if l is not None and 0.45 <= l <= 0.92:
            score += 1
            if l >= 0.6 and a is not None and a > 10:
                score += 1  # Light + high a -> pink/skin
        # Prefer pink when light and in pink hue band even if red is strong
        if h is not None and 315 <= h <= 345 and l is not None and l >= 0.55:
            score += 1
        # LAB: positive a and non-strongly-negative b (permit slight negative for magenta)
        if a is not None and a > 10 and b is not None and b >= -10:
            score += 1
            if 0 <= b <= 25:
                score += 1  # common skin-tones range
        elif a is not None and a > 5 and (b is None or b >= -10):
            score += 1
        if lch_h is not None and ((315 <= lch_h <= 345) or (20 <= lch_h <= 35)):
            score += 1
        if hsv_s is not None and hsv_s >= 0.25:
            score += 1
            if hsv_s >= 0.4:
                score += 1
        if hsv_v is not None and hsv_v >= 0.5:
            score += 1
        # Penalties
        if b is not None and b < -20:
            score -= 3  # too purple
        if b is not None and b > 40:
            score -= 2  # too yellow/orange (push to orange/yellow)
        # Penalize strong yellow signature in LCH for pink
        if lch_h is not None and 45 <= lch_h <= 75 and lch_c is not None and lch_c >= 40:
            score -= 2
        # Strong brown/skin cluster should not be pink
        if (
            L is not None
            and 28 <= L <= 55
            and a is not None
            and 20 <= a <= 40
            and b is not None
            and 15 <= b <= 30
            and l is not None
            and 0.25 <= l <= 0.6
            and s is not None
            and 0.25 <= s <= 0.75
        ):
            score -= 5
        return max(0, score)

    def check_orange():
        score = 0
        if h is not None and 30 < h <= 55:
            score += 3  # stronger claim for orange band
        # Copper/bronze: allow 10-30 if yellow component is strong
        if (
            h is not None
            and 10 < h <= 30
            and b is not None
            and b > 25
            and a is not None
            and a > 8
        ):
            score += 2
        # Also catch oranges in brown range (25-30) if LAB b is high
        if h is not None and 25 < h <= 30 and b is not None and b > 30:
            score += 1
        # Low-hue orange fallback (5-15°) when b is high and a is strong (e.g., Squig Orange)
        # Avoid catching deep saturated reds: require a not extremely high
        if (
            h is not None
            and 5 <= h <= 15
            and b is not None
            and b >= 22
            and a is not None
            and 20 <= a <= 45
            and l is not None
            and 0.35 <= l <= 0.65
        ):
            score += 3
        # Penalize clear reds in low hue with extremely high a
        if h is not None and h < 15 and a is not None and a > 45:
            score -= 4
        if s is not None and s >= 0.45:
            score += 1
            if s >= 0.6:
                score += 1
        if l is not None and 0.35 <= l <= 0.9:
            score += 1
        # CRITICAL: Both a and b should be positive, with high b
        if a is not None and a > 8 and b is not None and b > 18:
            # Deep reds (very low hue + extremely high a) should not gain strong orange credit
            if h is not None and h < 15 and a > 50:
                score -= 3
            else:
                score += 2  # Higher weight
                if b > 30:
                    score += 2  # Stronger bonus for very high b
                if b > 40:
                    score += 1
        # Metallic hint: high chroma supports orange assignment in 25-60°
        if lch_c is not None and lch_c >= 40 and h is not None and 25 <= h <= 60:
            score += 1
        if lch_h is not None and 30 < lch_h <= 55:
            score += 1
        # Also check for high b at brown-orange transition
        if lch_h is not None and 55 < lch_h <= 65 and b is not None and b > 30:
            score += 1
        # Penalty: yellow-like (very high b) at yellow LCH hue (70-85)
        if lch_h is not None and 70 <= lch_h <= 85 and b is not None and b >= 50:
            score -= 3
        # Penalty: yellow-like in HSL hue >= 38 with very high b
        if h is not None and h >= 38 and b is not None and b >= 50:
            score -= 2
        # Penalty: low hue (<12°) with extremely high a and high saturation (classic red)
        if (
            h is not None
            and h < 12
            and a is not None
            and a >= 50
            and ((s is not None and s >= 0.8) or (hsv_s is not None and hsv_s >= 0.8))
        ):
            score -= 4
        # Penalty: flesh/brown cluster should not be orange
        if (
            s is not None
            and s <= 0.6
            and l is not None
            and 0.2 <= l <= 0.6
            and a is not None
            and 5 <= a <= 25
            and b is not None
            and 8 <= b <= 30
        ):
            score -= 3
        # Additional penalty for brown hides (mid a/b, darker l) regardless of hue
        if (
            L is not None
            and L <= 40
            and a is not None
            and 15 <= a <= 30
            and b is not None
            and 15 <= b <= 35
            and l is not None
            and l <= 0.45
        ):
            score -= 2
        if hsv_s is not None and hsv_s >= 0.45:
            score += 1
            if hsv_s >= 0.6:
                score += 1
        # Extra penalty for canonical red hue in HSL/HSV (350-10°) with very high a
        if h is not None and ((h >= 350) or (h <= 10)) and a is not None and a >= 50:
            score -= 5
        if (
            hsv_h is not None
            and ((hsv_h >= 350) or (hsv_h <= 10))
            and a is not None
            and a >= 50
        ):
            score -= 3
        if hsv_v is not None and 0.45 <= hsv_v <= 0.95:
            score += 1
        return max(0, score)

    def check_yellow():
        score = 0
        if h is not None and 50 < h <= 75:
            score += 1
        # Gold-like yellows in lower hue (20-30°) with sufficient brightness/saturation
        if (
            h is not None
            and 20 <= h <= 30
            and b is not None
            and b >= 18
            and l is not None
            and l >= 0.55
        ):
            score += 3
        # Strong yellow bias in 35-45° with very high b
        if h is not None and 35 <= h <= 45 and b is not None and b >= 50:
            score += 3
        # Also catch yellows in orange-brown range if LAB b is very high
        if h is not None and 40 <= h <= 50:
            if b is not None and b > 50:
                score += 1  # Very high b indicates yellow even at lower hue
        if s is not None and s >= 0.4:
            score += 1
        # Widen lightness range slightly
        if l is not None and 0.4 <= l <= 0.9:
            score += 1
        if a is not None and -5 <= a <= 20:
            score += 1
        # CRITICAL: Very high LAB b (>40) is strong yellow indicator
        if b is not None and b >= 20:
            score += 2  # Higher weight
            if b >= 40:
                score += 3  # Stronger bonus for very high b (definite yellow/orange/metallic gold)
        if lch_h is not None and 50 < lch_h <= 75:
            score += 1
        # Also check for high b at lower LCH hue
        if lch_h is not None and 40 <= lch_h <= 50:
            if b is not None and b > 50:
                score += 1
        if hsv_s is not None and hsv_s >= 0.4:
            score += 1
        if hsv_v is not None and 0.5 <= hsv_v <= 0.9:
            score += 1
        # Metallic hint: high chroma supports yellow assignment (helps golds)
        if lch_c is not None and lch_c >= 40 and (h is not None and 45 <= h <= 75):
            score += 1
        # Reduce yellow if a and b are only modest and saturation is low (avoid pulling browns)
        if (
            b is not None
            and b < 20
            and s is not None
            and s < 0.3
            and l is not None
            and l < 0.6
        ):
            score -= 2
        return score

    def check_turquoise_teal():
        score = 0
        if h is not None and 145 <= h <= 195:
            score += 4
        if s is not None and s >= 0.35:
            score += 1
        if l is not None and 0.25 <= l <= 0.8:
            score += 1
        # Teal should have non-positive a and often negative b
        if a is not None and a <= 0 and b is not None and b <= 0:
            score += 3
        if lch_h is not None and 150 <= lch_h <= 195:
            score += 4
        if hsv_s is not None and hsv_s >= 0.35:
            score += 1
        if hsv_v is not None and 0.3 <= hsv_v <= 0.8:
            score += 1
        # Penalize teal if red bias
        if a is not None and a > 5:
            score -= 2
        return score

    def check_blue():
        score = 0
        # Hue range for blue
        if h is not None and 195 < h <= 255:
            score += 2
        # Allow low-saturation cool blues (e.g., Ulthuan Grey) to still score via LAB
        if b is not None and b <= -5 and (a is None or -10 <= a <= 10):
            score += 2  # Strong cool bias
            if b <= -12:
                score += 1
        # Saturation may be low for cool greys; don't require high s
        if s is not None and s >= 0.25:
            score += 1
            if s >= 0.35:
                score += 1
        if l is not None and 0.25 <= l <= 0.85:
            score += 1
        if lch_h is not None and 200 < lch_h <= 255:
            score += 1
        if hsv_s is not None and hsv_s >= 0.25:
            score += 1
            if hsv_s >= 0.35:
                score += 1
        if hsv_v is not None and 0.25 <= hsv_v <= 0.85:
            score += 1
        # Penalty if b is strongly positive (these are more likely orange/brown)
        if b is not None and b > 5:
            score -= 2
        return max(0, score)

    def check_purple_violet():
        score = 0
        if h is not None and 255 < h < 330:
            score += 2  # Higher weight for purple hue
        # Also catch purple-pinks (extend range slightly)
        if h is not None and 250 <= h <= 255:
            if a is not None and a > 5 and b is not None and b < -10:
                score += 1
        if s is not None and s >= 0.35:
            score += 1
        # Lower saturation threshold for muted purples
        if s is not None and 0.15 <= s < 0.35:
            score += 1
        if l is not None and 0.25 <= l <= 0.8:
            score += 1
        # CRITICAL: Positive a AND negative b is key purple identifier
        if a is not None and a > 5 and b is not None and b < -10:
            score += 3  # Much higher weight (key identifier!)
        elif a is not None and a > 0 and b is not None and b < -5:
            score += 2  # Still score for less extreme values
        # Disqualify if b is positive (these are browns/reds)
        if b is not None and b >= 0:
            score -= 5  # Heavy penalty
        if lch_h is not None and 255 < lch_h < 330:
            score += 1
        if hsv_s is not None and hsv_s >= 0.35:
            score += 1
        elif hsv_s is not None and 0.15 <= hsv_s < 0.35:
            score += 1  # Also catch lower saturation purples
        if hsv_v is not None and 0.25 <= hsv_v <= 0.8:
            score += 1
        return max(0, score)  # Don't allow negative

    # Score all families
    scores = {
        BLACK: check_black(),
        WHITE: check_white_offwhite(),
        GREY: check_grey(),
        BROWN: check_brown(),
        GREEN: check_green(),
        RED: check_red(),
        PINK: check_pink(),
        ORANGE: check_orange(),
        YELLOW: check_yellow(),
        TURQUOISE_TEAL: check_turquoise_teal(),
        BLUE: check_blue(),
        PURPLE_VIOLET: check_purple_violet(),
    }

    # Find the family with the highest score
    if not scores or max(scores.values()) == 0:
        family_id = UNKNOWN
        scores_dict = {k: v for k, v in scores.items()}
        return {
            "family_id": family_id,
            "family_name": FAMILY_ID_TO_NAME[family_id],
            "scores": scores_dict,
        }

    max_family = max(scores, key=scores.get)
    max_score = scores[max_family]

    # Require minimum score threshold (default 3 as per Perplexity)
    if max_score < 3:
        family_id = UNKNOWN
    else:
        family_id = max_family

    scores_dict = {k: v for k, v in scores.items()}
    return {
        "family_id": family_id,
        "family_name": FAMILY_ID_TO_NAME[family_id],
        "scores": scores_dict,
    }

