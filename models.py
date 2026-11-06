"""
Data models and schemas for the Infinite Choose-Your-Own-Adventure Engine.
"""
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field


class Objective(BaseModel):
    id: str = ""
    text: str
    completed: bool = False


class Quest(BaseModel):
    id: str
    title: str
    description: str
    stage: str
    progress_percent: int = 0
    objectives: List[Objective] = []
    status: str = "active"  # active, completed, failed
    reward: Optional[str] = None


class InventoryItem(BaseModel):
    id: str
    name: str
    description: str
    category: str = "misc"  # weapon, armor, artifact, consumable, lore, key_item
    quantity: int = 1
    icon: str = "sparkles"
    usable: bool = True
    effect_hint: Optional[str] = None


class CharacterVisualDNA(BaseModel):
    name: str
    gender_presentation: str = "androgynous"
    face: str = "striking features"
    hair: str = "dark braided hair"
    eyes: str = "piercing amber eyes"
    attire: str = "weathered explorer duster with brass clasps"
    distinguishing_feature: str = "glowing rune brand along right forearm"
    signature_gear: str = "relic compass on silver chain"
    persistent_seed: int = 42
    style_anchor: str = ""


class Character(BaseModel):
    id: str
    name: str
    role: str
    status: str = "Alive"
    affinity: int = 50  # 0 (hostile) to 100 (devoted ally)
    visual_dna: Optional[CharacterVisualDNA] = None
    notes: str = ""
    is_companion: bool = False
    avatar_url: Optional[str] = None


CLASS_ARCHETYPES: Dict[str, Dict[str, Any]] = {
    "Runic Scholar": {
        "id": "runic_scholar",
        "name": "Runic Scholar",
        "icon": "🔮",
        "tagline": "Master of ancient glyphs, ether currents & forbidden lore",
        "advantage": "High Energy (+25) & Deciphers Arcane Sigils",
        "tradeoff": "Lower physical durability (90 HP)",
        "base_health": 90,
        "base_energy": 125,
        "primary_stat": "Wits (16)",
        "stats": {"Might": 8, "Wits": 16, "Agility": 11, "Presence": 12},
        "condition": "Arcane Insight",
        "starter_item": {
            "id": "aether_lens",
            "name": "Aether Focusing Lens",
            "description": "An attuned optical lens that reveals hidden glyphs, leyline currents, and invisible anomalies.",
            "category": "artifact",
            "icon": "gem"
        }
    },
    "Ironclad Warden": {
        "id": "ironclad_warden",
        "name": "Ironclad Warden",
        "icon": "🛡️",
        "tagline": "Unbreakable bulwark against monstrosities & traps",
        "advantage": "High Fortitude (+25 HP) & Heavy Armor Resilience",
        "tradeoff": "Reduced agility and reserve energy (85 Energy)",
        "base_health": 125,
        "base_energy": 85,
        "primary_stat": "Might (16)",
        "stats": {"Might": 16, "Wits": 9, "Agility": 10, "Presence": 12},
        "condition": "Unyielding Stance",
        "starter_item": {
            "id": "tempered_buckler",
            "name": "Tempered Runesteel Buckler",
            "description": "A reinforced shield capable of absorbing devastating direct blows and surviving lethal ambushes.",
            "category": "weapon",
            "icon": "shield"
        }
    },
    "Shadow Stalker": {
        "id": "shadow_stalker",
        "name": "Shadow Stalker",
        "icon": "🗡️",
        "tagline": "Phantom operative of stealth, infiltration & ambush",
        "advantage": "Flawless Infiltration & Critical Strike Evasion",
        "tradeoff": "Vulnerable in open slugfests without cover",
        "base_health": 105,
        "base_energy": 105,
        "primary_stat": "Agility (16)",
        "stats": {"Might": 10, "Wits": 12, "Agility": 16, "Presence": 9},
        "condition": "Silentshadow",
        "starter_item": {
            "id": "shadow_cloak",
            "name": "Shadow-Weave Cloak",
            "description": "A light-absorbing mantle that bends peripheral vision, muffles footsteps, and slips warded gates.",
            "category": "artifact",
            "icon": "scroll"
        }
    },
    "Silver-Tongue Envoy": {
        "id": "silver_tongue_envoy",
        "name": "Silver-Tongue Envoy",
        "icon": "🕊️",
        "tagline": "Master diplomat capable of turning foes into allies",
        "advantage": "+20 Starting NPC Affinity & Persuasion Mastery",
        "tradeoff": "Lower raw martial power in direct assaults",
        "base_health": 100,
        "base_energy": 110,
        "primary_stat": "Presence (16)",
        "stats": {"Might": 9, "Wits": 12, "Agility": 10, "Presence": 16},
        "condition": "Silver-Tongued",
        "starter_item": {
            "id": "guild_signet",
            "name": "Signet of the Free Accord",
            "description": "A recognized diplomatic seal that commands respect, prevents hostilities, and unlocks hidden bargains.",
            "category": "key_item",
            "icon": "spark"
        }
    },
    "Alchemical Medic": {
        "id": "alchemical_medic",
        "name": "Alchemical Medic",
        "icon": "🧪",
        "tagline": "Field apothecary and resourceful survival scavenger",
        "advantage": "Consumables 50% More Potent & Emergency Remedy",
        "tradeoff": "Requires reagent preparation and clever positioning",
        "base_health": 110,
        "base_energy": 100,
        "primary_stat": "Wits/Survival (14)",
        "stats": {"Might": 11, "Wits": 14, "Agility": 11, "Presence": 11},
        "condition": "Field Alchemist",
        "starter_item": {
            "id": "panacea_elixir",
            "name": "Vial of Pure Panacea",
            "description": "A masterwork curative draught that heals 50 HP and cures all negative status conditions.",
            "category": "consumable",
            "icon": "potion"
        }
    }
}


