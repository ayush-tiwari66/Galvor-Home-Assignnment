# Ad label audit

**Sample:** 20 of 97 distinct videos, fixed in advance: 2 ads that distort the totals, the next 4 by spend, and 14 at random (`data/audit/audit_sample.csv`).

**Method:** Claude, the AI assistant used on this project, compared six frames per video (three from the first 3 seconds, three across the rest) plus the transcript with the system's labels. No person has reviewed these verdicts yet, and no audio was heard. The sample is too small to estimate error rates precisely, so the intervals below are wide.

| Label | Agree | Disagree | Can't tell | Agreement (decided ads) | 95% interval | Decision |
|---|---:|---:|---:|---:|---|---|
| `child_on_screen` | 19 | 0 | 1 | 100% | 83% to 100% | Use. Six frames can miss a child who appears late; denser frames confirmed all 3 such ads. |
| `child_in_first_3s` | 20 | 0 | 0 | 100% | 84% to 100% | Use. |
| `first_frame` | 20 | 0 | 0 | 100% | 84% to 100% | Use. |
| `ad_format` | 16 | 3 | 1 | 84% | 62% to 94% | Use with care: findings resting on a single format must be re-read against the videos. |
| `creator_type` | 15 | 0 | 5 | 100% | 80% to 100% | Use with care: roles often can't be told from the screen. |
| `product_shown_as` | 19 | 1 | 0 | 95% | 76% to 99% | Use with care. |
| `setting` | 16 | 0 | 4 | 100% | 81% to 100% | Use with care: many ads show only a tabletop. |
| `product_form` | 17 | 3 | 0 | 85% | 64% to 95% | Do not use. Replaced by our reviewed product map. |
| `product` | 18 | 1 | 1 | 95% | 75% to 99% | Use. This is our own map; the one error found was corrected. |

## Disagreements

| Ad | Label | System value | Finding |
|---|---|---|---|
| LJ-004 | `product_form` | milk_mix_powder | End card and tub read Proteinmix; mixed into roti dough |
| LJ-034 | `product_shown_as` | held_by_creator | Mostly scooped and mixed into dough; in_use fits better |
| LJ-038 | `product` | nutrimix_unspecified | Our own map was too broad: end card shows the 2+ tub. Map corrected |
| LJ-060 | `ad_format` | child_led | Polished film with no speech; silent_brand_film fits better |
| LJ-063 | `product_form` | gummies | Shows gummies and Nutrimix together; label captures only one |
| LJ-064 | `ad_format` | explainer_to_camera | Presenter looks away from camera over product shots; voiceover_montage fits better |
| LJ-084 | `ad_format` | explainer_to_camera | Staged two-person conversation; the matching LJ-052 setup is labelled skit |
| LJ-097 | `product_form` | milk_mix_powder | End card reads Proteinmix; on-screen DIY Quick Proteinmix Waffles |
