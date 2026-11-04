"""Choose the ad sample for the label audit, download the videos and build one frame sheet per ad.

Run with: uv run --group audit python scripts/audit_prepare.py
Add ad IDs after the command to build sheets for just those ads.

The sample is fixed in advance so it can't drift towards ads that happen to agree with the labels:
the two ads that distort the totals, the four next-largest by spend, then 14 chosen at random from the rest.
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

import imageio_ffmpeg
import pandas as pd
from PIL import Image, ImageDraw

from lj import clean, config, ingest

SEED = 20261104
RANDOM_SAMPLE = 14
VIDEO_DIR = config.AUDIT_DIR / "videos"
SHEET_DIR = config.AUDIT_DIR / "sheets"
TILE_WIDTH = 300


def choose_sample(ads: pd.DataFrame) -> pd.DataFrame:
    distinct = ads.drop_duplicates("creative_id")
    forced = distinct[distinct.ad_id.isin(["LJ-004", "LJ-089"])]
    largest = distinct[~distinct.ad_id.isin(forced.ad_id)].nlargest(4, "spend_inr")
    rest = distinct[~distinct.ad_id.isin(forced.ad_id) & ~distinct.ad_id.isin(largest.ad_id)]
    random = rest.sample(RANDOM_SAMPLE, random_state=SEED)
    sample = pd.concat([forced.assign(reason="distorts totals"), largest.assign(reason="largest spend"), random.assign(reason="random")])
    return sample.sort_values("ad_id")


def frame_times(duration: float) -> list[float]:
    """Three frames inside the first 3 seconds, for hook labels, then three across the rest of the ad."""
    return [0.2, 1.5, 2.8, duration * 0.35, duration * 0.65, max(duration - 1.0, 3.0)]


def extract(video: Path, seconds: float, target: Path) -> bool:
    command = [imageio_ffmpeg.get_ffmpeg_exe(), "-y", "-loglevel", "error", "-ss", f"{seconds:.2f}", "-i", str(video),
               "-frames:v", "1", "-vf", f"scale={TILE_WIDTH}:-2", str(target)]
    subprocess.run(command, check=True, timeout=60)
    return target.exists()


def build_sheet(video: Path, duration: float, ad_id: str, target: Path) -> None:
    tiles = []
    with tempfile.TemporaryDirectory() as folder:
        for i, seconds in enumerate(frame_times(duration)):
            frame = Path(folder) / f"{i}.jpg"
            if extract(video, seconds, frame):
                tile = Image.open(frame).convert("RGB")
                ImageDraw.Draw(tile).rectangle((0, 0, 90, 18), fill="black")
                ImageDraw.Draw(tile).text((3, 3), f"{ad_id} {seconds:.1f}s", fill="white")
                tiles.append(tile.copy())
    width, height = tiles[0].size
    sheet = Image.new("RGB", (width * 6, height), "white")
    for i, tile in enumerate(tiles):
        sheet.paste(tile, (i * width, 0))
    sheet.save(target, quality=82)


def main() -> None:
    ads = clean.clean_all(ingest.load_raw()).ads
    VIDEO_DIR.mkdir(parents=True, exist_ok=True)
    SHEET_DIR.mkdir(parents=True, exist_ok=True)
    named = sys.argv[1:]
    if named:  # targeted re-checks: build sheets for these ads and leave the fixed audit sample alone
        for row in ads[ads.ad_id.isin(named)].itertuples():
            video = VIDEO_DIR / f"{row.ad_id}.mp4"
            if not video.exists():
                urllib.request.urlretrieve(row.video_url, video)
            build_sheet(video, row.duration_s, row.ad_id, SHEET_DIR / f"{row.ad_id}.jpg")
            print(row.ad_id)
        return
    sample = choose_sample(ads)
    sample[["ad_id", "reason"]].to_csv(config.AUDIT_DIR / "audit_sample.csv", index=False)
    for row in sample.itertuples():
        video = VIDEO_DIR / f"{row.ad_id}.mp4"
        if not video.exists():
            urllib.request.urlretrieve(row.video_url, video)
        build_sheet(video, row.duration_s, row.ad_id, SHEET_DIR / f"{row.ad_id}.jpg")
        print(row.ad_id, row.reason)
    columns = ["ad_id", "reason", "child_on_screen", "child_in_first_3s", "first_frame", "ad_format", "creator_type",
               "product_shown_as", "setting", "product_form", "product"]
    print(sample[columns].to_string(index=False))


if __name__ == "__main__":
    main()
