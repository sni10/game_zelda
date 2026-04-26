# Концепция RPG механик для 2D Zelda-подобной игры
*Вдохновлено элементами из различных RPG игр*

## 1. Архитектура боевой системы

### 1.1 Ядро боевой системы

#### Базовая модель урона
```
DamageModel {
    base_damage: float
    damage_type: enum [Physical, Fire, Ice, Electric, Poison]
    damage_source: enum [Melee, Ranged, Environmental, Magic]
    armor_penetration: float (0-1)
    critical_multiplier: float (1.5-3.0)
    stagger_force: float
    knockback_vector: Vector2D
}
```

#### Система попаданий и коллизий
- **Hit Registration**: Ray-cast или box-collision для 2D
- **Hit Zones**: голова (x2 damage), торс (x1), конечности (x0.8)
- **Directional Combat**: учет направления атаки (фронт/тыл/фланг)
- **Counter Window**: 0.3-0.5 сек для парирования перед ударом противника

### 1.2 Система Adrenaline

```
AdrenalineSystem {
    max_points: 100
    gain_per_hit: 5-15 (зависит от типа удара)
    gain_per_kill: 20-40
    gain_per_environmental_kill: 50
    decay_rate: 2 points/sec после 3 сек без боя
    
    Fatality_Mode {
        activation_cost: 100
        duration: single_strike
        instant_kill: true
        animation_priority: highest
    }
    
    Enhanced_Magic {
        spell_damage_multiplier: 2.0
        spell_area_multiplier: 1.5
        special_effects: enabled
    }
}
```

## 2. Система оружия

### 2.1 Классы оружия

#### Мечи (Swords)
```
SwordClass {
    attack_speed: 1.0
    base_damage: 30-45
    stamina_cost: 15
    reach: 2 tiles
    sweep_arc: 120°
    
    Modes:
        - One_Handed: allows_shield, damage_mod: 0.85
        - Two_Handed: no_shield, damage_mod: 1.15, stagger_bonus: +30%
    
    Special_Attacks:
        - Power_Strike: hold 1.5s, damage x2, breaks_block
        - Charge_Attack: sprint + attack, stun 1s
        - Rotating_Slash: 360° arc, hits_multiple, requires adrenaline
    
    Skill_Requirements:
        - Orc_Cleaver: Strength_Level_2
        - Legendary_Weapons: Strength_Level_3
}
```

#### Кинжалы (Daggers)
```
DaggerClass {
    attack_speed: 1.5
    base_damage: 15-25 per blade
    dual_wield: mandatory
    stamina_cost: 10
    reach: 1 tile
    
    Special_Mechanics:
        - Backstab: x4 damage from behind
        - Stealth_Kill: instant if undetected
        - Poison_Application: applies DoT
        - Faster_Movement: +15% while equipped
    
    Combo_System:
        - Quick_Slash: LMB x3
        - Cross_Cut: LMB + RMB alternating
        - Bleed_Combo: Power_Strike from stealth
}
```

#### Посохи (Staves)
```
StaffClass {
    attack_speed: 0.7
    base_damage: 35-50
    stamina_cost: 20
    reach: 3 tiles
    sweep_arc: 180°
    
    Unique_Properties:
        - Area_Damage: hits all enemies in arc
        - Knockdown_Chance: 40% on power strike
        - Stagger_Guaranteed: on normal hit
        - Ground_Slam: area stun 1.5s (special attack)
    
    Defensive_Bonus:
        - Block_Efficiency: 80%
        - Parry_Window: +0.2s bonus
}
```

#### Луки (Bows)
```
BowClass {
    draw_time: 1.0-2.0s
    base_damage: 40-80 (scales with draw)
    projectile_speed: 20 tiles/sec
    stamina_drain: 10/sec while drawn
    
    Arrow_Types:
        - Standard: base damage
        - Fire: +15 fire damage, ignites
        - Poison: DoT 5 dmg/sec for 10s
        - Rope: creates climbable anchor
    
    Skill_Progression:
        - Eagle_Eye: zoom 2x
        - Stable_Aim: reduced sway
        - Fast_Reload: -30% draw time
        - Multi_Shot: 2-3 arrows (multiplayer)
}
```

### 2.2 Система крафта оружия

```
ForgingSystem {
    Materials:
        - Iron: base stats
        - Steel: +20% damage, +10% durability
        - Mythril: +40% damage, magic conductivity
    
    Process_Steps:
        1. Heat_Metal: timing window 3s
        2. Shape_Blade: QTE sequence
        3. Quench: temperature management
        4. Sharpen: precision minigame
    
    Quality_Tiers:
        - Poor: 70% stats
        - Normal: 100% stats
        - Fine: 120% stats
        - Masterwork: 150% stats + special property
}
```

## 3. Магическая система

### 3.1 Базовые заклинания

