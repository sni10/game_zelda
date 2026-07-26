"""
Тесты для combat loop: knockback, contact damage, game over, drops.
"""
import pytest
import pygame
import random
from unittest.mock import MagicMock, patch

from src.entities.enemy import Enemy, EnemyStats, LightEnemy, HeavyEnemy
from src.entities.enemy_ai import IdleBehavior
from src.systems.enemy_manager import EnemyManager
from src.systems.pickup_manager import PickupManager


@pytest.fixture
def world():
    w = MagicMock()
    w.width = 2000
    w.height = 2000
    w.check_collision.return_value = False
    return w


@pytest.fixture
def pickup_manager():
    return PickupManager()


@pytest.fixture
def enemy_manager(world, pickup_manager):
    em = EnemyManager(world, pickup_manager=pickup_manager)
    return em


def _make_enemy(x=500, y=500, hp=3, damage=1, speed=80):
    stats = EnemyStats(
        name='Test', max_health=hp, speed=speed,
        width=24, height=24, color=(200, 80, 80), damage=damage
    )
    zone = pygame.Rect(400, 400, 200, 200)
    return Enemy(x, y, stats, IdleBehavior(), zone)


class TestEnemyPlayerCollision:

    def test_enemy_does_not_overlap_player(self, world):
        """Враг не может войти в хитбокс игрока."""
        player = MagicMock()
        player.x = 100.0
        player.y = 100.0
        player.rect = pygame.Rect(100, 100, 32, 32)

        # Враг рядом, двигается к игроку
        enemy = _make_enemy(x=140, y=100, speed=200)
        old_x = enemy.x
        # update: AI двигает к игроку, но коллизия с player.rect откатывает
        enemy.update(0.5, world, player)
        # Враг НЕ должен залезть в игрока
        assert not enemy.rect.colliderect(player.rect)
        # Позиция осталась прежней (откат)
        assert enemy.x == old_x


class TestKnockbackOnEnemy:

    def test_enemy_gets_knockback_on_hit(self, enemy_manager):
        """Враг получает knockback при ударе мечом."""
        enemy = _make_enemy()
        enemy_manager.enemies.append(enemy)
        player = MagicMock()
        player.x = 480.0
        player.y = 500.0
        attack_rects = [pygame.Rect(490, 490, 30, 30)]
        enemy_manager.apply_player_attack(1, attack_rects, 1, player=player)
        assert enemy.knockback_timer > 0
        assert enemy.knockback_vx > 0  # Отлетает вправо (от игрока)


class TestEnemyAttackCooldown:

    def test_enemy_cannot_hit_twice_during_cooldown(self, enemy_manager):
        """Враг не бьёт повторно во время attack cooldown."""
        enemy = _make_enemy(x=100, y=100, damage=5)
        enemy_manager.enemies.append(enemy)

        player = MagicMock()
        player.x = 100.0
        player.y = 100.0
        player.rect = pygame.Rect(100, 100, 32, 32)
        player.is_invulnerable = False
        player.take_damage.return_value = True

        # Первый удар — проходит
        dmg = enemy_manager.apply_contact_damage(player)
        assert dmg == 5
        assert enemy.attack_cooldown_timer > 0

        # Сбрасываем invulnerable для чистоты теста
        player.is_invulnerable = False
        player.take_damage.reset_mock()

        # Второй удар сразу — блокируется cooldown врага
        dmg2 = enemy_manager.apply_contact_damage(player)
        assert dmg2 == 0
        player.take_damage.assert_not_called()

    def test_enemy_retreats_after_hit(self, enemy_manager):
        """Враг отскакивает назад после удара."""
        enemy = _make_enemy(x=100, y=100, damage=5)
        enemy_manager.enemies.append(enemy)

        player = MagicMock()
        player.x = 100.0
        player.y = 100.0
        player.rect = pygame.Rect(100, 100, 32, 32)
        player.is_invulnerable = False
        player.take_damage.return_value = True

        enemy_manager.apply_contact_damage(player)
        # Враг получил knockback (retreat)
        assert enemy.knockback_timer > 0


