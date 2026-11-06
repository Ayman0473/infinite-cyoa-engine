"""
Visual consistency and real-time image generation engine for Infinite CYOA.
Maintains persistent character visual anchors, deterministic seeds, and unified art style prompts.
Includes instant procedural SVG scene & portrait generators for 100% offline/timeout-proof rendering.
"""
import hashlib
import urllib.parse
from typing import Dict, List, Optional, Any
from models import Character, CharacterVisualDNA, GameState


ART_STYLES: Dict[str, Dict[str, str]] = {
    "Dark Fantasy Graphic Novel": {
        "prefix": "masterpiece dark fantasy graphic novel illustration, Mike Mignola and Frank Miller aesthetic, heavy bold ink shadows, crisp cel outlines, moody chiaroscuro lighting, cinematic composition",
        "suffix": "trending on artstation, 8k resolution, richly detailed fantasy concept art, sharp focus, consistent character features --no blurry, 3d render, photo, mutated anatomy, deformed hands",
        "bg_color": "#0d0f17",
        "accent_color": "#d97706",
        "secondary_color": "#dc2626"
    },
    "Cyberpunk Synthwave": {
        "prefix": "cinematic cyberpunk digital concept art, Syd Mead and Yoji Shinkawa aesthetic, neon rain reflections, volumetric haze, crisp mechanical linework, high contrast cyan and magenta glow",
        "suffix": "masterpiece digital art, 8k, sharp focus, atmospheric futuristic scene, consistent character cybernetics --no low quality, blurry, photorealistic render",
        "bg_color": "#080c16",
        "accent_color": "#06b6d4",
        "secondary_color": "#ec4899"
    },
    "High Fantasy Watercolor": {
        "prefix": "vintage high fantasy storybook watercolor and gouache illustration, Alan Lee and Arthur Rackham style, fine quill ink linework, textured parchment paper, golden hour rim lighting",
        "suffix": "masterwork painting, rich earthy pigments, intricate details, evocative atmosphere --no photographic, smooth 3d, modern digital look",
        "bg_color": "#18130c",
        "accent_color": "#eab308",
        "secondary_color": "#15803d"
    },
    "Cosmic Void Eldritch": {
        "prefix": "dark cosmic horror illustration, H.P. Lovecraft aesthetic, Wayne Barlowe style, surreal geometric celestial architecture, deep violet and obsidian palette, eerie luminescent particles",
        "suffix": "epic scale, intricate otherworldly textures, 8k, museum quality gothic illustration --no plain, blurry, cheerful, lowres",
        "bg_color": "#0a0614",
        "accent_color": "#a855f7",
        "secondary_color": "#3b82f6"
    },
    "Cinematic Studio Anime": {
        "prefix": "masterpiece cinematic anime key visual, Studio Ghibli and Makoto Shinkai aesthetic, clean expressive line art, vibrant atmospheric lighting, detailed lush environment",
        "suffix": "8k wallpaper, stunning lighting effects, painterly anime concept art, sharp lines --no distorted, messy, photorealistic",
        "bg_color": "#0b1520",
        "accent_color": "#38bdf8",
        "secondary_color": "#f472b6"
    },
    "Medieval Woodcut Engraving": {
        "prefix": "authentic 16th century medieval woodcut engraving, Albrecht Durer style, intricate vintage crosshatching, sepia ink on aged handmade rag paper, dark historical symbolism",
        "suffix": "high contrast black and ivory print, museum archive quality, sharp etched linework --no color, 3d, modern, photographic",
        "bg_color": "#16120b",
        "accent_color": "#ca8a04",
        "secondary_color": "#78350f"
    }
}


def generate_deterministic_seed(text: str, salt: int = 0) -> int:
    """Generate a stable, reproducible integer seed from a string identifier."""
    raw = f"{text}_{salt}"
    h = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    return int(h[:8], 16) % 10000000


