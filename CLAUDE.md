# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

LessonAI is an AI-powered educational comic book (HQ) generator focused on **Artificial Intelligence concepts**. It produces professional-grade cyberpunk comics (Marvel/DC quality) using a fixed cast of 8 tech-team characters, multi-agent orchestration (Agno framework), multi-provider image generation (DALL-E 3, Gemini, Flux, Stability AI), and a PIL-based composition engine rendering at A4 300 DPI (2480×3508px).

The primary language of the project (UI, prompts, documentation) is **Brazilian Portuguese**.

### Narrative Structure
Every episode follows a mandatory 6-act arc: **Mystery → Investigation → Explanation → Visualization → Understanding → Hook**. The 8 fixed characters (Kira, Sofia, Yuki, Marcus, Luna, AXIOM, Victor, Bia) are distributed across acts according to their narrative roles. Max 5 pages per episode.

## Commands

```bash
# Install dependencies
uv sync

# Run the app
uv run streamlit run app.py

# Run all tests
uv run pytest

# Run a single test file
uv run pytest tests/test_composer.py

# Run a specific test
uv run pytest tests/test_composer.py::TestClassName::test_method -v
```

No linter or formatter is currently configured.

## Architecture

### Entry Point
- **app.py** — Monolithic Streamlit app (~10k lines) with the full multi-step workflow: Theme → Script → Layout Editor → Image Generation → Composition → Export.

### Pipeline (src/pipeline/)
The core processing chain, each stage feeding the next:

1. **prompt_builder.py** — Consolidates Master Spec DNA, character designs, style anchors, and color palettes into visual prompts for image generation.
2. **image_engine.py** — Multi-provider image factory (OpenAI, Gemini, Replicate, Stability AI). Supports `IMAGE_MOCK=true` env var to skip API calls during development.
3. **vision_engine.py** — Uses Gemini Flash to detect character positions in generated images, returning normalized 0–1000 coordinates for balloon anchor placement.
4. **composer.py** (Master Spec v58.0) — The composition engine. Handles panel layouts (5-panel configurations), balloon rendering with 360° tail control, text auto-fitting across 12 dialogue styles, and hard/soft collision detection.
5. **balloon_presets.py** — PIL-based balloon generation engine with 15+ styles (standard, burst, cloud, thought, electronic, etc.), organic jittering, and a modifiers system.
6. **exporter.py** — PDF and media export via ReportLab.
7. **validator.py** — Output validation.

### Agents (src/agents/)
- **editorial.py** — Script generation using Agno agents with DuckDuckGo web search. Outputs structured Pydantic models (`RoteiroSchema` → `PaginaSchema` → `QuadroSchema`). Contains the `CAST_ROSTER` (8 fixed characters) and `NARRATIVE_ARC` (6-act structure). Enforces: 4–6 panels/page, max 22 words per balloon, ALL CAPS dialogue, automatic character distribution.

### Configuration (src/config/)
- **managers.py** — JSON-based persistence for themes, characters, and art styles (CRUD operations, seeded from `references/` text files). Data stored in `config/*.json`.
- **image_config.py** — Central constants: Master Spec styles, composer metrics (gutters, safe zones, borders), text scale map for dialogue styles, available models, and defaults.
- **master_spec_v58.json** — Full Master Spec configuration as structured JSON.

### UI (src/ui/)
- **sidebar.py** — Streamlit sidebar: style/LLM/image provider selection, language switching (6 languages), mock mode toggle, character/theme/style management.

### Reference Prompts (references/)
Modular editorial prompt files loaded by `src/prompts/loader.py`:
- `MASTER-PROMPT.txt`, `Story-Engine-Prompt.txt`, `Prompt-de-ARTE.txt`, `Prompt-de-CORES.txt`, `Prompt-de-DIREÇÃO-CINEMATOGRÁFICA-DOS-QUADROS.txt`, `Prompt-de-PERSONAGENS-CONSISTENTES.txt`, `Formatação-Marvel-DC.txt`

## Key Conventions

- **Coordinate system**: Normalized 0–1000 across all components for cross-resolution precision.
- **Dialogue styles**: 12 types (sussurro=0.6× to grito=1.6× scale) defined in `image_config.py` and rendered by `composer.py`.
- **Balloon presets**: Defined as PIL polygon generators in `balloon_presets.py`, referenced by name (e.g., `"standard"`, `"burst"`, `"cloud"`).
- **Structured script output**: All scripts follow `RoteiroSchema` → pages (`PaginaSchema`) → panels (`QuadroSchema`) Pydantic models in `editorial.py`.

## Environment Variables

Required API keys (loaded via `python-dotenv` from `.env`):
- `OPENAI_API_KEY` — DALL-E 3 image generation
- `GOOGLE_API_KEY` — Gemini image generation and vision detection
- `REPLICATE_API_TOKEN` — Flux image generation
- `TAVILY_API_KEY` — Web search enrichment
- `IMAGE_MOCK` — Set to `true` to use placeholder images (skips API calls)
