#!/usr/bin/env python3

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Patch, Rectangle

from wafer_region_calculator import (
    create_die_map,
    normalize_input,
    optimize_offset,
)


REGIONS = ("A", "B", "C", "D", "E")


def get_final_offset(cfg):
    """Return the reticle offset actually used for die placement."""
    offset_x = cfg["offset_x_mm"]
    offset_y = cfg["offset_y_mm"]

    if cfg["auto_optimize_offset"]:
        optimization = optimize_offset(cfg, offset_x, offset_y)
        offset_x = optimization["offset_x_mm"]
        offset_y = optimization["offset_y_mm"]

    return offset_x, offset_y


def draw_die(ax, die):
    """Draw one die according to its geometric state."""
    state = die["state"]

    if state == "full":
        facecolor = "#C8E6C9"
        edgecolor = "#388E3C"
        linewidth = 0.8
        alpha = 0.70
    elif state == "partial":
        facecolor = "#FFE0B2"
        edgecolor = "#F57C00"
        linewidth = 1.0
        alpha = 0.80
    else:
        facecolor = "#EEEEEE"
        edgecolor = "#9E9E9E"
        linewidth = 0.5
        alpha = 0.45

    ax.add_patch(
        Rectangle(
            (die["x"], die["y"]),
            die["width"],
            die["height"],
            facecolor=facecolor,
            edgecolor=edgecolor,
            linewidth=linewidth,
            alpha=alpha,
            zorder=2,
        )
    )


def draw_region_boundaries(ax, diameter):
    """
    Draw A-E square-region boundaries.

    Region definition:
        r_square = max(|x - xc|, |y - yc|)

    The wafer radius is divided equally into five parts.
    """
    radius = diameter / 2.0
    cx = radius
    cy = radius

    for i in range(1, 5):
        half_side = radius * i / 5.0
        ax.add_patch(
            Rectangle(
                (cx - half_side, cy - half_side),
                2.0 * half_side,
                2.0 * half_side,
                fill=False,
                edgecolor="black",
                linewidth=1.5,
                linestyle="--",
                zorder=5,
            )
        )


def draw_region_labels(ax, diameter):
    """Place one A-E label in each square region."""
    radius = diameter / 2.0
    cx = radius
    cy = radius

    positions = {
        "A": (cx, cy),
        "B": (cx, cy - radius * 0.30),
        "C": (cx, cy - radius * 0.50),
        "D": (cx, cy - radius * 0.70),
        "E": (cx, cy - radius * 0.90),
    }

    for region in REGIONS:
        x, y = positions[region]
        ax.text(
            x,
            y,
            region,
            horizontalalignment="center",
            verticalalignment="center",
            fontsize=13,
            fontweight="bold",
            color="black",
            bbox={
                "boxstyle": "round,pad=0.20",
                "facecolor": "white",
                "edgecolor": "none",
                "alpha": 0.80,
            },
            zorder=10,
        )


def draw_wafer_regions(data, output_path):
    """Draw wafer, A-E regions, and all die positions."""
    cfg = normalize_input(data)

    diameter = cfg["wafer_diameter_mm"]
    radius = diameter / 2.0
    cx = radius
    cy = radius

    offset_x, offset_y = get_final_offset(cfg)
    die_map = create_die_map(cfg, offset_x, offset_y)
    dies = die_map["dies"]

    fig, ax = plt.subplots(figsize=(10, 10), dpi=200)

    # Draw all die rectangles first so wafer/region boundaries stay visible above them.
    for die in dies:
        draw_die(ax, die)

    # Wafer outer boundary.
    ax.add_patch(
        Circle(
            (cx, cy),
            radius,
            fill=False,
            edgecolor="black",
            linewidth=2.0,
            zorder=8,
        )
    )

    # Edge-loss boundary.
    edge_loss = cfg["edge_loss_mm"]
    if edge_loss > 0:
        ax.add_patch(
            Circle(
                (cx, cy),
                radius - edge_loss,
                fill=False,
                edgecolor="#555555",
                linewidth=1.2,
                linestyle=":",
                zorder=7,
            )
        )

    # Notch keep-out boundary. This follows the same geometry used by
    # wafer_region_calculator.py: y < diameter - notch_keep_out.
    notch_keep_out = cfg["notch_keep_out_mm"]
    if notch_keep_out > 0:
        notch_y = diameter - notch_keep_out
        ax.plot(
            [0, diameter],
            [notch_y, notch_y],
            color="#555555",
            linewidth=1.2,
            linestyle=":",
            zorder=7,
        )

    draw_region_boundaries(ax, diameter)
    draw_region_labels(ax, diameter)

    full_count = sum(1 for die in dies if die["state"] == "full")
    partial_count = sum(1 for die in dies if die["state"] == "partial")
    lost_count = sum(1 for die in dies if die["state"] == "lost")

    info_text = (
        f"Full Dies: {full_count}\n"
        f"Partial Dies: {partial_count}\n"
        f"Lost Dies: {lost_count}\n"
        f"Offset X: {offset_x:.4f} mm\n"
        f"Offset Y: {offset_y:.4f} mm"
    )

    ax.text(
        diameter + 8,
        diameter * 0.15,
        info_text,
        horizontalalignment="left",
        verticalalignment="top",
        fontsize=9,
        bbox={
            "boxstyle": "round,pad=0.4",
            "facecolor": "white",
            "edgecolor": "#BBBBBB",
        },
    )

    legend_items = [
        Patch(facecolor="#C8E6C9", edgecolor="#388E3C", label="Full Die"),
        Patch(facecolor="#FFE0B2", edgecolor="#F57C00", label="Partial Die"),
        Patch(facecolor="#EEEEEE", edgecolor="#9E9E9E", label="Lost Die"),
    ]

    ax.legend(
        handles=legend_items,
        loc="lower left",
        bbox_to_anchor=(1.02, 0.35),
        frameon=True,
    )

    margin = 5
    ax.set_xlim(-margin, diameter + 75)

    # Reverse Y axis to match the coordinate direction used by the placement logic.
    ax.set_ylim(diameter + margin, -margin)
    ax.set_aspect("equal", adjustable="box")
    ax.axis("off")
    ax.set_title("Wafer Die Map with A-E Regions", fontsize=15, pad=15)

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, bbox_inches="tight")
    plt.close(fig)

    return {
        "image": str(output_path),
        "full_dies": full_count,
        "partial_dies": partial_count,
        "lost_dies": lost_count,
        "offset_x_mm": offset_x,
        "offset_y_mm": offset_y,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Render wafer die placement together with A-E square wafer regions"
    )
    parser.add_argument("input_json", help="Path to wafer input JSON")
    parser.add_argument(
        "-o",
        "--output",
        default="wafer_regions.png",
        help="Output PNG path",
    )
    args = parser.parse_args()

    with open(args.input_json, "r", encoding="utf-8") as f:
        data = json.load(f)

    result = draw_wafer_regions(data, args.output)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
