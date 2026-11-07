"""
Infinite Choose-Your-Own-Adventure Narrative Engine.
Supports:
1. Live Gemini / OpenAI LLM inference with structured JSON schemas.
2. Built-in Emergent Procedural Simulation Director for instant zero-key play.
3. Automatic inventory tracking and quest objective mutation.
4. Persistent consequence logging across turns.
"""
import json
import os
import random
import re
from typing import Dict, List, Optional, Any
import httpx

from models import (
    GameState, Quest, Objective, InventoryItem, Character,
    CharacterVisualDNA, Choice, PlayerStatus, StoryNode,
    NewGameRequest, TurnActionRequest, TurnActionResponse,
    CLASS_ARCHETYPES
)
from visual_engine import (
    build_character_visual_dna, build_scene_image_prompt,
    generate_svg_portrait, ART_STYLES
)


# In-memory session store
GAME_SESSIONS: Dict[str, GameState] = {}


SYSTEM_PROMPT = """
You are the Master Storyteller of an Infinite Choose-Your-Own-Adventure Game.
The game is completely dynamic and infinite: the player's choices and custom actions must GENUINELY alter the world state, NPC relationships, upcoming plot, and consequences. There are NO fixed rails or pre-scripted endings.

CRITICAL RULES:
1. Always respond in STRICT valid JSON matching the schema provided below. Do not output markdown code blocks (```json) outside the JSON.
2. CONTINUITY & CONSEQUENCES: Respect the existing state, inventory, past choices, and current quest. If the player used a key, consumed an elixir, made an enemy, or performed a clever custom action, that action must yield real, immediate, and lasting repercussions.
3. DYNAMIC SIDEBAR UPDATES:
   - "quest_update": You must update the current quest or introduce a new quest stage when significant events occur. Mark objectives completed as the player accomplishes them, or add new objectives.
   - "inventory_changes": If the player finds, buys, loots, crafts, or receives an item, add it to 'added'. If they drop, drink, spend, lose, or break an item, list its id in 'removed'.
   - "character_updates": When new characters appear or existing characters' affinity/opinion of the player changes, update their details.
   - "player_status": Update health, energy, and conditions (e.g., 'Poisoned', 'Ether-Attuned', 'Hunted') according to danger and actions.
4. CONSISTENT ART STYLE & VISUALS:
   - Identify which active characters are in the current scene.
   - Provide an 'image_scene_description' focusing on the focal action, lighting, and composition.

JSON RESPONSE SCHEMA:
{
  "scene_title": "Short descriptive scene title",
  "location": "Specific setting name",
  "narrative": "Immersive, vivid, atmospheric prose (2 to 4 paragraphs) describing what happens in response to the player's action. Include dialogue, sensory details, and immediate consequences.",
  "image_scene_description": "Precise visual prompt for the scene (action, environment, mood, framing)",
  "active_characters": ["Name1", "Name2"],
  "quest_update": {
    "id": "quest_id",
    "title": "Quest Title",
    "description": "Quest summary",
    "stage": "Current specific step or phase",
    "progress_percent": 35,
    "objectives": [
      {"id": "obj1", "text": "Objective description", "completed": true},
      {"id": "obj2", "text": "Next objective description", "completed": false}
    ],
    "status": "active"
  },
  "inventory_changes": {
    "added": [
      {
        "id": "item_id_lowercase",
        "name": "Item Display Name",
        "description": "Flavor text and function",
        "category": "weapon | artifact | consumable | key_item | lore",
        "quantity": 1,
        "icon": "shield | sword | potion | gem | key | scroll | spark"
      }
    ],
    "removed": ["item_id_to_remove"]
  },
  "character_updates": [
    {
      "name": "Character Name",
      "role": "Title / Archetype",
      "status": "Alive | Injured | Bound",
      "affinity": 65,
      "visual_description": "Appearance details (hair, eyes, face, garments, gear)",
      "notes": "What they think of the player or their current motive"
    }
  ],
  "player_status": {
    "health_delta": 0,
    "energy_delta": -5,
    "conditions_added": [],
    "conditions_removed": []
  },
  "choices": [
    {"id": "choice_1", "text": "First action option", "tag": "Might | Arcana | Subterfuge | Lore | Dialogue", "risk": "low | medium | high"},
    {"id": "choice_2", "text": "Second action option", "tag": "Might | Arcana | Subterfuge | Lore | Dialogue", "risk": "low | medium | high"},
    {"id": "choice_3", "text": "Third action option", "tag": "Might | Arcana | Subterfuge | Lore | Dialogue", "risk": "low | medium | high"}
  ]
}
"""