#### Огненные заклинания
```
FireSpells {
    Fire_Trap {
        mana_cost: 20
        damage: 50
        trigger_radius: 1 tile
        invisible_to_enemies: true
        duration: 30s or until triggered
    }
    
    Fireball {
        mana_cost: 30
        damage: 40-60
        guided: mouse_controlled
        explosion_radius: 2 tiles
        adrenaline_effect: multi_projectile(3)
    }
    
    Flame_Burst {
        mana_cost: 40
        damage: 80-100
        cone_angle: 90°
        range: 4 tiles
        ignite_duration: 5s
        adrenaline_effect: damage x2
    }
    
    Ignite {
        mana_cost: 50
        damage: 60 + 30 AoE
        radius: 3 tiles
        DoT: 10/sec for 3s
    }
}
```

#### Ледяные заклинания
```
IceSpells {
    Freeze {
        mana_cost: 25
        duration: 2-4s
        creates_ice_patch: 3x3 tiles
        slip_chance: 80%
        adrenaline_effect: permanent_freeze
    }
    
    Ice_Ground {
        mana_cost: 15
        area: 5x2 tiles
        duration: 10s
        movement_penalty: -50%
        fall_damage_multiplier: 2x
    }
}
```

#### Электрические заклинания
```
LightningSpells {
    Lightning_Bolt {
        mana_cost: 35
        damage: 50-70
        chain_bounces: 3
        chain_damage_reduction: 20% per bounce
        water_amplification: 2x damage
        adrenaline_effect: chain_lightning(6 bounces)
    }
}
```

#### Утилитарные заклинания
```
UtilitySpells {
    Telekinesis {
        mana_cost: 20/sec
        grab_range: 5 tiles
        throw_force: based_on_object_weight
        damage: weight * velocity
        adrenaline_effect: grab_enemies
    }
    
    Night_Vision {
        mana_cost: 5 + 2/sec
        visibility_radius: +10 tiles
        highlight_enemies: true
        detect_traps: true
    }
    
    Heal {
        mana_cost: 40
        healing: 50-70 HP
        cast_time: 2s
        can_resurrect_at_level_3: true
    }
    
    Charm {
        mana_cost: 60
        duration: 30s
        max_targets: 1 (+1 per skill level)
        breaks_on_damage: 50% chance
    }
    
    Weaken {
        mana_cost: 30
        duration: 5-10s
        damage_reduction: -50%
        speed_reduction: -30%
        adrenaline_effect: permanent_shrink
    }
}
```

## 4. Расширенная боевая система *(планы на версии 3.0+)*

### 4.1 Продвинутые боевые механики
*Требует дополнительные анимации и ассеты*

```
AdvancedCombat {
    Combo_System {
        chain_attacks: 3-5 hit sequences
        timing_windows: 0.5s between hits
        damage_scaling: x1.0, x1.2, x1.5
        finishing_moves: special animations
    }
    
    Environmental_Hazards {
        Spike_Traps: instant_kill on contact
        Fire_Pits: DoT 20/sec
        Ice_Patches: movement_penalty -50%
        Poison_Gas: DoT + vision_reduction
    }
}
```

### 4.2 Взаимодействие с окружением *(версии 4.0+)*
*Потребует сложные анимации и физику*

```
EnvironmentalInteraction {
    Interactive_Objects {
        Levers: activate mechanisms
        Buttons: temporary effects
        Destructible_Walls: block/open passages
        Moving_Platforms: transportation
    }
}
```

## 5. Система прокачки

### 5.1 Древо навыков

```
SkillTree {
    Combat_Branch {
        Melee_Combat {
            Level_1: {
                unlocks: [Flurry_of_Blows, Charge]
                cost: 1 point
            }
            Level_2: {
                unlocks: [Disarm, Shield_Use]
                cost: 2 points
            }
            Level_3: {
                unlocks: [Breaking_Parry, Rotating_Slash]
                cost: 3 points
            }
        }
        
        Strength {
            Level_1: damage +15%, unlock heavy weapons
            Level_2: damage +30%, unlock orc weapons
            Level_3: damage +50%, unlock legendary weapons
        }
        
        Critical_Strike {
            Level_1: crit chance +10%
            Level_2: crit damage x2.5
            Level_3: crit applies bleed
        }
        
        Archery {
            Level_1: Eagle Eye (zoom)
            Level_2: Stable Aim
            Level_3: Fast Reload
        }
    }
    
    Magic_Branch {
        // Спеллы разблокируются покупкой
        spell_cost: 1-3 points each
        mana_upgrades: +20/40/60
    }
    
    Miscellaneous_Branch {
        Endurance {
            Level_1: HP +30
            Level_2: HP +60
            Level_3: HP +100
        }
        
        Stealth {
            Level_1: Silent_Walk
            Level_2: Backstab
            Level_3: Shadow_Hide + Pickpocket
        }
        
        Athletics {
            sprint_duration: +50%
            underwater_breathing: +100%
            kick_cooldown: -30%
        }
        
        Burglar {
            lockpicking: enabled
            trap_detection: visible at 3 tiles
            trap_disarm: enabled
        }
    }
}
```