class TestContactDamageWithIframes:

    def test_contact_damage_uses_iframes(self, enemy_manager):
        """Контактный урон блокируется i-frames."""
        enemy = _make_enemy(x=100, y=100, damage=5)
        enemy_manager.enemies.append(enemy)

        player = MagicMock()
        player.x = 100.0
        player.y = 100.0
        player.rect = pygame.Rect(100, 100, 32, 32)
        player.is_invulnerable = False
        player.take_damage.return_value = True

        dmg = enemy_manager.apply_contact_damage(player)
        assert dmg == 5
        player.take_damage.assert_called_once_with(5)

    def test_no_damage_when_invulnerable(self, enemy_manager):
        """Неуязвимый игрок не получает контактный урон."""
        enemy = _make_enemy(x=100, y=100, damage=5)
        enemy_manager.enemies.append(enemy)

        player = MagicMock()
        player.is_invulnerable = True
        player.rect = pygame.Rect(100, 100, 32, 32)

        dmg = enemy_manager.apply_contact_damage(player)
        assert dmg == 0
        player.take_damage.assert_not_called()


class TestDropLoot:

    def test_drop_xp_always(self, enemy_manager, pickup_manager):
        """XP пикап всегда дропается при смерти."""
        random.seed(42)
        stats = EnemyStats(
            name='Light', max_health=1, speed=80,
            width=24, height=24, color=(200, 80, 80), damage=5
        )
        zone = pygame.Rect(400, 400, 200, 200)
        enemy = Enemy(500, 500, stats, IdleBehavior(), zone)
        enemy_manager.enemies.append(enemy)
        enemy.take_damage(1)
        enemy_manager.update(0.1)
        # XP всегда (light_xp_amount=3 > 0)
        assert pickup_manager.count() > 0

    def test_drop_hearts_when_player_hurt(self, enemy_manager, pickup_manager):
        """При неполном HP игрока дропаются сердечки, не монеты."""
        random.seed(0)  # seed где шансы проходят
        player = MagicMock()
        player.x = 0.0
        player.y = 0.0
        player.health = 3
        player.max_health = 10  # HP неполное

        # Много убийств для статистической проверки
        from src.entities.pickup import HeartPickup, CoinPickup
        for i in range(50):
            stats = EnemyStats(
                name='Heavy', max_health=1, speed=80,
                width=24, height=24, color=(200, 80, 80), damage=5
            )
            zone = pygame.Rect(400, 400, 200, 200)
            e = Enemy(500 + i, 500, stats, IdleBehavior(), zone)
            e.take_damage(1)
            enemy_manager.enemies.append(e)

        enemy_manager.update(0.1, player_x=0, player_y=0, player=player)

        hearts = sum(1 for p in pickup_manager.pickups if isinstance(p, HeartPickup))
        coins = sum(1 for p in pickup_manager.pickups if isinstance(p, CoinPickup))
        # При неполном HP — сердечки есть, монет нет
        assert hearts > 0
        assert coins == 0

    def test_drop_coins_when_player_full_hp(self, enemy_manager, pickup_manager):
        """При полном HP игрока дропаются монеты, не сердечки."""
        random.seed(0)
        player = MagicMock()
        player.x = 0.0
        player.y = 0.0
        player.health = 10
        player.max_health = 10  # HP полное

        from src.entities.pickup import HeartPickup, CoinPickup
        for i in range(50):
            stats = EnemyStats(
                name='Heavy', max_health=1, speed=80,
                width=24, height=24, color=(200, 80, 80), damage=5
            )
            zone = pygame.Rect(400, 400, 200, 200)
            e = Enemy(500 + i, 500, stats, IdleBehavior(), zone)
            e.take_damage(1)
            enemy_manager.enemies.append(e)

        enemy_manager.update(0.1, player_x=0, player_y=0, player=player)

        hearts = sum(1 for p in pickup_manager.pickups if isinstance(p, HeartPickup))
        coins = sum(1 for p in pickup_manager.pickups if isinstance(p, CoinPickup))
        assert hearts == 0
        assert coins > 0

    def test_no_drops_without_pickup_manager(self, world):
        """Без pickup_manager дроп не падает (не крашится)."""
        em = EnemyManager(world, pickup_manager=None)
        enemy = _make_enemy(hp=1)
        em.enemies.append(enemy)
        enemy.take_damage(1)
        em.update(0.1)  # Не должен крашнуться


