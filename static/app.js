/**
 * Main Frontend Application Controller for Infinite CYOA.
 * Coordinates state, UI events, dynamic sidebar updates,
 * real-time consistent art rendering, and procedural audio.
 */

const API_BASE = (window.location.origin && window.location.origin !== "null" && window.location.protocol.startsWith("http")) 
    ? window.location.origin 
    : "http://localhost:8000";

const state = {
    sessionId: localStorage.getItem("cyoa_session_id") || null,
    apiKey: localStorage.getItem("cyoa_api_key") || "",
    artStyle: "Dark Fantasy Graphic Novel",
    gameState: null,
    loading: false,
    selectedItem: null
};

// DOM References
const el = {
    // Header
    turnCount: document.getElementById("turn-count"),
    btnNewGame: document.getElementById("btn-new-game"),
    btnSettings: document.getElementById("btn-settings"),
    btnSound: document.getElementById("btn-sound"),
    btnExport: document.getElementById("btn-export"),
    
    // Stage
    visualImage: document.getElementById("visual-image"),
    visualLoader: document.getElementById("visual-loader"),
    badgeStyle: document.getElementById("badge-style"),
    badgeSeed: document.getElementById("badge-seed"),
    activeCharsBar: document.getElementById("active-chars-bar"),
    sceneLocation: document.getElementById("scene-location"),
    sceneTurn: document.getElementById("scene-turn"),
    sceneTitle: document.getElementById("scene-title"),
    narrativeText: document.getElementById("narrative-text"),
    eventBanner: document.getElementById("event-banner"),
    choicesList: document.getElementById("choices-list"),
    customActionInput: document.getElementById("custom-action-input"),
    btnCustomAction: document.getElementById("btn-custom-action"),

    // Dynamic Sidebar: Player
    playerName: document.getElementById("player-name"),
    playerArchetype: document.getElementById("player-archetype"),
    playerAvatar: document.getElementById("player-avatar"),
    barHp: document.getElementById("bar-hp"),
    textHp: document.getElementById("text-hp"),
    barEnergy: document.getElementById("bar-energy"),
    textEnergy: document.getElementById("text-energy"),
    conditionsRow: document.getElementById("conditions-row"),

    // Dynamic Sidebar: Current Quest
    questTitle: document.getElementById("quest-title"),
    questStage: document.getElementById("quest-stage"),
    questBarFill: document.getElementById("quest-bar-fill"),
    questPercent: document.getElementById("quest-percent"),
    objectivesList: document.getElementById("objectives-list"),

    // Dynamic Sidebar: Inventory
    inventoryGrid: document.getElementById("inventory-grid"),
    inventoryCount: document.getElementById("inventory-count"),

    // Dynamic Sidebar: Codex
    codexList: document.getElementById("codex-list"),

    // Modals
    newGameModal: document.getElementById("new-game-modal"),
    settingsModal: document.getElementById("settings-modal"),
    itemModal: document.getElementById("item-modal"),
    charModal: document.getElementById("char-modal"),

    // Inputs inside Modals
    inputApiKey: document.getElementById("input-api-key"),
    btnSaveSettings: document.getElementById("btn-save-settings"),
    btnStartNewGame: document.getElementById("btn-start-new-game"),
    newGameTheme: document.getElementById("new-game-theme"),
    newGameStyle: document.getElementById("new-game-style"),
    newGamePlayerName: document.getElementById("new-game-player-name"),
    newGameArchetype: document.getElementById("new-game-archetype"),
    classesGrid: document.getElementById("classes-grid"),
    selectedClassStatSummary: document.getElementById("selected-class-stat-summary"),
    choiceTimerCard: document.getElementById("choice-timer-card"),
    timerLabel: document.getElementById("timer-label"),
    timerSeconds: document.getElementById("timer-seconds"),
    timerFill: document.getElementById("timer-fill"),
    btnSkipTimer: document.getElementById("btn-skip-timer")
};

// Initialize
window.addEventListener("DOMContentLoaded", () => {
    initEvents();
    loadClasses();
    if (state.apiKey) {
        el.inputApiKey.value = state.apiKey;
    }
    
    // Check if existing session
    if (state.sessionId) {
        fetchGameState(state.sessionId);
    } else {
        // Open new game modal by default
        openModal(el.newGameModal);
    }
});