### 5.2 Получение очков навыков

```
SkillPointSystem {
    Sources:
        - Mission_Objectives: 1-3 points
        - Secret_Areas: 1 point each
        - Boss_Defeats: 2-4 points
        - Challenge_Completion: 1-2 points
    
    Total_Per_Playthrough: ~40-50 points
    
    Respec_Option: special_item or altar
}
```

## 6. ИИ противников и паттерны

### 6.1 Базовые типы врагов

```
EnemyTypes {
    Melee_Guard {
        hp: 100
        attack_pattern: 3-hit combo
        block_chance: 50%
        vulnerable_to: backstab, environmental
        ai_behavior: aggressive, calls_reinforcements
    }
    
    Archer {
        hp: 60
        attack_range: 15 tiles
        retreat_trigger: player_distance < 3
        vulnerable_to: rush attacks
    }
    
    Mage {
        hp: 80
        spell_rotation: [fireball, teleport, shield]
        mana_regen: 10/sec
        interrupt_on_hit: 70% chance
    }
    
    Spider {
        hp: 150 (проблемный враг)
        jump_attack: 5 tile range
        poison_bite: 10 dmg/sec
        wall_climb: enabled
        cramped_space_spawner: true
    }
}
```

### 6.2 Продвинутый ИИ

```
AIBehaviorSystem {
    Environmental_Awareness {
        avoid_hazards: true
        use_cover: ranged units
        retreat_near_cliffs: when low hp
    }
    
    Group_Tactics {
        flanking_maneuvers: 3+ enemies
        synchronized_attacks: shield + archer
        morale_system: flee at 20% squad hp
    }
    
    Adaptive_Difficulty {
        reaction_time: 0.3-1.0s (based on difficulty)
        perfect_block_chance: 10-50%
        combo_variation: 2-5 patterns
    }
}
```

## 7. Оптимизация для 2D платформера

### 7.1 Адаптация для сетки

```
GridAdaptation {
    Movement {
        tile_size: 32x32 px
        sub_tile_precision: 4 subdivisions
        diagonal_movement: true
        momentum_preservation: true
    }
    
    Combat_Ranges {
        melee: 1-2 tiles
        polearm: 2-3 tiles
        ranged: 5-20 tiles
        spell: 3-15 tiles
    }
    
    Physics_Simplification {
        gravity: -9.8 m/s² (adjustable)
        friction: surface-dependent
        knockback: discrete tile jumps
        projectile_arc: parabolic with grid snap
    }
}
```

### 7.2 Визуальная обратная связь

```
VisualFeedback {
    Damage_Numbers {
        normal: white
        critical: yellow
        elemental: color-coded
        heal: green
    }
    
    Status_Effects {
        burning: flame particles
        frozen: ice overlay
        poisoned: green aura
        stunned: stars animation
    }
    
    Combat_Indicators {
        parry_window: flash effect
        backstab_angle: shadow indicator
        environmental_danger: red outline
    }
}
```

## 8. Мультиплеер адаптация

### 8.1 Классы персонажей

```
MultiplayerClasses {
    Archer: long-range specialist
    Priestess: AoE magic damage
    Paladin: tank + healing
    Knight: melee DPS
    Assassin: stealth + burst
}
```

### 8.2 Балансировка

```
PvPBalance {
    ttk (time to kill): 3-8 seconds
    respawn_timer: 5-15 seconds
    objective_scaling: based on team size
    matchmaking_elo: 1000-3000 range
}
```

## 9. Технические требования

### 9.1 Производительность

```
PerformanceTargets {
    fps: 60 stable
    input_lag: <50ms
    network_latency: <100ms acceptable
    physics_updates: 60Hz
    collision_checks: spatial hashing
}
```

### 9.2 Архитектура систем

```
SystemArchitecture {
    Combat_System: ECS-based
    Physics_Engine: Box2D or custom
    State_Machine: hierarchical FSM
    Ability_System: command pattern
    Damage_Pipeline: event-driven
}
```

## Итоговые замечания

Данная концепция представляет поэтапное развитие RPG механик для 2D игры:

**Приоритет версии 1.x-2.x:**
1. **Боевая система** - разнообразие оружия и атак
2. **Магическая система** - заклинания и мана
3. **Система прокачки** - навыки и характеристики  
4. **Крафт и инвентарь** - создание и улучшение предметов
5. **Зелья и расходники** - временные эффекты

**Отложенные возможности (3.0+):**
- Сложные анимации взаимодействий
- Физические механики 
- Продвинутые environmental эффекты

**Ключевые принципы:**
- Модульная архитектура для поэтапного добавления
- Баланс между простотой реализации и глубиной геймплея
- Фокус на core RPG механиках, а не на физических эффектах
- Избежание прямого копирования существующих игр