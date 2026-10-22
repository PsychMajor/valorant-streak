Use **Tools → Valorant Streak…** for the friendly settings and sound previews.

- **enabled**: enable streak rewards.
- **collection**: choose one of the 28 collections in Tools → Valorant Streak. Available IDs: `reaver`, `prime`, `kuronami`, `oni`, `rgx_11z_pro`, `araxys`, `prelude_to_chaos`, `base`, `ion`, `glitchpop`, `recon`, `spectrum`, `gaia's_vengeance`, `sovereign`, `forsaken`, `elderflame`, `singularity`, `sentinels_of_light`, `ruination`, `chronovoid`, `neptune`, `magepunk`, `champions_2021`, `champions_2024`, `evori_dreamwings`, `mystbloom`, `neo_frontier`, `origin`.
- **window_seconds**: starting gap between successful answer ratings (1–600 seconds). The first correct answer always starts at 1 and gives the full starting window for answer 2.
- **timing_mode**: `accelerating` (default) or `fixed` (the original behavior). Accelerating is custom study pacing, not verified Valorant game timing.
- **shrink_percent**: percent shorter after each additional success, 1–75 (default 20). This continues after the ace for subsequent fifth-sound repeats.
- **minimum_window_percent**: shortest window as a percentage of the starting window, 5–100 (default 25). With a 10-second start the windows are 10, 8, 6.4, 5.12 seconds toward the ace, then 4.096, 3.2768, 2.62144, 2.5 seconds for repeats. Later repeats keep the 2.5-second floor.
- **count_hard**: if true, Hard/Good/Easy extend the streak. If false, only Good/Easy do; Hard resets it. Again always resets it.
- **volume**: effect volume, 0–100. Independent of card audio.
- **popup_seconds**: duration of the large reward banner, 0.5–8 seconds.
- **show_countdown**: show a small remaining-time bar after the banner disappears.
- **position**: `bottom_center` or `top_right`.

The fifth sound repeats at 5+ correct answers. An expired timer or non-counting
answer clears the streak; the next correct answer starts again at the full window.
The progress bar uses the current window, not the original starting duration.
Leaving review, undoing an action,
switching profiles, or changing settings clears the streak. Time continues while
you read a question, view the answer, or open another window. No cards or review
scheduling are changed. Anki desktop with Qt 6 only.
