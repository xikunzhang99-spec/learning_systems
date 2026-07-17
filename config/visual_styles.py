"""Visual style configuration library for image generation.

Each style defines positive/negative prompts, lighting, color, and
quality descriptors. Negative prompts are merged with global defaults.
"""

DEFAULT_NEGATIVE = (
    "no text, no letters, no words, no captions, no subtitles, "
    "no speech bubbles, no dialogue boxes, no typography, "
    "no watermark, no logo, no UI elements, no signage"
)

VISUAL_STYLES = {
    "american_comic": {
        "name": "American Comic",
        "positive": (
            "american comic book style, bold black outlines, flat colors, "
            "halftone dots and screentones, dynamic panel composition, "
            "graphic novel aesthetic, strong inking, cel shading"
        ),
        "negative": (
            "photorealistic, 3d render, soft shading, gradients, "
            "manga screentone, anime eyes"
        ),
        "lighting": "dramatic high-contrast lighting, strong shadows, rim light",
        "color": "vibrant saturated comic book palette, primary colors, limited color range",
        "quality": "high quality illustration, clean lines, professional comic art",
    },
    "anime": {
        "name": "Anime",
        "positive": (
            "japanese anime style, clean linework, cel shading, "
            "large expressive eyes, soft hair shading, studio ghibli inspired, "
            "beautiful background art, atmospheric lighting"
        ),
        "negative": (
            "photorealistic, 3d render, western comic style, thick outlines, "
            "halftone dots, realistic proportions"
        ),
        "lighting": "soft diffused lighting, volumetric light rays, warm sunlight, bloom effect",
        "color": "pastel and soft color palette, harmonious colors, seasonal tones",
        "quality": "high quality anime illustration, detailed background, professional animation art",
    },
    "cinematic": {
        "name": "Cinematic",
        "positive": (
            "cinematic lighting, film grain, shallow depth of field, "
            "movie poster composition, dramatic atmosphere, lens flare, "
            "photorealistic rendering, 35mm film aesthetic"
        ),
        "negative": (
            "cartoon, illustration, flat colors, cel shading, "
            "comic lines, anime style, low poly 3d"
        ),
        "lighting": "cinematic three-point lighting, golden hour, volumetric fog, practical lights",
        "color": "cinematic color grading, teal and orange, desaturated shadows, filmic look",
        "quality": "4K, highly detailed, photorealistic, octane render, ray tracing",
    },
    "hand_drawn": {
        "name": "Hand-drawn Sketch",
        "positive": (
            "hand-drawn illustration, pencil sketch texture, watercolor wash, "
            "ink lines, artistic, organic brushstrokes, sketchbook aesthetic, "
            "loose and expressive linework, visible paper texture"
        ),
        "negative": (
            "digital art, vector graphics, perfect lines, cel shading, "
            "3d render, glossy, smooth gradients, comic book inking"
        ),
        "lighting": "natural light, soft shadows, paper white highlights, ambient occlusion",
        "color": "muted earthy tones, watercolor bleeding, subtle color washes, monochrome accents",
        "quality": "artistic illustration, gallery quality, expressive style",
    },
    "flat_design": {
        "name": "Modern Flat Design",
        "positive": (
            "modern flat design illustration, clean geometric shapes, "
            "minimalist composition, bold colors, vector art style, "
            "2d flat shading, simple gradients, crisp edges"
        ),
        "negative": (
            "3d render, realistic textures, complex shading, outlines, "
            "hand-drawn lines, painterly, brush strokes, photorealism"
        ),
        "lighting": "even flat lighting, subtle ambient shadows, clean highlights",
        "color": "bold modern palette, flat colors, complementary color schemes, solid fills",
        "quality": "clean vector illustration, professional UI illustration quality",
    },
}


def get_style(style_id):
    """Get a visual style config by ID. Falls back to default if not found."""
    if style_id in VISUAL_STYLES:
        return VISUAL_STYLES[style_id]
    return get_default_style()


def list_styles():
    """Return list of available style IDs."""
    return list(VISUAL_STYLES.keys())


def get_style_name(style_id):
    """Return human-readable style name."""
    style = get_style(style_id)
    return style.get("name", style_id)


def get_default_style():
    """Return the default style (american_comic)."""
    return VISUAL_STYLES.get("american_comic", list(VISUAL_STYLES.values())[0])


def build_positive_prompt(style_id):
    """Build the full positive prompt for a given style."""
    style = get_style(style_id)
    parts = [
        style["positive"],
        style["lighting"],
        style["color"],
        style["quality"],
    ]
    return ", ".join(parts)


def build_negative_prompt(style_id):
    """Build the full negative prompt: style-specific + global default."""
    style = get_style(style_id)
    style_neg = style.get("negative", "")
    if style_neg:
        return f"{DEFAULT_NEGATIVE}, {style_neg}"
    return DEFAULT_NEGATIVE


def get_style_choices():
    """Return list of (style_id, style_name) for Streamlit selectbox."""
    return [(sid, s["name"]) for sid, s in VISUAL_STYLES.items()]
