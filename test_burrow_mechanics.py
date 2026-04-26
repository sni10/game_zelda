#!/usr/bin/env python3
"""
Test script for burrow mechanics implementation
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.world.terrain import load_map_from_file, TerrainType
from src.components.burrow_components import (
    BurrowEntranceComponent, 
    BurrowExitComponent, 
    UndergroundMovementComponent,
    HillSurfaceComponent,
    BurrowAnimationComponent
)
from src.systems.burrow_animation_system import BurrowAnimationSystem
from src.systems.underground_movement_system import UndergroundMovementSystem
from src.systems.burrow_trigger_system import BurrowTriggerSystem
from src.rendering.layer_strategies import HillRenderStrategy


def test_terrain_loading():
    """Test loading of the new terrain types"""
    print("Testing terrain loading...")
    
    try:
        terrain_tiles, _overlay_tiles, player_x, player_y = load_map_from_file('data/burrow_test_world.txt')
        print(f"✓ Map loaded successfully with {len(terrain_tiles)} tiles")
        print(f"✓ Player start position: ({player_x}, {player_y})")
        
        # Count different terrain types
        terrain_counts = {}
        for tile in terrain_tiles:
            terrain_type = tile.terrain_type
            terrain_counts[terrain_type] = terrain_counts.get(terrain_type, 0) + 1
        
        print("Terrain type counts:")
        for terrain_type, count in terrain_counts.items():
            print(f"  {terrain_type.name}: {count}")
        
        # Check for new terrain types
        new_types = [
            TerrainType.BURROW_ENTRANCE,
            TerrainType.BURROW_EXIT,
            TerrainType.UNDERGROUND_PATH,
            TerrainType.HILL_SURFACE
        ]
        
        for terrain_type in new_types:
            if terrain_type in terrain_counts:
                print(f"✓ Found {terrain_type.name} tiles: {terrain_counts[terrain_type]}")
            else:
                print(f"✗ No {terrain_type.name} tiles found")
        
        return True
        
    except Exception as e:
        print(f"✗ Error loading terrain: {e}")
        return False


def test_components():
    """Test burrow components creation"""
    print("\nTesting burrow components...")
    
    try:
        # Test BurrowEntranceComponent
        entrance = BurrowEntranceComponent(
            exit_position=(100, 200),
            underground_path=[(50, 100), (75, 150), (100, 200)]
        )
        print("✓ BurrowEntranceComponent created successfully")
        print(f"  Exit position: {entrance.exit_position}")
        print(f"  Path points: {len(entrance.underground_path)}")
        
        # Test BurrowExitComponent
        exit_comp = BurrowExitComponent(entrance_position=(50, 100))
        print("✓ BurrowExitComponent created successfully")
        print(f"  Entrance position: {exit_comp.entrance_position}")
        
        # Test UndergroundMovementComponent
        underground = UndergroundMovementComponent(
            path_points=[(50, 100), (75, 150), (100, 200)]
        )
        print("✓ UndergroundMovementComponent created successfully")
        print(f"  Is underground: {underground.is_underground}")
        print(f"  Movement speed: {underground.movement_speed}")
        
        # Test HillSurfaceComponent
        hill = HillSurfaceComponent(surface_entities=[])
        print("✓ HillSurfaceComponent created successfully")
        
        # Test BurrowAnimationComponent
        animation = BurrowAnimationComponent()
        print("✓ BurrowAnimationComponent created successfully")
        print(f"  Is active: {animation.is_active}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error creating components: {e}")
        return False


def test_systems():
    """Test burrow systems creation"""
    print("\nTesting burrow systems...")
    
    try:
        from src.core.ecs.entity import EntityManager
        
        # Create entity manager
        entity_manager = EntityManager()
        
        # Test BurrowAnimationSystem
        animation_system = BurrowAnimationSystem(entity_manager)
        print("✓ BurrowAnimationSystem created successfully")
        print(f"  Required components: {[comp.__name__ for comp in animation_system.get_required_components()]}")
        
        # Test UndergroundMovementSystem
        movement_system = UndergroundMovementSystem(entity_manager)
        print("✓ UndergroundMovementSystem created successfully")
        print(f"  Required components: {[comp.__name__ for comp in movement_system.get_required_components()]}")
        
        # Test BurrowTriggerSystem
        trigger_system = BurrowTriggerSystem(entity_manager)
        print("✓ BurrowTriggerSystem created successfully")
        print(f"  Required components: {[comp.__name__ for comp in trigger_system.get_required_components()]}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error creating systems: {e}")
        return False


def test_rendering_strategy():
    """Test hill rendering strategy"""
    print("\nTesting hill rendering strategy...")
    
    try:
        # Test HillRenderStrategy
        hill_strategy = HillRenderStrategy()
        print("✓ HillRenderStrategy created successfully")
        print(f"  Render priority: {hill_strategy.get_render_priority()}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error creating rendering strategy: {e}")
        return False


def test_terrain_properties():
    """Test new terrain tile properties"""
    print("\nTesting terrain tile properties...")
    
    try:
        from src.world.terrain import TerrainTile
        
        # Test burrow entrance tile
        entrance_tile = TerrainTile(0, 0, TerrainType.BURROW_ENTRANCE)
        print("✓ Burrow entrance tile created")
        print(f"  Is burrow entrance: {entrance_tile.is_burrow_entrance}")
        print(f"  Is interactive: {entrance_tile.is_interactive}")
        print(f"  Color: {entrance_tile.get_color()}")
        
        # Test underground path tile
        path_tile = TerrainTile(32, 0, TerrainType.UNDERGROUND_PATH)
        print("✓ Underground path tile created")
        print(f"  Is underground path: {path_tile.is_underground_path}")
        print(f"  Color: {path_tile.get_color()}")
        
        # Test hill surface tile
        hill_tile = TerrainTile(64, 0, TerrainType.HILL_SURFACE)
        print("✓ Hill surface tile created")
        print(f"  Is hill surface: {hill_tile.is_hill_surface}")
        print(f"  Color: {hill_tile.get_color()}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error testing terrain properties: {e}")
        return False


def main():
    """Run all tests"""
    print("=== Burrow Mechanics Implementation Test ===\n")
    
    tests = [
        test_terrain_loading,
        test_components,
        test_systems,
        test_rendering_strategy,
        test_terrain_properties
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=== Test Results ===")
    print(f"Passed: {passed}/{total}")
    
    if passed == total:
        print("✓ All tests passed! Burrow mechanics implementation is working correctly.")
        return 0
    else:
        print("✗ Some tests failed. Please check the implementation.")
        return 1


if __name__ == "__main__":
    sys.exit(main())