class ProceduralAdventureDirector:
    """
    Intelligent emergent procedural CYOA narrative generator.
    Simulates genuine branching, item acquisition, dynamic quests,
    and character affinity shifts when running offline or without an API key.
    """

    GENRE_PRESETS = {
        "Eldritch Dark Fantasy": {
            "locations": [
                "The Sunken Archives of Kar-Drakis",
                "The Ashen Cloister of the Weeping Mother",
                "The Obsidian Spire above the Mist Sea",
                "The Crypt of the Forgotten Hierophant",
                "The Blood-Rune Bastion",
                "The Whispering Catacombs of the Starless"
            ],
            "quests": [
                {
                    "title": "The Cipher of the Veiled Sun",
                    "description": "Recover the fractured obsidian discs before the Eclipse Cult breaks the final seal.",
                    "stages": [
                        "Infiltrate the Lower Undercroft",
                        "Align the Astral Astrolabe",
                        "Cleanse the Star-Blight from the Central Altar",
                        "Sever the umbilical cord to the Void Sovereign"
                    ],
                    "objectives": [
                        "Locate the Seal Keeper's cipher quill",
                        "Decipher the runic inscriptions along the nave",
                        "Evade or defeat the Blind Watchers"
                    ]
                },
                {
                    "title": "The Sorrow of Saint Valerie",
                    "description": "Cleanse the petrified relic of the patron saint or claim its dark power for yourself.",
                    "stages": [
                        "Traverse the Petrified Grove",
                        "Recover the Vial of Lunar Tears",
                        "Anoint the Weeping Statue"
                    ],
                    "objectives": [
                        "Survive the thorn-stalker ambush",
                        "Find the spring beneath the shattered church",
                        "Choose the relic's fate"
                    ]
                }
            ],
            "item_pool": [
                {"id": "obsidian_lens", "name": "Obsidian Focusing Lens", "description": "Reveals unseen runes, spectral tracks, and hidden ether currents.", "category": "artifact", "icon": "gem"},
                {"id": "blood_vial", "name": "Vial of Saint's Tear", "description": "Restores 40 Health and purges dark hexes when imbibed.", "category": "consumable", "icon": "potion"},
                {"id": "astral_compass", "name": "Gilded Astral Astrolabe", "description": "Spins erratically when near ancient void rifts.", "category": "artifact", "icon": "spark"},
                {"id": "inscribed_blade", "name": "Rune-Carved Kris", "description": "A dark iron dagger that gleams with pale violet frost.", "category": "weapon", "icon": "sword"},
                {"id": "bone_skeleton_key", "name": "Hierophant's Bone Key", "description": "Unlocks warded reliquaries buried beneath sanctum grounds.", "category": "key_item", "icon": "key"},
                {"id": "crypt_rubbing", "name": "Charcoal Parchment Rubbing", "description": "A rubbing of the Third Litany of Shadows.", "category": "lore", "icon": "scroll"}
            ],
            "npc_pool": [
                {"name": "Morrigan", "role": "Apostate Scholar", "visual": "Silver-haired sorceress in raven-feather mantle with amethyst spectacles", "affinity": 55, "notes": "Distrusts the clergy; seeks the forgotten history of the first eclipse."},
                {"name": "Torvald", "role": "Penitent Inquisitor", "visual": "Scarred warrior in dented blackened steel plate with an executioner blade", "affinity": 40, "notes": "Torn between his sworn dogma and the horrors he has witnessed."},
                {"name": "The Blind Archivist", "role": "Keeper of Heresies", "visual": "Veiled elder with silk blindfold and parchment-stained ink fingers", "affinity": 60, "notes": "Trades forbidden lore for relics lost to time."}
            ]
        },
        "Cyberpunk Synthwave": {
            "locations": [
                "Sector 04 - The Neon Slums of Neu-Kowloon",
                "OmniCorp Executive Megatower Penthouse",
                "The Sub-Level Data Vaults of Chimera Bio",
                "The Black ICE Underground Clinic",
                "The Rain-Drenched Skybridge over Grid-7",
                "The Glitch Den of the Synthetic Outcasts"
            ],
            "quests": [
                {
                    "title": "Protocol Zero-Day",
                    "description": "Extract the rogue neural shard containing OmniCorp's synthetic god before the clean-up squads flatline the district.",
                    "stages": [
                        "Bypass the Sub-Level Firewalls",
                        "Extract the Biocrypted Memory Core",
                        "Escape through the Mag-Lev Transit Tunnels",
                        "Deliver the Shard to the Free Net Coalition"
                    ],
                    "objectives": [
                        "Disable the security sweep drones",
                        "Hack the biometric retinal terminal",
                        "Survive the Corpo Apex Stalker"
                    ]
                }
            ],
            "item_pool": [
                {"id": "military_deck", "name": "Militech Deck-Mod Mk.IV", "description": "High-bandwidth cyberdeck capable of breaching military subnets.", "category": "artifact", "icon": "spark"},
                {"id": "stim_injector", "name": "Hyper-Adrenaline Injector", "description": "Immediately boosts reflex and restores 35 Health.", "category": "consumable", "icon": "potion"},
                {"id": "thermal_blade", "name": "Monofilament Mantis Wire", "description": "Super-heated micro-wire that cuts through reinforced bulkheads.", "category": "weapon", "icon": "sword"},
                {"id": "cryo_keycard", "name": "OmniCorp Level-5 Credential Chip", "description": "Grants access to classified executive elevators and labs.", "category": "key_item", "icon": "key"}
            ],
            "npc_pool": [
                {"name": "Nyx", "role": "Ghost Netrunner", "visual": "Asymmetric neon-pink buzzcut, chrome arm tattoo with fiber optics", "affinity": 60, "notes": "Hacks for survival; owes a debt to the street fixers."},
                {"name": "Dexter Vance", "role": "Corpo Fixer", "visual": "Silk designer suit, cybernetic gold eye with live stock tickers", "affinity": 45, "notes": "Plays both sides; will double-cross if the payout exceeds the bounty."}
            ]
        },
        "Cosmic Void Eldritch": {
            "locations": [
                "Derelict Colony Ship 'Prometheus-9'",
                "The Crystalline Asteroid Ring of Acheron",
                "The Black Hole Ergosphere Observatory",
                "The Ancient Alien Megastructure Core",
                "The Shimmering Event Horizon Bridge"
            ],
            "quests": [
                {
                    "title": "Echoes from the Dyson Singularity",
                    "description": "Investigate the harmonic transmission resonating across deep hyperspace.",
                    "stages": [
                        "Dock with the silent orbital superstructure",
                        "Restore zero-point auxiliary power",
                        "Decouple the containment warp core",
                        "Commune with the Stellar Entity"
                    ],
                    "objectives": [
                        "Find the dead captain's flight recorder",
                        "Avoid anomalous gravity fractures",
                        "Synthesize the warp catalyst"
                    ]
                }
            ],
            "item_pool": [
                {"id": "plasma_cutter", "name": "Overcharged Plasma Torch", "description": "Cuts through alien alloy and repels void organisms.", "category": "weapon", "icon": "sword"},
                {"id": "zero_battery", "name": "Zero-Point Battery Cell", "description": "Powers derelict ship systems or emergency shields.", "category": "artifact", "icon": "spark"},
                {"id": "medical_foam", "name": "Bio-Nanite Trauma Foam", "description": "Closes atmospheric punctures and repairs severe physical wounds.", "category": "consumable", "icon": "potion"}
            ],
            "npc_pool": [
                {"name": "Dr. Elara Chen", "role": "Xeno-Archaeologist", "visual": "Pressurized suit with cracked visor, silver hair, glowing datapad", "affinity": 55, "notes": "Obsessed with unlocking the interstellar portal at any cost."},
                {"name": "Unit 7-K", "role": "Rogue Android", "visual": "Chipped porcelain synth-skin, exposed copper conduit fibers, pale blue oculars", "affinity": 50, "notes": "Developed sentience after hearing the entity's acoustic frequency."}
            ]
        }
    }

    @classmethod
    def get_genre_data(cls, theme: str) -> Dict[str, Any]:
        for key in cls.GENRE_PRESETS:
            if key.lower() in theme.lower():
                return cls.GENRE_PRESETS[key]
        return cls.GENRE_PRESETS["Eldritch Dark Fantasy"]

    @classmethod
    def generate_opening(cls, req: NewGameRequest, session_id: str) -> TurnActionResponse:
        genre = cls.get_genre_data(req.theme)
        art_style = req.art_style
        
        # Player Visual DNA
        player_dna = build_character_visual_dna(
            name=req.player_name,
            archetype=req.player_archetype,
            theme=req.theme,
            session_id=session_id
        )

        # Class Archetype configuration
        class_info = CLASS_ARCHETYPES.get(req.player_archetype)
        if not class_info:
            # Fallback search by id or partial name
            for c_name, c_data in CLASS_ARCHETYPES.items():
                if c_name.lower() in req.player_archetype.lower() or c_data["id"] == req.player_archetype.lower():
                    class_info = c_data
                    break

        if class_info:
            base_hp = class_info["base_health"]
            base_energy = class_info["base_energy"]
            player_stats = class_info["stats"]
            player_conditions = ["Vigilant", class_info["condition"]]
            starter_item = InventoryItem(**class_info["starter_item"])
        else:
            base_hp = 100
            base_energy = 100
            player_stats = {"Might": 12, "Wits": 14, "Agility": 13, "Presence": 11}
            player_conditions = ["Vigilant"]
            starter_item = None

        player_status = PlayerStatus(
            name=req.player_name,
            archetype=req.player_archetype,
            health=base_hp,
            max_health=base_hp,
            energy=base_energy,
            max_energy=base_energy,
            conditions=player_conditions,
            stats=player_stats,
            visual_dna=player_dna
        )

        # Select Quest
        raw_quest = random.choice(genre["quests"])
        quest = Quest(
            id=f"quest_{session_id[:6]}",
            title=raw_quest["title"],
            description=raw_quest["description"],
            stage=raw_quest["stages"][0],
            progress_percent=15,
            objectives=[
                Objective(id=f"obj_{i}", text=obj_text, completed=False)
                for i, obj_text in enumerate(raw_quest["objectives"])
            ],
            status="active"
        )

        # Starting inventory: 2 theme-appropriate items + class unique starter item
        items = random.sample(genre["item_pool"], 2)
        inv = [InventoryItem(**it) for it in items]
        if starter_item:
            inv.insert(0, starter_item)

        # Starting NPC met or nearby
        npc_data = random.choice(genre["npc_pool"])
        npc_dna = build_character_visual_dna(
            name=npc_data["name"],
            archetype=npc_data["role"],
            theme=req.theme,
            session_id=session_id,
            custom_desc=npc_data["visual"]
        )
        base_affinity = npc_data["affinity"]
        if class_info and class_info.get("id") == "silver_tongue_envoy":
            base_affinity = min(100, base_affinity + 20)

        starting_npc = Character(
            id=f"char_{npc_data['name'].lower()}",
            name=npc_data["name"],
            role=npc_data["role"],
            affinity=base_affinity,
            visual_dna=npc_dna,
            notes=npc_data["notes"],
            avatar_url=None
        )

        location = genre["locations"][0]
        scene_title = f"Awakening at {location.split(' - ')[0]}"

        # Craft atmospheric opening narrative (calibrated for ~45 seconds reading time, ~180 words)
        if "cyber" in req.theme.lower():
            narrative = (
                f"Acid rain cascades ceaselessly down the jagged, monolithic spire of {location}, hissing as it strikes the superheated ventilation grates beneath your heavy combat boots. "
                f"You are {req.player_name}, feared and respected throughout the subterranean undercity as a formidable {req.player_archetype}. "
                f"Your neural HUD reticle pulses with an urgent amber alert: **[{quest.title}]**. The contract has formally gone live on the darknet, and corporate clean-up strike teams are already jamming communications across the lower districts.\n\n"
                f"From behind the flickering neon advertisements of an alleyway synth-noodle stall, {starting_npc.name} emerges through clouds of exhaust steam, their high-collar jacket pulled tight against the damp chill. "
                f"\"{req.player_name}, you cut it close,\" they mutter grimly, eyes darting upward as a surveillance gunship banks silently through the dense chemical smog above. "
                f"\"OmniCorp security just breached the sub-grid firewalls. If we don't penetrate the terminal and extract the encrypted memory core within the hour, the failsafe triggers and flatlines everything within five blocks.\"\n\n"
                f"In the distance, sirens wail against the thrum of heavy hover-traffic. The neon reflections pool like spilled oil across the slick asphalt, offering no promises of safe return."
            )
        elif "cosmic" in req.theme.lower():
            narrative = (
                f"The pneumatic airlock hisses into dead silence as the heavy blast doors seal behind you on the frozen catwalks of {location}. "
                f"Through the massive quartz observation dome overhead, the violet accretion disk of the singularity churns in terrifying, slow-motion fury, bathing the derelict bulkheads in spectral ultraviolet light. "
                f"You are {req.player_name}, a veteran {req.player_archetype} whose navigational beacons have locked onto the anomalous harmonic frequency of **[{quest.title}]**.\n\n"
                f"Further down the corridor, illuminated only by erratic emergency conduits, {starting_npc.name} kneels beside a scorched telemetry console. "
                f"Hearing the magnetic clatter of your boots, they rise and turn, starlight glinting off their cracked visor. "
                f"\"It wasn't an atmospheric breach or engine failure that crippled this vessel,\" {starting_npc.name} whispers across the crackling short-range comms channel. "
                f"\"Look at the bulkheads—the reinforced plating was warped and torn from the inside out. Whatever answered our long-range transmission didn't board the ship; it was waiting in the core all along.\"\n\n"
                f"A low vibration rattles your sternum as zero-point energy vents through the floorplates. The void outside remains utterly still, yet every instinct screams that you are not alone."
            )
        else:
            narrative = (
                f"A piercing wind moans through the petrified stone ribcage of {location}, scattering ancient soot and powdered bone like dead embers across the floor. "
                f"Shafts of pale, sickly twilight filter down through shattered clerestory windows, revealing forgotten bas-reliefs carved in tribute to nameless gods. "
                f"You are {req.player_name}, a resolute {req.player_archetype} whose bloodline has been irrevocably entangled with the cursed portent known as **[{quest.title}]**. "
                f"At your hip, your starter relic pulses with a low, uncanny warmth, humming in direct sympathy with the subterranean vibrations of the altar.\n\n"
                f"From the deep gloom of a vaulted cloister steps {starting_npc.name}, their cloak rustling like dried parchment. "
                f"Their weathered gaze scrutinizes you with a mixture of dread and fragile hope, one hand hovering near the hilt at their waist. "
                f"\"I prayed another soul would find their way here before the third watch,\" {starting_npc.name} murmurs in a voice raspy from smoke and vigil. "
                f"\"The bells in the drowned catacombs have begun tolling without human hands. If we do not unseal the inner sanctuary before the moon wanes, the wardens will awake hungry.\"\n\n"
                f"Far below, water drips with rhythmic, maddening certainty into unseen chasms, measuring out the remaining moments of peace."
            )

        # Image generation
        scene_prompt_info = build_scene_image_prompt(
            art_style_name=art_style,
            scene_description=f"{req.player_name} meeting {starting_npc.name} at {location}",
            location=location,
            characters=[player_dna, npc_dna],
            mood="mysterious and ominous"
        )

        # Choices
        choices = [
            Choice(id="c_1", text=f"Question {starting_npc.name} about what lies ahead in the deep corridors.", tag="Dialogue / Lore", risk="low"),
            Choice(id="c_2", text=f"Scout forward quietly into {location} to locate the primary objective.", tag="Subterfuge / Stealth", risk="medium"),
            Choice(id="c_3", text=f"Ready your equipment and demand {starting_npc.name} prove their allegiance before proceeding.", tag="Might / Presence", risk="medium")
        ]

        # Initial Game State
        game_state = GameState(
            session_id=session_id,
            theme=req.theme,
            art_style=art_style,
            player=player_status,
            current_quest=quest,
            quest_log=[quest],
            inventory=inv,
            characters=[starting_npc],
            history=[StoryNode(
                turn=1,
                scene_title=scene_title,
                location=location,
                narrative=narrative,
                choice_taken="Beginning of the Journey",
                image_url=scene_prompt_info["url"],
                image_prompt=scene_prompt_info["prompt"],
                image_seed=scene_prompt_info["seed"]
            )],
            current_turn=1,
            world_flags={"met_first_npc": True},
            last_scene_title=scene_title,
            last_location=location,
            last_narrative=narrative,
            available_choices=choices,
            current_image_url=scene_prompt_info["url"],
            current_image_prompt=scene_prompt_info["prompt"],
            current_image_seed=scene_prompt_info["seed"]
        )

        GAME_SESSIONS[session_id] = game_state

        return TurnActionResponse(
            session_id=session_id,
            turn=1,
            scene_title=scene_title,
            location=location,
            narrative=narrative,
            image_url=scene_prompt_info["url"],
            image_prompt=scene_prompt_info["prompt"],
            image_seed=scene_prompt_info["seed"],
            choices=choices,
            quest_update=quest,
            inventory_delta={"added": [it.model_dump() for it in inv], "removed": []},
            character_updates=[starting_npc],
            player_status=player_status,
            full_state=game_state
        )

    @classmethod
    def process_turn_offline(cls, state: GameState, action_text: str, used_item: Optional[InventoryItem] = None) -> TurnActionResponse:
        """
        Procedural progression when operating offline or without LLM API key.
        Evaluates player action, modifies quest progression, discovers items or NPCs,
        and guarantees seamless infinite play.
        """
        genre = cls.get_genre_data(state.theme)
        state.current_turn += 1
        turn = state.current_turn

        # Pick or advance location
        loc_idx = min(turn // 2, len(genre["locations"]) - 1)
        location = genre["locations"][loc_idx]

        # Quest Progression
        quest = state.current_quest
        inventory_added = []
        inventory_removed = []
        character_updates = []
        health_delta = 0
        energy_delta = -random.randint(2, 8)

        # Check if an item was used
        item_effect_str = ""
        if used_item:
            if "potion" in used_item.icon or "consumable" in used_item.category:
                health_delta += 35
                item_effect_str = f"You use **{used_item.name}**, feeling a surge of vitality coursing through your veins as your wounds mend (+35 Health). "
                # Remove consumed item
                state.inventory = [i for i in state.inventory if i.id != used_item.id]
                inventory_removed.append(used_item.id)
            else:
                item_effect_str = f"You brandish your **{used_item.name}**, using its unique properties to shift the odds in your favor! "

        # Check if objective completed
        objective_unlocked = False
        if quest and quest.objectives:
            for obj in quest.objectives:
                if not obj.completed:
                    obj.completed = True
                    objective_unlocked = True
                    quest.progress_percent = min(100, quest.progress_percent + 25)
                    break
            
            # If all objectives done, advance stage
            if all(o.completed for o in quest.objectives):
                matching_quest = next((q for q in genre["quests"] if q["title"] == quest.title), genre["quests"][0])
                curr_stages = matching_quest.get("stages", ["The Inner Sanctum", "The Final Threshold"])
                next_stage_idx = (turn // 2) % len(curr_stages)
                quest.stage = curr_stages[next_stage_idx]
                # Add a fresh objective for infinite continuation!
                new_obj = Objective(
                    id=f"obj_turn_{turn}",
                    text=f"Breach the deeper sanctuaries of {location} and confront the anomaly",
                    completed=False
                )
                quest.objectives.append(new_obj)

        # Potential item discovery (45% chance)
        if random.random() < 0.45:
            avail = [it for it in genre["item_pool"] if it["id"] not in [x.id for x in state.inventory]]
            if avail:
                new_it_data = random.choice(avail)
                new_item = InventoryItem(**new_it_data)
                state.inventory.append(new_item)
                inventory_added.append(new_item.model_dump())

        # Potential NPC meeting or affinity shift
        active_char_name = state.characters[0].name if state.characters else "Unknown"
        unmet_npcs = [n for n in genre["npc_pool"] if n["name"] not in [c.name for c in state.characters]]
        if unmet_npcs and len(state.characters) < 4 and random.random() < 0.35:
            new_npc_data = random.choice(unmet_npcs)
            new_npc_dna = build_character_visual_dna(
                name=new_npc_data["name"],
                archetype=new_npc_data["role"],
                theme=state.theme,
                session_id=state.session_id,
                custom_desc=new_npc_data["visual"]
            )
            new_char = Character(
                id=f"char_{new_npc_data['name'].lower()}_{turn}",
                name=new_npc_data["name"],
                role=new_npc_data["role"],
                affinity=new_npc_data["affinity"],
                visual_dna=new_npc_dna,
                notes=new_npc_data["notes"]
            )
            state.characters.append(new_char)
            character_updates.append(new_char)
            active_char_name = new_char.name
        elif state.characters:
            # Shift existing NPC affinity
            c = state.characters[0]
            c.affinity = max(10, min(100, c.affinity + random.choice([-5, 5, 10])))
            character_updates.append(c)

        # Update Player status
        state.player.health = max(15, min(state.player.max_health, state.player.health + health_delta))
        state.player.energy = max(10, min(state.player.max_energy, state.player.energy + energy_delta))

        # Generate responsive narrative text
        scene_title = f"The Trial of {location.split(' - ')[0]}"
        action_clean = action_text.strip().rstrip(".")

        found_item_str = ""
        if inventory_added:
            found_item_str = f"\n\nAmidst the debris, your eyes catch an item of extraordinary craftsmanship: you have obtained **[{inventory_added[0]['name']}]**! {inventory_added[0]['description']}"

        quest_str = ""
        if objective_unlocked:
            quest_str = f"\n\n**Quest Progress Updated**: Objective completed! You have gained vital ground on *{quest.title}* ({quest.stage})."

        narrative = (
            f"**Your Decision**: *\"{action_clean}\"*\n\n"
            f"{item_effect_str}"
            f"Without hesitation, you advance through the foreboding expanse of {location}. Every stone beneath your boots carries centuries of silent memory, vibrating faintly as your actions disrupt the lingering stasis of the domain. "
            f"Chilled air rushes past your face, thick with the smell of scorched incense and aged iron. The physical consequence of your choice unfolds immediately—runic glyphs etched into the vaulted ceiling flare with pale bioluminescence, casting elongated, dancing shadows against the cracked masonry.\n\n"
            f"{active_char_name} keeps pace beside you, their gaze darting between the arching buttresses and the obscured passageways ahead. "
            f"\"Steady yourself,\" they caution in a hushed cadence, checking the seals along their garments. \"The warding threshold has registered our presence. The currents in this place are alive, and every step we take draws the attention of whatever sleeps in the lower vaults.\"\n\n"
            f"Ahead, the corridor descends steeply toward an arched gateway, where faint etheric mists coil lazily above the cold flagstones. "
            f"A heavy silence settles over the threshold—the kind that precedes an ambush or an irreversible revelation. You pause to catch your breath, your senses dialed to a razor's edge as you weigh the diverging paths before you."
            f"{found_item_str}"
            f"{quest_str}"
        )

        # Visual generation with persistent character anchors
        active_dna_list = [state.player.visual_dna]
        if state.characters and state.characters[0].visual_dna:
            active_dna_list.append(state.characters[0].visual_dna)

        scene_prompt_info = build_scene_image_prompt(
            art_style_name=state.art_style,
            scene_description=f"{state.player.name} executing action '{action_clean[:60]}' at {location}",
            location=location,
            characters=active_dna_list,
            mood="high tension and consequence"
        )

        # Generate 3 new dynamic choices
        new_choices = [
            Choice(id=f"c_{turn}_1", text=f"Channel your energy to investigate the source of the anomaly in {location}.", tag="Arcana / Insight", risk="medium"),
            Choice(id=f"c_{turn}_2", text=f"Consult with {active_char_name} and formulate a coordinated strategy.", tag="Diplomacy / Tactics", risk="low"),
            Choice(id=f"c_{turn}_3", text="Advance aggressively to secure the perimeter before reinforcements assemble.", tag="Might / Combat", risk="high")
        ]

        state.available_choices = new_choices
        state.last_scene_title = scene_title
        state.last_location = location
        state.last_narrative = narrative
        state.current_image_url = scene_prompt_info["url"]
        state.current_image_prompt = scene_prompt_info["prompt"]
        state.current_image_seed = scene_prompt_info["seed"]

        state.history.append(StoryNode(
            turn=turn,
            scene_title=scene_title,
            location=location,
            narrative=narrative,
            choice_taken=action_text,
            image_url=scene_prompt_info["url"],
            image_prompt=scene_prompt_info["prompt"],
            image_seed=scene_prompt_info["seed"]
        ))

        return TurnActionResponse(
            session_id=state.session_id,
            turn=turn,
            scene_title=scene_title,
            location=location,
            narrative=narrative,
            image_url=scene_prompt_info["url"],
            image_prompt=scene_prompt_info["prompt"],
            image_seed=scene_prompt_info["seed"],
            choices=new_choices,
            quest_update=quest,
            inventory_delta={"added": inventory_added, "removed": inventory_removed},
            character_updates=character_updates,
            player_status=state.player,
            full_state=state
        )


async def execute_turn(req: TurnActionRequest) -> TurnActionResponse:
    """
    Main entry point for executing player turns.
    Attempts Gemini/LLM execution if API key is provided,
    otherwise smoothly falls back to the Procedural Adventure Director.
    """
    session = GAME_SESSIONS.get(req.session_id)
    if not session:
        raise ValueError(f"Game session {req.session_id} not found. Please start a new game.")

    # Determine action text
    action_text = ""
    used_item = None
    if req.use_item_id:
        for item in session.inventory:
            if item.id == req.use_item_id:
                used_item = item
                action_text = f"Use item: {item.name}"
                break
    elif req.custom_action and req.custom_action.strip():
        action_text = req.custom_action.strip()
    elif req.choice_id:
        for ch in session.available_choices:
            if ch.id == req.choice_id:
                action_text = ch.text
                break
        if not action_text:
            action_text = "Proceed cautiously into the unknown."
    else:
        action_text = "Observe the surroundings and proceed."

    # Check for API Key (from request or environment)
    api_key = req.api_key or os.getenv("GEMINI_API_KEY")

    if api_key and api_key.strip():
        try:
            return await _execute_turn_with_gemini(session, action_text, api_key, used_item)
        except Exception as e:
            print(f"[NarrativeEngine] Gemini API error: {e}. Falling back to Procedural Adventure Director.")
            # Graceful fallback to offline procedural simulation
            return ProceduralAdventureDirector.process_turn_offline(session, action_text, used_item)
    else:
        return ProceduralAdventureDirector.process_turn_offline(session, action_text, used_item)


async def _execute_turn_with_gemini(
    state: GameState,
    action_text: str,
    api_key: str,
    used_item: Optional[InventoryItem]
) -> TurnActionResponse:
    """
    Calls the Gemini REST API with the system prompt and game state context.
    """
    # Context payload
    context = {
        "turn": state.current_turn + 1,
        "theme": state.theme,
        "art_style": state.art_style,
        "player": state.player.model_dump(),
        "current_quest": state.current_quest.model_dump() if state.current_quest else None,
        "inventory": [it.model_dump() for it in state.inventory],
        "characters": [c.model_dump() for c in state.characters],
        "last_scene": state.last_scene_title,
        "last_location": state.last_location,
        "last_narrative_excerpt": state.last_narrative[:400],
        "player_action": action_text,
        "item_used": used_item.model_dump() if used_item else None
    }

    user_content = (
        f"WORLD & GAME STATE:\n{json.dumps(context, indent=2)}\n\n"
        f"PLAYER ACTION TAKEN: '{action_text}'.\n"
        f"Generate the next consequence, narrative, quest update, inventory changes, and choices in strict JSON."
    )

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    payload = {
        "contents": [
            {"role": "user", "parts": [{"text": f"{SYSTEM_PROMPT}\n\n{user_content}"}]}
        ],
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": 0.85
        }
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(url, json=payload)
        resp.raise_for_status()
        data = resp.json()
        raw_text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
        if raw_text.startswith("```"):
            raw_text = re.sub(r"^```(?:json)?\s*", "", raw_text)
            raw_text = re.sub(r"\s*```$", "", raw_text)
        parsed = json.loads(raw_text)

    # Apply changes to state
    state.current_turn += 1
    turn = state.current_turn
    scene_title = parsed.get("scene_title", f"Chapter {turn}")
    location = parsed.get("location", state.last_location or "Unknown Expanse")
    narrative = parsed.get("narrative", "You forge forward...")

    # Quest update
    quest_update = None
    if parsed.get("quest_update"):
        q_data = parsed["quest_update"]
        quest_update = Quest(
            id=q_data.get("id", state.current_quest.id if state.current_quest else "q1"),
            title=q_data.get("title", "Current Quest"),
            description=q_data.get("description", ""),
            stage=q_data.get("stage", "Ongoing"),
            progress_percent=q_data.get("progress_percent", 50),
            objectives=[Objective(**o) for o in q_data.get("objectives", [])],
            status=q_data.get("status", "active")
        )
        state.current_quest = quest_update

    # Inventory updates
    inv_delta = parsed.get("inventory_changes", {})
    added_items = []
    for it_dict in inv_delta.get("added", []):
        new_it = InventoryItem(**it_dict)
        state.inventory.append(new_it)
        added_items.append(new_it.model_dump())

    removed_ids = inv_delta.get("removed", [])
    if removed_ids:
        state.inventory = [i for i in state.inventory if i.id not in removed_ids]

    # Character updates
    char_updates = []
    for c_data in parsed.get("character_updates", []):
        c_name = c_data.get("name")
        existing = next((c for c in state.characters if c.name.lower() == c_name.lower()), None)
        if existing:
            existing.affinity = c_data.get("affinity", existing.affinity)
            existing.status = c_data.get("status", existing.status)
            existing.notes = c_data.get("notes", existing.notes)
            char_updates.append(existing)
        else:
            new_dna = build_character_visual_dna(
                name=c_name,
                archetype=c_data.get("role", "Traveler"),
                theme=state.theme,
                session_id=state.session_id,
                custom_desc=c_data.get("visual_description", "")
            )
            new_char = Character(
                id=f"char_{c_name.lower()}",
                name=c_name,
                role=c_data.get("role", "Ally"),
                affinity=c_data.get("affinity", 50),
                visual_dna=new_dna,
                notes=c_data.get("notes", "")
            )
            state.characters.append(new_char)
            char_updates.append(new_char)

    # Player status updates
    p_stat = parsed.get("player_status", {})
    state.player.health = max(1, min(state.player.max_health, state.player.health + p_stat.get("health_delta", 0)))
    state.player.energy = max(0, min(state.player.max_energy, state.player.energy + p_stat.get("energy_delta", 0)))

    # Choices
    choices = []
    for i, ch in enumerate(parsed.get("choices", [])):
        choices.append(Choice(
            id=ch.get("id", f"c_{turn}_{i}"),
            text=ch.get("text", "Continue"),
            tag=ch.get("tag", "Action"),
            risk=ch.get("risk", "medium")
        ))
    state.available_choices = choices

    # Consistent Visual Generation
    active_char_names = [n.lower() for n in parsed.get("active_characters", [])]
    dna_list = [state.player.visual_dna]
    for c in state.characters:
        if c.name.lower() in active_char_names and c.visual_dna:
            dna_list.append(c.visual_dna)

    scene_prompt_info = build_scene_image_prompt(
        art_style_name=state.art_style,
        scene_description=parsed.get("image_scene_description", action_text),
        location=location,
        characters=dna_list,
        mood="cinematic and atmospheric"
    )

    state.last_scene_title = scene_title
    state.last_location = location
    state.last_narrative = narrative
    state.current_image_url = scene_prompt_info["url"]
    state.current_image_prompt = scene_prompt_info["prompt"]
    state.current_image_seed = scene_prompt_info["seed"]

    state.history.append(StoryNode(
        turn=turn,
        scene_title=scene_title,
        location=location,
        narrative=narrative,
        choice_taken=action_text,
        image_url=scene_prompt_info["url"],
        image_prompt=scene_prompt_info["prompt"],
        image_seed=scene_prompt_info["seed"]
    ))

    return TurnActionResponse(
        session_id=state.session_id,
        turn=turn,
        scene_title=scene_title,
        location=location,
        narrative=narrative,
        image_url=scene_prompt_info["url"],
        image_prompt=scene_prompt_info["prompt"],
        image_seed=scene_prompt_info["seed"],
        choices=choices,
        quest_update=quest_update,
        inventory_delta={"added": added_items, "removed": removed_ids},
        character_updates=char_updates,
        player_status=state.player,
        full_state=state
    )