function initEvents() {
    if (el.btnExport) {
        el.btnExport.addEventListener("click", () => {
            window.soundEngine.playClick();
            if (!state.sessionId) {
                alert("Start or continue a story first to export your chronicle.");
                return;
            }
            window.open(`${API_BASE}/api/game/export/${state.sessionId}`, "_blank");
        });
    }

    el.btnNewGame.addEventListener("click", () => {
        window.soundEngine.playClick();
        openModal(el.newGameModal);
    });

    el.btnSettings.addEventListener("click", () => {
        window.soundEngine.playClick();
        openModal(el.settingsModal);
    });

    el.btnSound.addEventListener("click", () => {
        const isMuted = window.soundEngine.toggleMute();
        el.btnSound.innerHTML = isMuted ? "🔇" : "🔊";
    });

    el.btnSaveSettings.addEventListener("click", () => {
        window.soundEngine.playClick();
        state.apiKey = el.inputApiKey.value.trim();
        localStorage.setItem("cyoa_api_key", state.apiKey);
        closeModal(el.settingsModal);
    });

    el.btnStartNewGame.addEventListener("click", () => {
        window.soundEngine.playChoiceSelect();
        startNewAdventure();
    });

    if (el.btnSkipTimer) {
        el.btnSkipTimer.addEventListener("click", () => {
            unlockChoices();
        });
    }

    if (el.btnCustomAction) {
        el.btnCustomAction.addEventListener("click", () => {
            submitCustomAction();
        });
    }

    if (el.customActionInput) {
        el.customActionInput.addEventListener("keydown", (e) => {
            if (e.key === "Enter") {
                submitCustomAction();
            }
        });
    }

    // Close buttons on modals
    document.querySelectorAll(".modal-close").forEach(btn => {
        btn.addEventListener("click", (e) => {
            const modal = e.target.closest(".modal-overlay");
            if (modal) closeModal(modal);
        });
    });
}

async function loadClasses() {
    if (!el.classesGrid) return;
    try {
        const res = await fetch(`${API_BASE}/api/classes`);
        if (!res.ok) throw new Error("Failed to load classes");
        const classes = await res.json();
        renderClassCards(classes);
    } catch (err) {
        console.warn("Could not fetch classes from API, using defaults:", err);
        // Fallback default classes
        renderClassCards([
            {
                name: "Runic Scholar",
                icon: "🔮",
                tagline: "Master of ancient glyphs & ether currents",
                advantage: "High Energy (+25) & Deciphers Arcane Sigils",
                tradeoff: "Lower physical durability (90 HP)",
                base_health: 90,
                base_energy: 125,
                primary_stat: "Wits (16)",
                starter_item: { name: "Aether Focusing Lens" }
            },
            {
                name: "Ironclad Warden",
                icon: "🛡️",
                tagline: "Unbreakable bulwark against monstrosities",
                advantage: "High Fortitude (+25 HP) & Heavy Armor Resilience",
                tradeoff: "Reduced agility & reserve energy (85 Energy)",
                base_health: 125,
                base_energy: 85,
                primary_stat: "Might (16)",
                starter_item: { name: "Tempered Runesteel Buckler" }
            },
            {
                name: "Shadow Stalker",
                icon: "🗡️",
                tagline: "Phantom operative of stealth & ambush",
                advantage: "Flawless Infiltration & Critical Strike Evasion",
                tradeoff: "Vulnerable in open slugfests without cover",
                base_health: 105,
                base_energy: 105,
                primary_stat: "Agility (16)",
                starter_item: { name: "Shadow-Weave Cloak" }
            },
            {
                name: "Silver-Tongue Envoy",
                icon: "🕊️",
                tagline: "Master diplomat capable of turning foes into allies",
                advantage: "+20 Starting NPC Affinity & Persuasion Mastery",
                tradeoff: "Lower raw martial power in direct assaults",
                base_health: 100,
                base_energy: 110,
                primary_stat: "Presence (16)",
                starter_item: { name: "Signet of the Free Accord" }
            },
            {
                name: "Alchemical Medic",
                icon: "🧪",
                tagline: "Field apothecary and resourceful scavenger",
                advantage: "Consumables 50% More Potent & Emergency Remedy",
                tradeoff: "Requires reagent preparation & positioning",
                base_health: 110,
                base_energy: 100,
                primary_stat: "Wits/Survival (14)",
                starter_item: { name: "Vial of Pure Panacea" }
            }
        ]);
    }
}