class TestMeleeKillBonus:
    """Ближний бой (is_melee=True в apply_player_attack) даёт больше
    XP/монет с врага - см. config.ini [progression] melee_kill_bonus_multiplier."""

    def _kill_light_enemy(self, enemy_manager, pickup_manager, is_melee):
        pickup_manager.pickups.clear()
        stats = EnemyStats(
            name='Light', max_health=1, speed=80,
            width=24, height=24, color=(200, 80, 80), damage=5
        )
        zone = pygame.Rect(400, 400, 200, 200)
        enemy = Enemy(500, 500, stats, IdleBehavior(), zone)
        enemy_manager.enemies.append(enemy)
        player = MagicMock()
        player.x, player.y = 0.0, 0.0
        player.health = 10
        player.max_health = 10  # полное HP -> монеты, не сердечки
        enemy_manager.apply_player_attack(
            1, [enemy.rect], 1, player=player, is_melee=is_melee
        )
        enemy_manager.update(0.1, player_x=0, player_y=0, player=player)

    def test_melee_kill_grants_more_xp(self, enemy_manager, pickup_manager):
        from src.entities.pickup import XPOrbPickup

        self._kill_light_enemy(enemy_manager, pickup_manager, is_melee=True)
        melee_orbs = [p for p in pickup_manager.pickups if isinstance(p, XPOrbPickup)]
        assert len(melee_orbs) == 1
        melee_xp = melee_orbs[0].amount

        self._kill_light_enemy(enemy_manager, pickup_manager, is_melee=False)
        ranged_orbs = [p for p in pickup_manager.pickups if isinstance(p, XPOrbPickup)]
        assert len(ranged_orbs) == 1
        ranged_xp = ranged_orbs[0].amount

        assert melee_xp > ranged_xp

    def test_melee_kill_grants_more_coins(self, enemy_manager, pickup_manager):
        """random.random/randint зафиксированы - единственная разница между
        двумя убийствами - is_melee, значит и разница в монетах - от бонуса."""
        from src.entities.pickup import CoinPickup

        with patch('random.random', return_value=0.0), \
                patch('random.randint', return_value=2):
            self._kill_light_enemy(enemy_manager, pickup_manager, is_melee=True)
            melee_coins = sum(
                1 for p in pickup_manager.pickups if isinstance(p, CoinPickup)
            )

            self._kill_light_enemy(enemy_manager, pickup_manager, is_melee=False)
            ranged_coins = sum(
                1 for p in pickup_manager.pickups if isinstance(p, CoinPickup)
            )

        assert melee_coins > ranged_coins


class TestAmmoDrop:
    """Патроны с врагов (v0.4.0b) - независимая ветка от heal/coin."""

    def _kill_light_enemy(self, enemy_manager, pickup_manager, player=None):
        stats = EnemyStats(
            name='Light', max_health=1, speed=80,
            width=24, height=24, color=(200, 80, 80), damage=5
        )
        zone = pygame.Rect(400, 400, 200, 200)
        enemy = Enemy(500, 500, stats, IdleBehavior(), zone)
        enemy_manager.enemies.append(enemy)
        enemy_manager.apply_player_attack(1, [enemy.rect], 1, player=player)
        enemy_manager.update(0.1, player_x=0, player_y=0, player=player)

    def test_ammo_drops_when_chance_triggers(self, enemy_manager, pickup_manager):
        from src.entities.pickup import AmmoPickup

        with patch('random.random', return_value=0.0):  # проходит любой chance-ролл
            self._kill_light_enemy(enemy_manager, pickup_manager)

        ammo_pickups = [p for p in pickup_manager.pickups if isinstance(p, AmmoPickup)]
        assert len(ammo_pickups) == 1
        assert ammo_pickups[0].ammo_type == "bullets"
        assert ammo_pickups[0].amount > 0

    def test_ammo_does_not_drop_when_chance_fails(self, enemy_manager, pickup_manager):
        from src.entities.pickup import AmmoPickup

        with patch('random.random', return_value=0.999):  # заведомо выше любого chance
            self._kill_light_enemy(enemy_manager, pickup_manager)

        ammo_pickups = [p for p in pickup_manager.pickups if isinstance(p, AmmoPickup)]
        assert ammo_pickups == []

    def test_ammo_pickup_apply_adds_to_reserve_capped(self):
        from src.entities.pickup import AmmoPickup
        from src.entities.player import Player

        player = Player(0, 0)
        player._combat.reserve["bullets"] = 80
        pickup = AmmoPickup(0, 0, ammo_type="bullets", amount=50)
        pickup.apply(player)
        # config.ini: ammo_rifle_reserve_cap = 90
        assert player.reserve_count("bullets") == 90

    def test_ammo_pickup_visual_tiers_do_not_crash(self):
        from src.entities.pickup import AmmoPickup
        screen = pygame.Surface((200, 200))
        for amount in (3, 15, 40):
            AmmoPickup(50, 50, ammo_type="bullets", amount=amount).draw(screen, 0, 0)