def build_character_visual_dna(
    name: str,
    archetype: str,
    theme: str,
    session_id: str,
    custom_desc: Optional[str] = None
) -> CharacterVisualDNA:
    """
    Constructs an immutable Visual DNA token for a character so their features
    remain invariant throughout every chapter of the adventure.
    """
    seed = generate_deterministic_seed(f"{session_id}_{name}", 99)

    # Defaults modulated by theme and archetype
    if "cyber" in theme.lower():
        face = "sharp angular jawline, faint chrome neural port at temple"
        hair = "asymmetric undercut with neon streaks"
        eyes = "augmented iridescent optical lenses with amber HUD reticle"
        attire = "weathered tactical trench coat with glowing collar seams and carbon fiber plating"
        feat = "subdermal circuit tattoos pulsing faint electric blue along neck"
        gear = "custom silenced rail-pistol holstered at ribs, data deck strapped to wrist"
    elif "cosmic" in theme.lower():
        face = "stoic pale features with silver starlight freckles"
        hair = "short cropped platinum hair swept back"
        eyes = "deep void-black irises flecked with star-cluster nebulae"
        attire = "sealed voidfarer pressurized jacket with brass gauges and insulated seals"
        feat = "tarnished astrolabe talisman humming with zero-point resonance"
        gear = "harmonic pulse scanner and telescoping ether staff"
    else:  # Eldritch / High Fantasy
        if "rogue" in archetype.lower() or "wanderer" in archetype.lower():
            face = "chiseled features, narrow thoughtful gaze, fine scar over left cheek"
            hair = "raven-black messy shoulder-length hair tied with leather cord"
            eyes = "piercing amber eyes with keen awareness"
            attire = "dark studded leather jerkin over soot-grey tunic with hooded cloak"
            feat = "curved rune brand glowing faintly violet on right forearm"
            gear = "etched obsidian hunting dagger at hip, ancient celestial ring"
        elif "scholar" in archetype.lower() or "mage" in archetype.lower():
            face = "refined high cheekbones, intense scholarly gaze"
            hair = "silver-streaked dark hair pulled back in ornate ringlets"
            eyes = "luminescent amethyst eyes that shimmer with arcane glyphs"
            attire = "high-collared midnight velvet robes trimmed with runic gold thread"
            feat = "intricate constellation marks etched into finger joints"
            gear = "leather-bound grimoire chained to iron waist-belt, bone focus wand"
        else:
            face = "hardened battle-tested visage, determined jawline"
            hair = "short dark brown hair, undercut"
            eyes = "flint-grey resolute eyes"
            attire = "dented blackened iron plate armor over weathered chainmail and wool kirtle"
            feat = "ancient crest carved into chest plate"
            gear = "broadsword with runic crossguard, heavy steel-banded heater shield"

    if custom_desc:
        face = f"{face}, {custom_desc}"

    return CharacterVisualDNA(
        name=name,
        gender_presentation="androgynous adventurer",
        face=face,
        hair=hair,
        eyes=eyes,
        attire=attire,
        distinguishing_feature=feat,
        signature_gear=gear,
        persistent_seed=seed,
        style_anchor=""
    )


def format_character_anchor(dna: CharacterVisualDNA) -> str:
    """Format the character's visual identity into a strict prompt anchor."""
    return (
        f"character '{dna.name}': {dna.face}, {dna.hair}, {dna.eyes}, "
        f"wearing {dna.attire}, distinguishing feature {dna.distinguishing_feature}, "
        f"equipped with {dna.signature_gear}"
    )


def build_scene_image_prompt(
    art_style_name: str,
    scene_description: str,
    location: str,
    characters: List[Optional[CharacterVisualDNA]],
    mood: str = "atmospheric and suspenseful"
) -> Dict[str, Any]:
    """
    Builds a unified, style-consistent image generation prompt.
    Synthesizes:
    - Art style prefix (linework, lighting, color rendering)
    - Scene environment and dramatic action
    - Persistent Character Visual Anchors (exact hair, eyes, facial traits, gear)
    - Art style suffix (quality enhancers and consistency locks)
    """
    style = ART_STYLES.get(art_style_name, ART_STYLES["Dark Fantasy Graphic Novel"])
    
    valid_characters: List[CharacterVisualDNA] = [c for c in characters if c is not None]

    char_anchors = []
    combined_seed_basis = ""
    for char in valid_characters:
        char_anchors.append(format_character_anchor(char))
        combined_seed_basis += f"{char.name}_{char.persistent_seed}_"

    char_desc = " | ".join(char_anchors) if char_anchors else "no prominent figures"

    # Strict composition
    full_prompt = (
        f"{style['prefix']}, "
        f"Scene: {scene_description} at {location}, mood {mood}. "
        f"Featuring {char_desc}. "
        f"{style['suffix']}"
    )

    # Seed calculation: combine characters' seeds with location hash for persistent scene look
    loc_seed = generate_deterministic_seed(location, 7)
    char_seed_sum = sum(getattr(c, "persistent_seed", 42) for c in valid_characters)
    final_seed = (loc_seed + char_seed_sum) % 10000000 if valid_characters else loc_seed

    # Generate Pollinations.ai URL
    encoded_prompt = urllib.parse.quote_plus(full_prompt[:800])
    image_url = (
        f"https://image.pollinations.ai/prompt/{encoded_prompt}"
        f"?width=1024&height=640&seed={final_seed}&model=flux&nologo=true"
    )

    return {
        "prompt": full_prompt,
        "seed": final_seed,
        "url": image_url,
        "art_style": art_style_name,
        "characters_depicted": [c.name for c in valid_characters]
    }