function renderClassCards(classList) {
    if (!el.classesGrid) return;
    el.classesGrid.innerHTML = "";

    const currentVal = el.newGameArchetype ? el.newGameArchetype.value : "Runic Scholar";

    classList.forEach((c, idx) => {
        const card = document.createElement("div");
        const isSelected = c.name === currentVal || idx === 0;
        card.className = `class-card ${isSelected ? "selected" : ""}`;

        card.innerHTML = `
            <div class="class-card-header">
                <span class="class-card-title">${c.icon} ${escapeHtml(c.name)}</span>
                <span class="class-card-stat-pill">${escapeHtml(c.primary_stat)}</span>
            </div>
            <div class="class-card-advantage">✨ ${escapeHtml(c.advantage)}</div>
            <div class="class-card-tradeoff">⚖️ ${escapeHtml(c.tradeoff)}</div>
            <div class="class-card-starter">📦 Starter: <strong>${escapeHtml(c.starter_item?.name || 'Class Relic')}</strong> (HP: ${c.base_health} | Energy: ${c.base_energy})</div>
        `;

        card.addEventListener("click", () => {
            window.soundEngine.playClick();
            document.querySelectorAll(".class-card").forEach(elCard => elCard.classList.remove("selected"));
            card.classList.add("selected");
            if (el.newGameArchetype) {
                el.newGameArchetype.value = c.name;
            }
            if (el.selectedClassStatSummary) {
                el.selectedClassStatSummary.textContent = `HP: ${c.base_health} | Energy: ${c.base_energy} | ${c.primary_stat}`;
            }
        });

        if (isSelected && el.selectedClassStatSummary) {
            el.selectedClassStatSummary.textContent = `HP: ${c.base_health} | Energy: ${c.base_energy} | ${c.primary_stat}`;
            if (el.newGameArchetype) el.newGameArchetype.value = c.name;
        }

        el.classesGrid.appendChild(card);
    });
}

function openModal(modal) {
    if (modal) modal.classList.add("open");
}

function closeModal(modal) {
    if (modal) modal.classList.remove("open");
}

function showLoader(text = "The story unfolds...") {
    state.loading = true;
    el.visualLoader.classList.add("active");
    const loaderText = el.visualLoader.querySelector("p");
    if (loaderText) loaderText.textContent = text;
}

function hideLoader() {
    state.loading = false;
    el.visualLoader.classList.remove("active");
}

// ==========================================================================
// API Calls & Engine Sync
// ==========================================================================

async function startNewAdventure() {
    showLoader("Forging a new world & establishing visual anchors...");
    closeModal(el.newGameModal);

    const theme = el.newGameTheme.value;
    const artStyle = el.newGameStyle.value;
    const playerName = el.newGamePlayerName.value.trim() || "Traveler";
    const archetype = el.newGameArchetype.value.trim() || "Arcane Wanderer";

    state.artStyle = artStyle;

    const payload = {
        theme: theme,
        art_style: artStyle,
        player_name: playerName,
        player_archetype: archetype,
        api_key: state.apiKey || null
    };

    try {
        const res = await fetch(`${API_BASE}/api/game/new`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        if (!res.ok) throw new Error(`HTTP error ${res.status}`);
        const data = await res.json();

        state.sessionId = data.session_id;
        localStorage.setItem("cyoa_session_id", state.sessionId);

        renderTurnResponse(data);
        window.soundEngine.playQuestUpdate();
    } catch (err) {
        console.error("Failed to start new game:", err);
        alert("Failed to initialize adventure. Please try again.");
    } finally {
        hideLoader();
    }
}

async function fetchGameState(sessionId) {
    showLoader("Restoring adventure state...");
    try {
        const res = await fetch(`${API_BASE}/api/game/state/${sessionId}`);
        if (!res.ok) {
            // Expired or invalid session
            localStorage.removeItem("cyoa_session_id");
            openModal(el.newGameModal);
            return;
        }
        const stateData = await res.json();
        state.gameState = stateData;
        renderFullState(stateData);
    } catch (err) {
        console.error("Error restoring session:", err);
        openModal(el.newGameModal);
    } finally {
        hideLoader();
    }
}

async function sendAction(choiceId = null, customAction = null, useItemId = null) {
    if (state.loading) return;
    showLoader("Consulting the threads of fate...");

    const payload = {
        session_id: state.sessionId,
        choice_id: choiceId,
        custom_action: customAction,
        use_item_id: useItemId,
        api_key: state.apiKey || null
    };

    try {
        const res = await fetch(`${API_BASE}/api/game/action`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });

        if (!res.ok) throw new Error(`Action failed with status ${res.status}`);
        const data = await res.json();

        // Audio cues
        if (data.inventory_delta?.added?.length > 0) {
            window.soundEngine.playItemDiscovered();
        } else if (data.quest_update) {
            window.soundEngine.playQuestUpdate();
        } else {
            window.soundEngine.playChoiceSelect();
        }

        renderTurnResponse(data);
    } catch (err) {
        console.error("Action error:", err);
        alert("Failed to resolve action. Please try again.");
    } finally {
        hideLoader();
    }
}

