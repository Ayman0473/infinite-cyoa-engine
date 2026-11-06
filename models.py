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
