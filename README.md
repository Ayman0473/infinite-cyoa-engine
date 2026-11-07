# Infinite Choose-Your-Own-Adventure Engine 🌌⚔️

An infinite, emergent choose-your-own-adventure engine with real-time consistent art generation, dynamic state mutation, and interactive HUD tracking.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688?logo=fastapi)
![License](https://img.shields.io/badge/License-MIT-green)

---

## ✨ Features

- **Emergent Branching Narrative**: Context-sensitive choices genuinely alter upcoming plot direction, NPC relationships, quests, and world conditions. No fixed rails or pre-scripted endings.
- **Balanced Class Archetypes**: Choose from 5 distinct, balanced character builds with unique perks and starter gear:
  - 🔮 **Runic Scholar**: +25 Max Energy (125 Energy) & Arcane Insight; lower physical HP (90). Starts with the *Aether Focusing Lens*.
  - 🛡️ **Ironclad Warden**: +25 Max Fortitude (125 HP) & Heavy Armor Resilience; reduced energy (85). Starts with the *Tempered Runesteel Buckler*.
  - 🗡️ **Shadow Stalker**: Balanced 105 HP / 105 Energy; Infiltration & Critical Strike Evasion. Starts with the *Shadow-Weave Cloak*.
  - 🕊️ **Silver-Tongue Envoy**: +20 Starting NPC Affinity & Persuasion Mastery; balanced 100 HP / 110 Energy. Starts with the *Signet of the Free Accord*.
  - 🧪 **Alchemical Medic**: Consumables 50% more potent & Field Alchemy; balanced 110 HP / 100 Energy. Starts with the *Vial of Pure Panacea*.
- **Consistent Art Style & Character DNA**:
  - Persistent character visual tokens (hair, eyes, facial traits, gear, apparel) and seed locks ensure characters look identical across scenes.
  - Curated art styles: Dark Fantasy Graphic Novel, Cyberpunk Synthwave, High Fantasy Watercolor, Cosmic Void, Cinematic Anime, and Medieval Woodcut.
  - Zero-latency rendering pipeline with instant procedural SVG scene fallback and real-time AI image cross-fading.
- **Dynamic Sidebar HUD**:
  - **Current Quest**: Multi-stage tracking with auto-updating objectives and live progress bar.
  - **Inventory Grid**: Slot-based management. Inspect lore or use items directly in the current scene.
  - **Character Codex**: Catalog of discovered NPCs with visual avatars and live affinity meters.
  - **Player Status**: Health, energy, and conditions (*Vigilant*, *Arcane Insight*, *Silentshadow*, etc.).
- **Chronicle Export**: 1-click Markdown export (📜 button in header) to save or download your full adventure chronicle, turns lived, and decisions taken.
- **Dual Engine Architecture**:
  - **Built-in Procedural Director**: Works 100% offline with zero configuration or API keys required.
  - **Live AI Mode**: Optional Gemini API key support via in-game settings modal (`⚙️`).
- **Tactile Procedural Audio**: Ambient synthesizers and feedback sound effects via Web Audio API.

---

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/Ayman0473/infinite-cyoa-engine.git
cd infinite-cyoa-engine
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the Application
**On Windows:**
Double-click `run.bat` or run:
```bash
python main.py
```

Open your browser to:
**[http://localhost:8000](http://localhost:8000)**

---

## 📁 Project Structure

```
├── main.py                 # FastAPI backend, static mounting, SVG & chronicle export
├── narrative_engine.py     # Emergent narrative director & state mutation logic
├── visual_engine.py        # Consistent Art Style manager & procedural SVG generators
├── models.py               # Pydantic schemas (GameState, Quest, Inventory, Character)
├── requirements.txt        # Python package requirements
├── run.bat                 # One-click Windows startup script
├── .gitignore              # Ignored files
└── static/
    ├── index.html          # Cyber-Fantasy HUD interface
    ├── style.css           # Glassmorphism theme, animations & responsive layout
    ├── app.js              # Frontend state manager and event handling
    └── audio.js            # Procedural Web Audio engine
```

---

## 📜 License
MIT License. Free to use, modify, and distribute.