function submitCustomAction() {
    const text = el.customActionInput.value.trim();
    if (!text) return;
    el.customActionInput.value = "";
    sendAction(null, text, null);
}

// ==========================================================================
// Rendering: Main Stage & Dynamic Sidebar
// ==========================================================================

function renderTurnResponse(data) {
    state.gameState = data.full_state;
    renderFullState(data.full_state);

    // Event Banner notice
    let notices = [];
    if (data.inventory_delta?.added?.length) {
        const itemNames = data.inventory_delta.added.map(i => i.name).join(", ");
        notices.push(`✨ Acquired: ${itemNames}`);
    }
    if (data.inventory_delta?.removed?.length) {
        notices.push(`🔻 Used/Lost: ${data.inventory_delta.removed.join(", ")}`);
    }

    if (notices.length > 0) {
        el.eventBanner.textContent = notices.join(" | ");
        el.eventBanner.classList.remove("hidden");
    } else {
        el.eventBanner.classList.add("hidden");
    }
}

function renderFullState(st) {
    if (!st) return;

    // Turn info
    el.turnCount.textContent = `Turn ${st.current_turn}`;
    el.sceneTurn.textContent = `Turn ${st.current_turn}`;
    el.sceneLocation.textContent = st.last_location || "Unknown Realm";
    el.sceneTitle.textContent = st.last_scene_title || "The Journey Unfolds";

    // Narrative text
    el.narrativeText.innerHTML = formatMarkdown(st.last_narrative);

    // Badges & Real-time Visual Image
    el.badgeStyle.textContent = st.art_style;
    el.badgeSeed.textContent = `Seed: #${st.current_image_seed || 42}`;

    // Immediate instant procedural scene SVG rendering (zero latency, zero failure)
    const sceneSvgUrl = `${API_BASE}/api/game/scene-svg/${st.session_id}?t=${Date.now()}`;
    el.visualImage.src = sceneSvgUrl;
    el.visualImage.style.opacity = "1";

    if (st.current_image_url) {
        // Preload external high-res AI generation with 7-second grace timeout
        const img = new Image();
        let active = true;
        const timer = setTimeout(() => {
            active = false;
        }, 7000);

        img.onload = () => {
            if (active) {
                clearTimeout(timer);
                el.visualImage.src = st.current_image_url;
            }
        };
        img.onerror = () => {
            clearTimeout(timer);
            // Retain procedural scene SVG
        };
        img.src = st.current_image_url;
    }

    // Active characters chips on image
    renderActiveCharacterChips(st);

    // Choices
    renderChoices(st.available_choices || []);

    // SIDEBAR: Player Status
    renderPlayerStatus(st.player);

    // SIDEBAR: Current Quest
    renderCurrentQuest(st.current_quest);

    // SIDEBAR: Inventory
    renderInventory(st.inventory || []);

    // SIDEBAR: Character Codex
    renderCodex(st.characters || []);
}

