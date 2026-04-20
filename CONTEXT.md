# Zebronics Soundbar Finder — Context

## Live URL
https://soundbars.zebronics.com

## Repo
zeb-g GitHub repo, root folder
GitHub Pages → main branch → root
CNAME → soundbars.zebronics.com

## Architecture
Static GitHub Pages site. No backend, no API, no build step.

```
Soundbar_Scores.xlsx  ← edit scores here (gitignored)
        ↓
convert_scores.py     ← run after editing Excel
        ↓
scores.json           ← committed to repo
products.json         ← committed to repo
index.html            ← committed to repo
        ↓
GitHub Pages → soundbars.zebronics.com
```

## Files
| File | Purpose |
|---|---|
| `index.html` | Full landing page — fetches products.json + scores.json |
| `products.json` | 37 soundbar SKUs — names, prices, ASINs, FSNs, URLs, specs |
| `scores.json` | Recommendation scores — 37 products × 13 dimensions |
| `Soundbar_Scores.xlsx` | Source scorecard (gitignored) — wide format, colour-coded |
| `convert_scores.py` | Excel → scores.json converter |
| `CNAME` | soundbars.zebronics.com |
| `img/` | Logo and images |

## How to update scores
1. Open `Soundbar_Scores.xlsx`
2. Change any score (1–5) in the coloured cells
3. Run: `python convert_scores.py`
4. Commit and push `scores.json`
5. Live within ~60 seconds

## How to update a product price or URL
1. Open `products.json`
2. Find the product by `id` and edit `price`, `mrp`, `amz`, `fk`, or `zeb`
3. Commit and push
4. Live within ~60 seconds

## How to add a new product
1. Add entry to `products.json` (copy an existing row as template)
2. Add a row to `Soundbar_Scores.xlsx` with a matching `product_id`
3. Run `convert_scores.py` → commit `scores.json`
4. Commit and push

## Amazon Associates
Tag: `zebaffiliate-21`
All Amazon URLs follow the format: `https://www.amazon.in/dp/ASIN?tag=zebaffiliate-21`
Keep this tag in every Amazon URL in products.json.

## Scoring dimensions (1 = worst fit, 5 = best fit)
**Room:** studio, small (1BHK), medium (2BHK), large (3BHK+)
**TV:** tv_small (32-43"), tv_medium (43-55"), tv_large (55-65"), tv_xlarge (65"+)
**Use:** movies, gaming, sports, everyday, music

## Phase 2 (planned ~2 months out)
Dealer lead capture via Supabase — requires adding a form + backend.
Products with `avail: "dealer"` are hidden in Phase 1.
Flip to `"online"` to show them, or `"both"` for online + dealer.

## Session history
- April 2026: Initial build — 37 products, full scoring, acoustic panel, sound demo
