# Blueprint Project Overview

## Purpose
Procedural generation library using metaclass-based "magical blueprints" pattern for content generation.

## Architecture
- **Base**: `Blueprint` class with `BlueprintMeta` metaclass
- **Fields**: Dynamic field system with operators, random selection, templates
- **Tags**: Auto-tagging system with `TagRepository` for querying blueprints
- **Mods**: Blueprint modifiers that transform other blueprints
- **Factories**: Combine blueprints with mods for procedural generation
- **Dice**: Dice rolling expressions (3d6+2)
- **Markov**: Text generation via Markov chains

## Key Files
- `src/blueprint/base.py`: Core Blueprint and metaclass
- `src/blueprint/fields.py`: Field system and resolution
- `src/blueprint/taggables.py`: Tag repository and queries
- `src/blueprint/mods.py`: Blueprint modifiers
- `src/blueprint/factories.py`: Blueprint factories
- `src/blueprint/dice.py`: Dice roller
- `features/`: BDD tests using behave

## Testing
- BDD: `uv run behave` (legacy)
- pytest: `uv run pytest` (preferred)
- Doctests in source files

## Tools
- ruff: linting and formatting
- mypy: type checking (strict mode)
- Python 3.11+ only

## Modernization Status
Migrating from Python 2.7 to 3.11+, removing `six` dependency, adding type hints.