function renderActiveCharacterChips(st) {
    el.activeCharsBar.innerHTML = "";
    
    // Player chip
    const playerChip = document.createElement("div");
    playerChip.className = "char-chip";
    playerChip.innerHTML = `
        <div class="char-chip-avatar">
            <img src="${API_BASE}/api/game/character-svg/${st.session_id}/${encodeURIComponent(st.player.name)}" width="20" height="20" style="object-fit:cover;">
        </div>
        <span>${escapeHtml(st.player.name)} (You)</span>
    `;
    playerChip.addEventListener("click", () => openCharacterModal(st.player.visual_dna, "Protagonist"));
    el.activeCharsBar.appendChild(playerChip);

    // NPCs
    (st.characters || []).forEach(char => {
        const chip = document.createElement("div");
        chip.className = "char-chip";
        chip.innerHTML = `
            <div class="char-chip-avatar">
                <img src="${API_BASE}/api/game/character-svg/${st.session_id}/${encodeURIComponent(char.name)}" width="20" height="20" style="object-fit:cover;">
            </div>
            <span>${escapeHtml(char.name)}</span>
        `;
        chip.addEventListener("click", () => openCharacterModal(char.visual_dna, char.role, char.notes, char.affinity));
        el.activeCharsBar.appendChild(chip);
    });
}

function renderChoices(choices) {
    el.choicesList.innerHTML = "";
    if (!choices || choices.length === 0) {
        el.choicesList.innerHTML = `<div style="color:var(--text-dim); font-size:0.85rem;">The path ahead is quiet. Enter a custom action to proceed.</div>`;
        return;
    }

    choices.forEach(ch => {
        const btn = document.createElement("button");
        btn.className = "choice-btn locked";
        btn.disabled = true;
        
        let tagClass = "tag-default";
        const tagUpper = (ch.tag || "").toUpperCase();
        if (tagUpper.includes("ARCANA") || tagUpper.includes("LORE")) tagClass = "tag-arcana";
        else if (tagUpper.includes("MIGHT") || tagUpper.includes("COMBAT")) tagClass = "tag-might";
        else if (tagUpper.includes("SUBTERFUGE") || tagUpper.includes("STEALTH")) tagClass = "tag-subterfuge";
        else if (tagUpper.includes("DIALOGUE")) tagClass = "tag-dialogue";

        btn.innerHTML = `
            <span>${escapeHtml(ch.text)}</span>
            <span class="choice-tag ${tagClass}">${escapeHtml(ch.tag || "Action")}</span>
        `;

        btn.addEventListener("click", () => {
            if (timerInterval) clearInterval(timerInterval);
            window.soundEngine.playClick();
            sendAction(ch.id, null, null);
        });

        el.choicesList.appendChild(btn);
    });

    // Start 50-second consideration cooldown timer
    startChoiceTimer(50);
}

let timerRemaining = 50;
let timerInterval = null;

function startChoiceTimer(duration = 50) {
    if (timerInterval) clearInterval(timerInterval);
    timerRemaining = duration;

    // Lock all choice buttons
    const buttons = document.querySelectorAll(".choice-btn");
    buttons.forEach(btn => {
        btn.classList.add("locked");
        btn.disabled = true;
    });

    if (el.choiceTimerCard) {
        el.choiceTimerCard.classList.remove("unlocked");
        el.choiceTimerCard.style.display = "flex";
    }
    if (el.timerSeconds) el.timerSeconds.textContent = `${duration}s`;
    if (el.timerFill) el.timerFill.style.width = "100%";
    if (el.timerLabel) el.timerLabel.innerHTML = `⏳ Contemplating Consequences: <strong id="timer-seconds">${duration}s</strong>`;

    timerInterval = setInterval(() => {
        timerRemaining--;
        const pct = Math.max(0, (timerRemaining / duration) * 100);
        if (el.timerFill) el.timerFill.style.width = `${pct}%`;
        const secElem = document.getElementById("timer-seconds");
        if (secElem) secElem.textContent = `${timerRemaining}s`;

        if (timerRemaining <= 0) {
            unlockChoices();
        }
    }, 1000);
}

