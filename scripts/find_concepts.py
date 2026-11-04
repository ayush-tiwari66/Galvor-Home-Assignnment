"""Find ads that reuse the same footage or script, so they aren't counted as independent evidence.

Run with: uv run --group audit python scripts/find_concepts.py

Compares frame fingerprints (reads frames over HTTP, so nothing large is downloaded) and transcript text, then
writes candidate pairs for human review. The reviewed result lives in data/overrides/ad_concepts.csv.
"""
from __future__ import annotations

import difflib
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor
from itertools import combinations

import imageio_ffmpeg
import numpy as np
import pandas as pd

from lj import clean, config, ingest

CACHE = config.AUDIT_DIR / "frame_hashes.csv"
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
FRAMES_PER_AD = 8
USABLE_SHARE = 0.85  # the end card is shared across ads, so it would create false matches
MATCH_BITS = 10  # two frames of 64 bits count as the same shot if they differ by at most this many bits


def fingerprint(url: str, seconds: float) -> str | None:
    """A 64-bit difference hash of the frame's central area (ignores letterboxing and most captions)."""
    command = [FFMPEG, "-loglevel", "error", "-ss", f"{seconds:.2f}", "-i", url, "-frames:v", "1",
               "-vf", "crop=iw*0.7:ih*0.5,scale=9:8,format=gray", "-f", "rawvideo", "-"]
    try:
        raw = subprocess.run(command, capture_output=True, timeout=90).stdout
    except subprocess.TimeoutExpired:
        return None
    if len(raw) != 72:
        return None
    pixels = np.frombuffer(raw, dtype=np.uint8).reshape(8, 9).astype(int)
    bits = (pixels[:, 1:] > pixels[:, :-1]).ravel()
    return f"{int(''.join('1' if b else '0' for b in bits), 2):016x}"


def build_hashes(ads: pd.DataFrame) -> pd.DataFrame:
    if CACHE.exists():
        return pd.read_csv(CACHE, dtype={"hash": str})
    jobs = []
    for row in ads.drop_duplicates("creative_id").itertuples():
        usable = row.duration_s * USABLE_SHARE
        jobs += [(row.ad_id, row.video_url, usable * (i + 0.5) / FRAMES_PER_AD) for i in range(FRAMES_PER_AD)]
    with ThreadPoolExecutor(8) as pool:
        hashes = list(pool.map(lambda job: fingerprint(job[1], job[2]), jobs))
    table = pd.DataFrame({"ad_id": [j[0] for j in jobs], "seconds": [round(j[2], 2) for j in jobs], "hash": hashes})
    table.dropna(subset=["hash"]).to_csv(CACHE, index=False)
    return table.dropna(subset=["hash"])


def shots_shared(a: list[int], b: list[int]) -> int:
    """How many of a's frames have a near-identical frame somewhere in b."""
    return sum(min(bin(x ^ y).count("1") for y in b) <= MATCH_BITS for x in a)


def tidy(text) -> str:
    return re.sub(r"[^\w ]", " ", str(text).lower()).strip()


def main() -> None:
    ads = clean.clean_all(ingest.load_raw()).ads
    hashes = build_hashes(ads)
    frames = {ad: [int(h, 16) for h in group.hash] for ad, group in hashes.groupby("ad_id")}
    rows = ads.drop_duplicates("creative_id").set_index("ad_id")
    pairs = []
    for a, b in combinations(rows.index, 2):
        shared = shots_shared(frames.get(a, []), frames.get(b, [])) if frames.get(a) and frames.get(b) else 0
        speech = difflib.SequenceMatcher(None, tidy(rows.transcript[a])[:600], tidy(rows.transcript[b])[:600]).ratio()
        hook = difflib.SequenceMatcher(None, tidy(rows.hook_line[a]), tidy(rows.hook_line[b])).ratio()
        if shared >= 2 or speech >= 0.55 or hook >= 0.7:
            pairs.append({"a": a, "b": b, "shots": shared, "speech": round(speech, 2), "hook": round(hook, 2),
                          "lang": f"{rows.language[a]}/{rows.language[b]}", "product": f"{rows['product'][a]}/{rows['product'][b]}",
                          "roas": f"{rows.roas[a]:.2f}/{rows.roas[b]:.2f}", "hook_a": str(rows.hook_line[a])[:45], "hook_b": str(rows.hook_line[b])[:45]})
    result = pd.DataFrame(pairs).sort_values(["shots", "speech"], ascending=False)
    print(f"frames hashed: {len(hashes)} across {len(frames)} ads; candidate pairs: {len(result)}")
    print(result.to_string(index=False))


if __name__ == "__main__":
    main()
