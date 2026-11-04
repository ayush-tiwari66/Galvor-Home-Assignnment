"""Summarise the ad label audit recorded in data/audit/label_audit_ads.csv."""
from __future__ import annotations

import math
from pathlib import Path

import pandas as pd

from lj import config

AUDIT_FILE = config.AUDIT_DIR / "label_audit_ads.csv"

# How the analysis will treat each audited label. These are our decisions, so they're written down here.
USE_DECISION = {
    "child_on_screen": "Use. Six frames can miss a child who appears late; denser frames confirmed all 3 such ads.",
    "child_in_first_3s": "Use.",
    "first_frame": "Use.",
    "ad_format": "Use with care: findings resting on a single format must be re-read against the videos.",
    "creator_type": "Use with care: roles often can't be told from the screen.",
    "product_shown_as": "Use with care.",
    "setting": "Use with care: many ads show only a tabletop.",
    "product_form": "Do not use. Replaced by our reviewed product map.",
    "product": "Use. This is our own map; the one error found was corrected.",
}


def wilson_interval(successes: int, total: int, z: float = 1.96) -> tuple[float, float]:
    """95% interval for a proportion, chosen because it behaves sensibly at small n and near 100%."""
    if total == 0:
        return (float("nan"), float("nan"))
    p = successes / total
    denominator = 1 + z * z / total
    centre = (p + z * z / (2 * total)) / denominator
    spread = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / denominator
    return (max(0.0, centre - spread), min(1.0, centre + spread))


def load_audit(path: Path = AUDIT_FILE) -> pd.DataFrame:
    return pd.read_csv(path, keep_default_na=False)


def summarise(audit: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for label, group in audit.groupby("label", sort=False):
        agree = int((group.verdict == "agree").sum())
        disagree = int((group.verdict == "disagree").sum())
        low, high = wilson_interval(agree, agree + disagree)
        rows.append({"label": label, "ads": len(group), "agree": agree, "disagree": disagree,
                     "cannot_tell": int((group.verdict == "cannot_tell").sum()),
                     "agreement": agree / (agree + disagree) if agree + disagree else float("nan"),
                     "low": low, "high": high, "decision": USE_DECISION[label]})
    return pd.DataFrame(rows)


def write_report(audit: pd.DataFrame, folder: Path = config.OUTPUTS_DIR) -> None:
    summary = summarise(audit)
    lines = [
        "# Ad label audit", "",
        f"**Sample:** {audit.ad_id.nunique()} of 97 distinct videos, fixed in advance: 2 ads that distort the totals, "
        "the next 4 by spend, and 14 at random (`data/audit/audit_sample.csv`).", "",
        "**Method:** Claude, the AI assistant used on this project, compared six frames per video (three from the first "
        "3 seconds, three across the rest) plus the transcript with the system's labels. No person has reviewed these "
        "verdicts yet, and no audio was heard. The sample is too small to estimate error rates precisely, so the "
        "intervals below are wide.", "",
        "| Label | Agree | Disagree | Can't tell | Agreement (decided ads) | 95% interval | Decision |",
        "|---|---:|---:|---:|---:|---|---|",
    ]
    for r in summary.itertuples():
        lines.append(f"| `{r.label}` | {r.agree} | {r.disagree} | {r.cannot_tell} | {r.agreement:.0%} | {r.low:.0%} to {r.high:.0%} | {r.decision} |")
    lines += ["", "## Disagreements", "", "| Ad | Label | System value | Finding |", "|---|---|---|---|"]
    for r in audit[audit.verdict == "disagree"].itertuples():
        lines.append(f"| {r.ad_id} | `{r.label}` | {r.system_value} | {r.note} |")
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "label_audit.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    write_report(load_audit())