function unlockChoices() {
    if (timerInterval) clearInterval(timerInterval);
    timerInterval = null;

    const buttons = document.querySelectorAll(".choice-btn");
    buttons.forEach(btn => {
        btn.classList.remove("locked");
        btn.disabled = false;
    });

    if (el.choiceTimerCard) {
        el.choiceTimerCard.classList.add("unlocked");
    }
    if (el.timerLabel) {
        el.timerLabel.innerHTML = `✨ Path Unlocked — Select Your Next Move`;
    }
    if (el.timerFill) el.timerFill.style.width = "100%";

    if (window.soundEngine) window.soundEngine.playChoiceSelect();
}

function renderPlayerStatus(player) {
    if (!player) return;
    el.playerName.textContent = player.name;
    el.playerArchetype.textContent = player.archetype;

    // HP Bar
    const hpPct = Math.max(0, Math.min(100, Math.round((player.health / player.max_health) * 100)));
    el.barHp.style.width = `${hpPct}%`;
    el.textHp.textContent = `${player.health} / ${player.max_health}`;

    // Energy Bar
    const energyPct = Math.max(0, Math.min(100, Math.round((player.energy / player.max_energy) * 100)));
    el.barEnergy.style.width = `${energyPct}%`;
    el.textEnergy.textContent = `${player.energy} / ${player.max_energy}`;

    // Avatar
    if (state.sessionId && player.name) {
        el.playerAvatar.innerHTML = `<img src="${API_BASE}/api/game/character-svg/${state.sessionId}/${encodeURIComponent(player.name)}" width="48" height="48" style="width:100%;height:100%;object-fit:cover;">`;
    }

    // Conditions
    el.conditionsRow.innerHTML = "";
    (player.conditions || []).forEach(cond => {
        const pill = document.createElement("span");
        pill.className = "condition-pill";
        pill.textContent = cond;
        el.conditionsRow.appendChild(pill);
    });
}

function renderCurrentQuest(quest) {
    if (!quest) {
        el.questTitle.textContent = "No Active Quest";
        el.questStage.textContent = "Awaiting destiny";
        el.questBarFill.style.width = "0%";
        el.questPercent.textContent = "0%";
        el.objectivesList.innerHTML = "";
        return;
    }

    el.questTitle.textContent = quest.title;
    el.questStage.textContent = quest.stage || "In Progress";
    const pct = Math.max(0, Math.min(100, quest.progress_percent || 0));
    el.questBarFill.style.width = `${pct}%`;
    el.questPercent.textContent = `${pct}%`;

    el.objectivesList.innerHTML = "";
    (quest.objectives || []).forEach(obj => {
        const item = document.createElement("div");
        item.className = `objective-item ${obj.completed ? "done" : ""}`;
        item.innerHTML = `
            <div class="objective-checkbox">${obj.completed ? "✓" : ""}</div>
            <span>${escapeHtml(obj.text)}</span>
        `;
        el.objectivesList.appendChild(item);
    });
}

function renderInventory(inventory) {
    el.inventoryGrid.innerHTML = "";
    el.inventoryCount.textContent = `(${inventory.length})`;

    const totalSlots = Math.max(8, Math.ceil(inventory.length / 4) * 4);

    for (let i = 0; i < totalSlots; i++) {
        const slot = document.createElement("div");
        if (i < inventory.length) {
            const it = inventory[i];
            slot.className = "item-slot";
            slot.innerHTML = `
                <div class="item-slot-icon">${getItemEmoji(it.icon, it.category)}</div>
                <div class="item-slot-name">${escapeHtml(it.name)}</div>
                ${it.quantity > 1 ? `<div class="item-slot-qty">x${it.quantity}</div>` : ""}
            `;
            slot.addEventListener("click", () => {
                window.soundEngine.playClick();
                openItemModal(it);
            });
        } else {
            slot.className = "item-slot empty";
            slot.innerHTML = `<div style="font-size:0.8rem; color:var(--text-dim);">+</div>`;
        }
        el.inventoryGrid.appendChild(slot);
    }
}

