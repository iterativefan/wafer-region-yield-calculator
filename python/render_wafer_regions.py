#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle

from wafer_region_calculator import normalize_input


REGIONS = ("A", "B", "C", "D", "E")


def draw_wafer_regions(data, output_path: str):
    cfg = normalize_input(data)
    diameter = cfg["wafer_diameter_mm"]
    radius = diameter / 2.0
    cx = cy = radius

    fig, ax = plt.subplots(figsize=(8, 8), dpi=200)

    # Wafer outer boundary.
    ax.add_patch(Circle((cx, cy), radius, fill=False, linewidth=2.0))

    # A-E boundaries: square radius = max(|dx|, |dy|), split into 5 equal parts.
    for i in range(1, 5):
        half_side = radius * i / 5.0
        ax.add_patch(
            Rectangle(
                (cx - half_side, cy - half_side),
                2.0 * half_side,
                2.0 * half_side,
                fill=False,
                linewidth=1.4,
                linestyle="--",
            )
        )

    # Put one label in each square band along the upper vertical direction.
    label_y = {
        "A": cy,
        "B": cy - radius * 0.30,
        "C": cy - radius * 0.50,
        "D": cy - radius * 0.70,
        "E": cy - radius * 0.90,
    }
    for region in REGIONS:
        ax.text(
            cx,
            label_y[region],
            region,
            ha="center",
            va="center",
            fontsize=16,
            fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.2", facecolor="white", alpha=0.75),
        )

    ax.set_xlim(-5, diameter + 5)
    ax.set_ylim(diameter + 5, -5)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title("Wafer A-E Regions")

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output, bbox_inches="tight")
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(
        description="Render wafer A-E square regions from JSON input"
    )
    parser.add_argument("input_json", help="Path to input JSON")
    parser.add_argument(
        "-o",
        "--output",
        default="wafer_regions.png",
        help="Output PNG path",
    )
    args = parser.parse_args()

    with open(args.input_json, "r", encoding="utf-8") as f:
        data = json.load(f)

    draw_wafer_regions(data, args.output)
    print(json.dumps({"image": str(Path(args.output))}, ensure_ascii=False))


if __name__ == "__main__":
    main()
