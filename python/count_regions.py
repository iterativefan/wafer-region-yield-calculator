#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

from wafer_region_calculator import (
    normalize_input,
    optimize_offset,
    create_die_map,
    count_geometric_states,
    region_stats,
)


def calculate_region_counts(data):
    cfg = normalize_input(data)

    offset_x = cfg["offset_x_mm"]
    offset_y = cfg["offset_y_mm"]

    optimization = None
    if cfg["auto_optimize_offset"]:
        optimization = optimize_offset(cfg, offset_x, offset_y)
        offset_x = optimization["offset_x_mm"]
        offset_y = optimization["offset_y_mm"]

    die_map = create_die_map(cfg, offset_x, offset_y)
    counts = count_geometric_states(die_map["dies"])
    regions = region_stats(die_map["dies"], cfg["wafer_diameter_mm"])

    result = {
        "full_dies": counts["full"],
        "partial_dies": counts["partial"],
        "total_dies": counts["full"] + counts["partial"],
        "regions": regions,
        "used_offset_mm": {
            "x": offset_x,
            "y": offset_y,
        },
    }

    if optimization is not None:
        result["auto_optimized"] = True
    else:
        result["auto_optimized"] = False

    return result


def main():
    parser = argparse.ArgumentParser(
        description="Count full/partial dies in wafer regions A-E"
    )
    parser.add_argument("input_json", help="Path to input JSON")
    parser.add_argument("-o", "--output", help="Optional output JSON path")
    args = parser.parse_args()

    with open(args.input_json, "r", encoding="utf-8") as f:
        data = json.load(f)

    result = calculate_region_counts(data)
    text = json.dumps(result, ensure_ascii=False, indent=2)

    if args.output:
        Path(args.output).write_text(text + "\n", encoding="utf-8")

    print(text)


if __name__ == "__main__":
    main()