function renderCodex(characters) {
    el.codexList.innerHTML = "";
    if (characters.length === 0) {
        el.codexList.innerHTML = `<div style="font-size:0.75rem; color:var(--text-dim);">No souls recorded yet.</div>`;
        return;
    }

    characters.forEach(char => {
        const card = document.createElement("div");
        card.className = "codex-card";
        card.innerHTML = `
            <div class="codex-avatar">
                <img src="${API_BASE}/api/game/character-svg/${state.sessionId}/${encodeURIComponent(char.name)}" width="38" height="38" style="width:100%;height:100%;object-fit:cover;">
            </div>
            <div class="codex-info">
                <h5>${escapeHtml(char.name)}</h5>
                <p>${escapeHtml(char.role)}</p>
            </div>
            <div class="codex-affinity">
                <span style="font-size:0.65rem; color:var(--text-dim);">Affinity</span>
                <span class="affinity-val">${char.affinity}%</span>
            </div>
        `;
        card.addEventListener("click", () => {
            window.soundEngine.playClick();
            openCharacterModal(char.visual_dna, char.role, char.notes, char.affinity);
        });
        el.codexList.appendChild(card);
    });
}

function getItemEmoji(icon, category) {
    switch (icon) {
        case "sword": return "⚔️";
        case "shield": return "🛡️";
        case "potion": return "🧪";
        case "gem": return "💎";
        case "key": return "🗝️";
        case "scroll": return "📜";
        case "spark": return "✨";
        default:
            if (category === "weapon") return "⚔️";
            if (category === "artifact") return "🔮";
            if (category === "consumable") return "🧪";
            return "📦";
    }
}

// ==========================================================================
// Modal Windows (Item Inspect & Character Dossier)
// ==========================================================================

function openItemModal(item) {
    state.selectedItem = item;
    const title = el.itemModal.querySelector("#item-modal-title");
    const desc = el.itemModal.querySelector("#item-modal-desc");
    const cat = el.itemModal.querySelector("#item-modal-cat");
    const btnUse = el.itemModal.querySelector("#btn-use-item");

    title.textContent = item.name;
    desc.textContent = item.description;
    cat.textContent = `Category: ${item.category.toUpperCase()}`;

    btnUse.onclick = () => {
        closeModal(el.itemModal);
        sendAction(null, null, item.id);
    };

    openModal(el.itemModal);
}

function openCharacterModal(dna, role, notes = "", affinity = null) {
    if (!dna) return;
    const nameEl = el.charModal.querySelector("#char-modal-name");
    const roleEl = el.charModal.querySelector("#char-modal-role");
    const avatarEl = el.charModal.querySelector("#char-modal-avatar");
    const dnaEl = el.charModal.querySelector("#char-modal-dna");
    const notesEl = el.charModal.querySelector("#char-modal-notes");

    nameEl.textContent = dna.name;
    roleEl.textContent = role || "Encountered Character";
    avatarEl.innerHTML = `<img src="${API_BASE}/api/game/character-svg/${state.sessionId}/${encodeURIComponent(dna.name)}" style="width:100%;height:100%;object-fit:cover;border-radius:12px;">`;

    dnaEl.innerHTML = `
        <div style="font-size:0.8rem; line-height:1.6; color:#cbd5e1;">
            <p><strong>Visual DNA Token:</strong></p>
            <p>• <strong>Face:</strong> ${escapeHtml(dna.face)}</p>
            <p>• <strong>Hair:</strong> ${escapeHtml(dna.hair)}</p>
            <p>• <strong>Eyes:</strong> ${escapeHtml(dna.eyes)}</p>
            <p>• <strong>Attire:</strong> ${escapeHtml(dna.attire)}</p>
            <p>• <strong>Feature:</strong> ${escapeHtml(dna.distinguishing_feature)}</p>
            <p>• <strong>Gear:</strong> ${escapeHtml(dna.signature_gear)}</p>
            <p>• <strong>Art Consistency Seed:</strong> #${dna.persistent_seed}</p>
        </div>
    `;

    notesEl.textContent = notes || "No additional lore entries recorded.";
    openModal(el.charModal);
}

// Helpers
function formatMarkdown(text) {
    if (!text) return "";
    let s = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    s = s.replace(/\*(.*?)\*/g, '<em>$1</em>');
    return s.split("\n\n").map(p => `<p>${p}</p>`).join("");
}

function escapeHtml(str) {
    if (!str) return "";
    return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}
