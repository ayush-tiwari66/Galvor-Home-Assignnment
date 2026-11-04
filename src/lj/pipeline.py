"""Run with: uv run python -m lj.pipeline"""
from __future__ import annotations

import sys

from lj import clean, config, ingest, validate


def main() -> int:
    raw = ingest.load_raw()
    checks = validate.run_all(raw)
    validate.write_report(checks, config.OUTPUTS_DIR)
    errors = validate.failed_errors(checks)
    print(f"Validation: {sum(c.passed for c in checks)}/{len(checks)} passed, {len(errors)} blocking.")
    if errors:
        for check in errors:
            print(f"  BLOCKING {check.dataset}: {check.name}: {check.detail}")
        return 1

    data = clean.clean_all(raw)
    config.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    # Processed tables contain the source text, so they stay out of the repo (see .gitignore).
    data.ads.to_csv(config.PROCESSED_DIR / "ads_clean.csv", index=False)
    data.posts.to_csv(config.PROCESSED_DIR / "posts_clean.csv", index=False)
    data.log.to_csv(config.OUTPUTS_DIR / "cleaning_log.csv", index=False)
    print(f"Cleaning log: {len(data.log)} changes.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