class Choice(BaseModel):
    id: str
    text: str
    tag: str = "Action"  # e.g., Combat, Arcana, Stealth, Dialogue, Danger, Item
    risk: str = "medium"  # low, medium, high, lethal


class PlayerStatus(BaseModel):
    name: str = "Traveler"
    archetype: str = "Arcane Wanderer"
    health: int = 100
    max_health: int = 100
    energy: int = 100
    max_energy: int = 100
    conditions: List[str] = []
    stats: Dict[str, int] = {"Might": 12, "Wits": 14, "Agility": 13, "Presence": 11}
    visual_dna: Optional[CharacterVisualDNA] = None


class StoryNode(BaseModel):
    turn: int
    scene_title: str
    location: str
    narrative: str
    choice_taken: Optional[str] = None
    image_url: Optional[str] = None
    image_prompt: Optional[str] = None
    image_seed: Optional[int] = None


class GameState(BaseModel):
    session_id: str
    theme: str = "Eldritch Dark Fantasy"
    art_style: str = "Dark Fantasy Graphic Novel"
    player: PlayerStatus = Field(default_factory=PlayerStatus)
    current_quest: Optional[Quest] = None
    quest_log: List[Quest] = []
    inventory: List[InventoryItem] = []
    characters: List[Character] = []
    history: List[StoryNode] = []
    current_turn: int = 0
    world_flags: Dict[str, Any] = {}
    last_scene_title: str = ""
    last_location: str = ""
    last_narrative: str = ""
    available_choices: List[Choice] = []
    current_image_url: Optional[str] = None
    current_image_prompt: Optional[str] = None
    current_image_seed: Optional[int] = None


class NewGameRequest(BaseModel):
    theme: str = "Eldritch Dark Fantasy"  # or Cyberpunk Noir, Cosmic Void, Sunken Seas, Custom
    custom_theme: Optional[str] = None
    art_style: str = "Dark Fantasy Graphic Novel"  # or Cyberpunk Synthwave, Watercolor Fantasy, Studio Anime, Eldritch Woodcut
    player_name: str = "Kaelen"
    player_archetype: str = "Runic Scholar"
    custom_premise: Optional[str] = None
    api_key: Optional[str] = None  # Optional Gemini / OpenAI API key


class TurnActionRequest(BaseModel):
    session_id: str
    choice_id: Optional[str] = None
    custom_action: Optional[str] = None
    use_item_id: Optional[str] = None
    api_key: Optional[str] = None


class TurnActionResponse(BaseModel):
    session_id: str
    turn: int
    scene_title: str
    location: str
    narrative: str
    image_url: str
    image_prompt: str
    image_seed: int
    choices: List[Choice]
    quest_update: Optional[Quest] = None
    inventory_delta: Dict[str, Any] = {}
    character_updates: List[Character] = []
    player_status: PlayerStatus
    full_state: GameState