def generate_svg_portrait(dna: CharacterVisualDNA, art_style: str) -> str:
    """
    Generates a procedural SVG avatar for a character based on their DNA and art style.
    Provides instant, 100% offline visuals for the character codex and sidebar.
    """
    style = ART_STYLES.get(art_style, ART_STYLES["Dark Fantasy Graphic Novel"])
    accent = style["accent_color"]
    bg = style["bg_color"]
    
    # Deterministic palette based on seed
    seed = getattr(dna, "persistent_seed", 42)
    h1 = (seed * 37) % 360
    h2 = (seed * 73) % 360

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200" width="100%" height="100%" class="character-portrait-svg">
      <defs>
        <radialGradient id="grad_{seed}" cx="50%" cy="40%" r="60%">
          <stop offset="0%" stop-color="hsl({h1}, 70%, 25%)" />
          <stop offset="100%" stop-color="{bg}" />
        </radialGradient>
        <linearGradient id="edge_{seed}" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" stop-color="{accent}" stop-opacity="0.8"/>
          <stop offset="100%" stop-color="hsl({h2}, 60%, 40%)" stop-opacity="0.2"/>
        </linearGradient>
        <filter id="glow_{seed}" x="-20%" y="-20%" width="140%" height="140%">
          <feGaussianBlur stdDeviation="3" result="blur" />
          <feComposite in="SourceGraphic" in2="blur" operator="over" />
        </filter>
      </defs>
      
      <!-- Background Circle / Frame -->
      <rect width="200" height="200" rx="16" fill="url(#grad_{seed})" />
      <rect width="194" height="194" x="3" y="3" rx="14" fill="none" stroke="url(#edge_{seed})" stroke-width="2" />
      
      <!-- Atmospheric Runic / Tech Ring -->
      <circle cx="100" cy="100" r="78" fill="none" stroke="{accent}" stroke-opacity="0.25" stroke-dasharray="4 8" stroke-width="1.5"/>
      <circle cx="100" cy="100" r="64" fill="none" stroke="hsl({h2}, 80%, 60%)" stroke-opacity="0.3" stroke-width="1"/>
      
      <!-- Character Silhouette / Form -->
      <!-- Shoulders / Cloak -->
      <path d="M 35 195 Q 60 145 100 140 Q 140 145 165 195 Z" fill="hsl({h1}, 35%, 15%)" stroke="{accent}" stroke-width="1.5" stroke-opacity="0.5"/>
      <path d="M 50 195 L 85 145 L 115 145 L 150 195 Z" fill="hsl({h2}, 30%, 20%)" opacity="0.6"/>
      
      <!-- Neck -->
      <rect x="88" y="115" width="24" height="30" rx="4" fill="hsl({h1}, 25%, 35%)"/>
      
      <!-- Head / Face -->
      <ellipse cx="100" cy="90" rx="32" ry="38" fill="hsl({h1}, 25%, 45%)" stroke="hsl({h1}, 30%, 65%)" stroke-width="1.5"/>
      
      <!-- Hair Silhouette -->
      <path d="M 64 92 C 60 55 80 42 100 42 C 125 42 142 55 136 92 C 130 70 120 58 100 58 C 80 58 70 70 64 92 Z" fill="hsl({h2}, 45%, 12%)" stroke="{accent}" stroke-width="1"/>
      
      <!-- Eyes with signature glow -->
      <ellipse cx="88" cy="88" rx="5" ry="3" fill="hsl({h1}, 20%, 90%)"/>
      <circle cx="88" cy="88" r="2.5" fill="{accent}" filter="url(#glow_{seed})"/>
      <ellipse cx="112" cy="88" rx="5" ry="3" fill="hsl({h1}, 20%, 90%)"/>
      <circle cx="112" cy="88" r="2.5" fill="{accent}" filter="url(#glow_{seed})"/>
      
      <!-- Distinguishing Feature / Brand Mark -->
      <path d="M 97 70 L 103 76 L 97 82" stroke="{accent}" stroke-width="1.5" fill="none" opacity="0.8"/>
      
      <!-- Title Badge at bottom -->
      <rect x="15" y="165" width="170" height="26" rx="6" fill="#000000" fill-opacity="0.75" stroke="{accent}" stroke-width="1"/>
      <text x="100" y="182" text-anchor="middle" fill="#ffffff" font-family="system-ui, sans-serif" font-size="11" font-weight="600" letter-spacing="1">
        {dna.name.upper()}
      </text>
    </svg>"""
    return svg


def generate_svg_scene(
    scene_title: str,
    location: str,
    art_style: str,
    characters: List[Optional[CharacterVisualDNA]],
    seed: int
) -> str:
    """
    Procedurally synthesizes a full 16:9 widescreen SVG scene illustration.
    Provides instant, zero-delay rendering with art style colors, silhouettes,
    gothic arches / cyber structures, and character presence.
    """
    style = ART_STYLES.get(art_style, ART_STYLES["Dark Fantasy Graphic Novel"])
    accent = style.get("accent_color", "#d97706")
    secondary = style.get("secondary_color", "#dc2626")
    bg = style.get("bg_color", "#0d0f17")

    valid_chars = [c for c in characters if c is not None]

    # Theme-specific backdrop geometries
    h = (seed * 43) % 360
    
    # Backdrop architecture
    if "cyber" in art_style.lower():
        bg_elements = f"""
          <!-- Cyber City Grid & Megatowers -->
          <line x1="0" y1="420" x2="1024" y2="420" stroke="{accent}" stroke-width="2" opacity="0.6"/>
          <line x1="0" y1="460" x2="1024" y2="460" stroke="{accent}" stroke-width="1.5" opacity="0.4"/>
          <line x1="0" y1="510" x2="1024" y2="510" stroke="{accent}" stroke-width="1" opacity="0.3"/>
          
          <!-- Tower Silhouettes -->
          <rect x="80" y="160" width="110" height="300" fill="#0b1120" stroke="{accent}" stroke-width="1" opacity="0.7"/>
          <rect x="230" y="110" width="160" height="350" fill="#0e172a" stroke="{secondary}" stroke-width="1" opacity="0.8"/>
          <rect x="640" y="90" width="140" height="370" fill="#0e172a" stroke="{accent}" stroke-width="1" opacity="0.8"/>
          <rect x="810" y="180" width="120" height="280" fill="#0b1120" stroke="{secondary}" stroke-width="1" opacity="0.7"/>

          <!-- Neon Hologram glyphs -->
          <circle cx="512" cy="200" r="90" fill="none" stroke="{accent}" stroke-width="2" stroke-dasharray="10 15" opacity="0.5"/>
          <circle cx="512" cy="200" r="70" fill="none" stroke="{secondary}" stroke-width="1.5" stroke-dasharray="6 8" opacity="0.6"/>
        """
    elif "cosmic" in art_style.lower():
        bg_elements = f"""
          <!-- Singularity / Event Horizon Disc -->
          <ellipse cx="512" cy="240" rx="280" ry="80" fill="none" stroke="{accent}" stroke-width="3" opacity="0.7" transform="rotate(-15 512 240)"/>
          <ellipse cx="512" cy="240" rx="200" ry="50" fill="none" stroke="{secondary}" stroke-width="2" opacity="0.9" transform="rotate(-15 512 240)"/>
          <circle cx="512" cy="240" r="45" fill="#000000" stroke="{accent}" stroke-width="4"/>
          
          <!-- Nebula Cloud Layers -->
          <path d="M 0 350 Q 250 180 512 260 T 1024 220 L 1024 576 L 0 576 Z" fill="hsl({h}, 60%, 10%)" opacity="0.6"/>
        """
    else:  # Dark Fantasy / Watercolor / Woodcut
        bg_elements = f"""
          <!-- Gothic Arches & Vaulted Spires -->
          <path d="M 120 450 L 120 220 Q 220 120 320 220 L 320 450 Z" fill="#0f1422" stroke="{accent}" stroke-width="1.5" opacity="0.8"/>
          <path d="M 704 450 L 704 220 Q 804 120 904 220 L 904 450 Z" fill="#0f1422" stroke="{accent}" stroke-width="1.5" opacity="0.8"/>
          
          <!-- Central Celestial Seal / Blood Moon -->
          <circle cx="512" cy="180" r="85" fill="none" stroke="{secondary}" stroke-width="2.5" stroke-dasharray="8 6" opacity="0.6"/>
          <circle cx="512" cy="180" r="70" fill="{secondary}" fill-opacity="0.15" stroke="{accent}" stroke-width="1.5"/>
          
          <!-- Subterranean Flagstones / Catacomb Floor -->
          <path d="M 0 440 Q 512 410 1024 440 L 1024 576 L 0 576 Z" fill="#090d16" stroke="{accent}" stroke-width="1" opacity="0.9"/>
        """

    # Build character silhouettes
    char_svg_parts = []
    positions = [(420, 360), (604, 370), (250, 390)]
    for idx, c in enumerate(valid_chars[:3]):
        cx, cy = positions[idx]
        c_seed = getattr(c, "persistent_seed", 42)
        c_accent = accent if idx == 0 else secondary
        char_svg_parts.append(f"""
          <!-- Character: {c.name} -->
          <g transform="translate({cx - 70}, {cy - 120}) scale(0.7)">
            <!-- Cloak/Armor -->
            <path d="M 30 190 Q 60 110 100 100 Q 140 110 170 190 Z" fill="#060911" stroke="{c_accent}" stroke-width="2"/>
            <!-- Head & glowing gaze -->
            <ellipse cx="100" cy="70" rx="26" ry="32" fill="#141a29" stroke="{c_accent}" stroke-width="1.5"/>
            <circle cx="92" cy="68" r="3" fill="{c_accent}"/>
            <circle cx="108" cy="68" r="3" fill="{c_accent}"/>
            <!-- Name Tag -->
            <rect x="40" y="200" width="120" height="22" rx="4" fill="#000000" fill-opacity="0.8" stroke="{c_accent}" stroke-width="1"/>
            <text x="100" y="215" text-anchor="middle" fill="#ffffff" font-family="system-ui, sans-serif" font-size="11" font-weight="bold">{c.name}</text>
          </g>
        """)

    char_group = "\n".join(char_svg_parts)

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1024 576" width="100%" height="100%">
      <defs>
        <linearGradient id="scene_sky_{seed}" x1="0%" y1="0%" x2="0%" y2="100%">
          <stop offset="0%" stop-color="{bg}"/>
          <stop offset="60%" stop-color="hsl({h}, 40%, 12%)"/>
          <stop offset="100%" stop-color="#05070c"/>
        </linearGradient>
        <radialGradient id="scene_glow_{seed}" cx="50%" cy="35%" r="60%">
          <stop offset="0%" stop-color="{accent}" stop-opacity="0.3"/>
          <stop offset="100%" stop-color="transparent" stop-opacity="0"/>
        </radialGradient>
      </defs>

      <!-- Background Canvas -->
      <rect width="1024" height="576" fill="url(#scene_sky_{seed})"/>
      <rect width="1024" height="576" fill="url(#scene_glow_{seed})"/>

      <!-- Atmospheric Backdrop Geometry -->
      {bg_elements}

      <!-- Character Presences -->
      {char_group}

      <!-- Bottom Scene Information HUD -->
      <rect x="0" y="516" width="1024" height="60" fill="#070a12" fill-opacity="0.9" stroke="{accent}" stroke-width="1" stroke-opacity="0.4"/>
      <circle cx="36" cy="546" r="6" fill="{accent}"/>
      <text x="56" y="542" fill="#ffffff" font-family="'Cinzel', serif, system-ui" font-size="15" font-weight="bold" letter-spacing="0.5">
        {scene_title.upper()}
      </text>
      <text x="56" y="562" fill="{accent}" font-family="system-ui, sans-serif" font-size="11" font-weight="600" letter-spacing="1">
        LOCATION: {location.upper()}
      </text>
      <text x="980" y="552" text-anchor="end" fill="#94a3b8" font-family="'JetBrains Mono', monospace" font-size="11">
        ART: {art_style.upper()} | SEED: #{seed}
      </text>
    </svg>"""
    return svg
