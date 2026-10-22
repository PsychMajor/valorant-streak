# Valorant Streak for Anki

Timed answer streaks, rising reward sounds, and a compact countdown for Anki desktop. Developed by PsychMajor.

## Release status

This repository contains the add-on's source code and tests. **An AnkiWeb release is not published yet.** Riot Games audio and artwork from the personal prototype are not included or licensed by this repository. The existing catalog describes that prototype's 28 collections; it is metadata, not a bundled sound pack. The source alone requires compatible local assets to run with audio and banners.

## What it does

- Hard, Good, or Easy extends a streak. You can exclude Hard.
- Each correct rating restarts a rolling deadline. Again or expiry resets it.
- Accelerating mode reduces each window by 20% by default, with a floor of 25% of the starting window. Fixed mode keeps it constant.
- Five reward stages; the fifth sound repeats while the counter continues past five.
- Adjustable volume, banner placement, duration, and countdown.
- Resets on undo, leaving reviews, opening settings, or closing a profile.

The timer measures time between ratings, including reading the question and viewing its answer. It uses your rating, not automated correctness detection. The shrinking window is a custom study mechanic, not a verified reproduction of Valorant's normal-round timing.

The add-on does not change cards, notes, scheduling, or card audio. It makes no network requests and requires no local server.

## Compatibility

Requires a Qt 6 build of Anki desktop. Tested with Anki 26.8.1's hooks and Qt libraries on macOS. Windows, Linux, and older versions have not been verified. Desktop add-ons do not run in AnkiMobile, AnkiDroid, or the AnkiWeb study interface.

## Build with your own compatible assets

Use only assets you have the rights to use. Supply a directory containing the files referenced by `addon/catalog.json`, or replace that catalog with your own collections using the same structure. Each collection needs an `id`, `name`, hex `color`, `banner` path, and five `sounds` entries with a `file` path. All asset paths must be below `assets/`.

```sh
python3 -m unittest discover -s tests -v
python3 scripts/build.py --assets /path/to/your/assets
```

The build validates all catalog paths and produces `dist/Valorant-Streak.ankiaddon`. In Anki desktop, use **Tools → Add-ons → Install from file**, select the package, and restart. Open **Tools → Valorant Streak…** to configure it. Do not enable two copies of this add-on simultaneously.

The build does not download game assets. Building a local package does not grant permission to redistribute third-party content.

## Development

`addon/core.py` contains pure timing rules; `addon/__init__.py` integrates review hooks, Qt overlays, settings, and audio. The test suite covers rolling deadlines, exact expiry, ratings, resets, accelerating windows, fifth-stage repeats, and invalid settings.

Report bugs using [GitHub Issues](https://github.com/PsychMajor/valorant-streak/issues), including your Anki version, operating system, and steps to reproduce. Do not attach your collection or private card content.

## License and attribution

The code in this repository is licensed under GNU AGPL v3 or later; see LICENSE. This license does not apply to third-party sounds or artwork, which are excluded. VALORANT is a Riot Games trademark. This independent project is not affiliated with or endorsed by Riot Games or Ankitects.
