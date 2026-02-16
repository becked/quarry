# Old World Encyclopedia (Web)

Static web interface for browsing quarry's extracted game data. Built with [Astro](https://astro.build/), [Svelte](https://svelte.dev/), and [Tailwind CSS](https://tailwindcss.com/).

## Prerequisites

Run the quarry pipeline first to populate `output/`:

```bash
uv run python -m quarry --game-path "/path/to/Old World" --output-dir ./output
```

## Development

```bash
cd web
npm install
npm run dev      # Dev server at localhost:4321
npm run build    # Static build to dist/
npm run preview  # Preview the built site
```

## How It Works

Astro reads the JSON files from `output/` at build time and generates a static HTML page for every entry across all 37 categories. Game text markup like `link(TECH_IRONWORKING,2)` is resolved to display text and cross-reference links using `_text-forms.json`.
