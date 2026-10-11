# WARDESK toolkit

Renders the daily **WARDESK** (@wardesk_daily) war-news carousel: 7 × 1080×1350 PNG slides for Instagram + Facebook.

```
toolkit/
  build.py          # JSON -> HTML -> PNG (headless Chromium via Playwright)
  mapsvg.py         # GeoJSON -> SVG Mercator map renderer used by build.py
  brand.json        # name, handle, colours, fonts
  posts/YYYY-MM-DD.json   # one content file per day
  fonts/            # Anton.ttf, Oswald.ttf (committed)
  data/             # Natural Earth GeoJSON, ~44 MB (git-ignored, download below)
  out/YYYY-MM-DD/   # build output (git-ignored)
```

## Setup

Needs Python 3, Playwright for Python with Chromium, and the Inter font installed system-wide.

```bash
pip install playwright && playwright install --with-deps chromium   # skip the install step if Chromium is already present
sudo apt-get install -y fonts-inter                                 # if `fc-list | grep -i inter` is empty

# fonts (already committed; re-download if missing)
curl -fsSL -o toolkit/fonts/Anton.ttf  https://raw.githubusercontent.com/google/fonts/main/ofl/anton/Anton-Regular.ttf
curl -fsSL -o toolkit/fonts/Oswald.ttf 'https://raw.githubusercontent.com/google/fonts/main/ofl/oswald/Oswald%5Bwght%5D.ttf'

# map data (git-ignored, re-download in every fresh checkout)
mkdir -p toolkit/data
curl -fsSL -o toolkit/data/countries.geojson https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_50m_admin_0_countries.geojson
curl -fsSL -o toolkit/data/admin1.geojson    https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_10m_admin_1_states_provinces.geojson
```

## Build

```bash
cd toolkit && python3 build.py posts/2026-10-11.json
# -> out/2026-10-11/slide_01.png … slide_07.png, caption_instagram.txt, caption_facebook.txt
```

## Post JSON format

Copy `posts/2026-10-11.json` as the template. Top level: `date`, `date_label`, `slides`, `caption_instagram`, `caption_facebook`.

Slide types, in the usual order:

| type    | fields |
|---------|--------|
| `cover` | `kicker`, `title` (`<br>` allowed), `fronts` [{`k`, `v`}] ×4, `sources`, optional `map` |
| `map`   | `tag`, `map`, `headline`, `bullets` (3–4), `sources` — one per front |
| `stats` | `tag`, `headline`, `stats` [{`n`, `l`, `s` source, `amber`}] ×4, `sources` |
| `watch` | `tag`, `headline`, `bullets`, `cta`, `cta_sub`, `sources` |

Text markup: `**bold**`, `[[red]]`, `{{amber}}`.

`map` object: `bbox` [lon0, lat0, lon1, lat1]; `highlight` (country `ADMIN` names from countries.geojson);
`admin1` [[admin, name, colour-or-"hatch"]] (names from admin1.geojson, e.g. `["Ukraine","Donets'k","hatch"]`);
`labels` [{lon, lat, text, size?, color?}]; `points` [{lon, lat, label, sub?, kind: "strike"|"info", dx?, dy?}]
(`dx < 0` right-aligns the label to the left of the dot; use `dx`/`dy` to fix overlapping labels);
`arrows` [[[lon, lat], [lon, lat]]].

## Publishing

1. Copy the PNGs to `media/YYYY-MM-DD/slide_01.png …`, commit, push to `main`.
2. Check each `https://raw.githubusercontent.com/Thessman12/wardesk-media/main/media/YYYY-MM-DD/slide_0N.png` returns `200 image/png`
   (raw.githubusercontent.com sometimes returns 429; wait and re-check).
3. Zapier → Instagram for Business → **Publish Photo(s)** (`publish_media_v2`):
   `instagramPageId` = `17841415009582338` (Wardesk Daily), `media` = the raw URLs in order, `caption` = `caption_instagram`.
4. Zapier → Facebook Pages → **Create Page Photo** (`page_photo`):
   `page` = `1275897742282879` (Wardesk), `source` = the raw URLs in order, `message` = `caption_facebook`.

If any step fails, don't post a partial carousel.

## Daily automation

A scheduled Claude Code task, **"WARDESK daily post"**, runs every day at 6:52 AM America/Chicago. It researches the news, writes
`posts/YYYY-MM-DD.json`, builds and checks the slides, pushes them to `media/`, and publishes them through Zapier.

Editorial rules: every number names its source. Claims by warring parties are labelled as claims. If outlets disagree on a toll,
the post says so. No invented quotes. Nothing older than a week is presented as new.
Day counters: Ukraine–Russia Day 1 = 2022-02-24; Iran war Day 1 = 2026-02-28.
