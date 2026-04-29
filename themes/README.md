<div align="center">
  <h1>Community Themes</h1>
  <p>Make your charts look exactly how you want</p>
</div>

## What's This?

This is where community-contributed themes live. Anyone can add a theme here and it'll be available to all ghlang users automatically.

## Theme Format

Themes are just JSON with 5 color values:

```jsonc
"your_theme_name": {
  "background": "#ffffff",  // chart background
  "text": "#1a1a1a",        // main text color
  "secondary": "#666666",   // secondary text (labels, etc)
  "legend_bg": "#f5f5f5",   // legend background
  "fallback": "#cccccc"     // color for unmapped languages
}
```

All colors should be hex codes (like `#ff5733`).

## Contributing a Theme

Want to add your theme? Here's how:

1. **Fork the repo** and edit `themes/manifest.json`

2. **Add your theme** with a descriptive name:

   ```json
   "your_theme_name": {
     "background": "#...",
     "text": "#...",
     "secondary": "#...",
     "legend_bg": "#...",
     "fallback": "#..."
   }
   ```

3. **Generate a preview** - run ghlang with your theme and save a chart:

   ```bash
   ghlang local . --theme your_theme_name -o preview
   ```

4. **Add the preview image** to `assets/themes/your_theme_name.png`

5. **Update the main README** - add a row to the themes table:

   ```markdown
   | `your_theme_name` | ![preview](url) | community |
   ```

6. **Submit a PR** with your changes

I'll review and merge it. Once it's in, everyone can use your theme after their cache refreshes (1-day TTL).

## Questions?

Open an [issue](https://github.com/MihaiStreames/ghlang/issues) if you need help or have questions about themes.
