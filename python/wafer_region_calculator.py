#!/usr/bin/env python3
import argparse
import json
import math
from pathlib import Path
from typing import Any, Dict, List, Tuple

REGIONS = ("A", "B", "C", "D", "E")


def get_rect_corners(x: float, y: float, width: float, height: float):
    return [
        (x, y),
        (x + width, y),
        (x, y + height),
        (x + width, y + height),
    ]


def get_rect_center(x: float, y: float, width: float, height: float):
    return (x + width / 2.0, y + height / 2.0)


def is_inside_circle(x: float, y: float, center_x: float, center_y: float, radius: float) -> bool:
    return math.sqrt((x - center_x) ** 2 + (y - center_y) ** 2) <= radius


def is_inside_rectangle(x: float, y: float, rx: float, ry: float, rw: float, rh: float) -> bool:
    return x >= rx and x <= rx + rw and y >= ry and y <= ry + rh


def rectangle_is_inside_rectangle(
    inner_x: float,
    inner_y: float,
    inner_w: float,
    inner_h: float,
    outer_x: float,
    outer_y: float,
    outer_w: float,
    outer_h: float,
    allow_partial: bool,
) -> bool:
    points = get_rect_corners(inner_x, inner_y, inner_w, inner_h)
    points.append(get_rect_center(inner_x, inner_y, inner_w, inner_h))
    inside = [
        p for p in points
        if is_inside_rectangle(p[0], p[1], outer_x, outer_y, outer_w, outer_h)
    ]
    if allow_partial:
        non_edge = []
        for x, y in inside:
            if x in (outer_x, outer_x + outer_w) or y in (outer_y, outer_y + outer_h):
                continue
            non_edge.append((x, y))
        return len(non_edge) > 0
    return len(inside) == 5


def rectangles_in_rectangle(
    outer_w: float,
    outer_h: float,
    inner_w: float,
    inner_h: float,
    gap_x: float,
    gap_y: float,
    offset_x: float,
    offset_y: float,
    center: bool,
    include_partials: bool,
) -> Dict[str, Any]:
    positions = []
    effective_w = inner_w + gap_x
    effective_h = inner_h + gap_y
    half_gap_x = gap_x / 2.0
    half_gap_y = gap_y / 2.0
    count_x = math.floor(outer_w / effective_w)
    count_y = math.floor(outer_h / effective_h)
    start_x = half_gap_x
    start_y = half_gap_y
    if center:
        count_x += 2
        count_y += 2
        total_inner_w = count_x * effective_w - gap_x
        total_inner_h = count_y * effective_h - gap_y
        start_x = (outer_w - total_inner_w) / 2.0
        start_y = (outer_h - total_inner_h) / 2.0

    num_rows = 0
    num_cols = 0
    for row in range(count_y + 1):
        for col in range(count_x + 1):
            x = start_x + col * effective_w + offset_x
            y = start_y + row * effective_h + offset_y
            if rectangle_is_inside_rectangle(
                x, y, inner_w, inner_h,
                0.0, 0.0, outer_w, outer_h,
                include_partials,
            ):
                positions.append({"x": x, "y": y})
                num_rows = row + 1
                num_cols = col + 1

    return {"positions": positions, "numRows": num_rows, "numCols": num_cols}


def rectangles_in_circle(
    diameter: float,
    rect_w: float,
    rect_h: float,
    gap_x: float,
    gap_y: float,
    offset_x: float,
    offset_y: float,
    include_partials: bool,
) -> List[Dict[str, float]]:
    radius = diameter / 2.0
    step_x = rect_w + gap_x
    step_y = rect_h + gap_y
    positions = []
    min_col = math.floor((-radius - offset_x - rect_w) / step_x)
    max_col = math.ceil((radius - offset_x) / step_x)
    min_row = math.floor((-radius - offset_y - rect_h) / step_y)
    max_row = math.ceil((radius - offset_y) / step_y)
    min_overlapping = 1 if include_partials else 5

    for row in range(min_row, max_row + 1):
        for col in range(min_col, max_col + 1):
            x = col * step_x + offset_x
            y = row * step_y + offset_y
            points = get_rect_corners(x, y, rect_w, rect_h)
            points.append(get_rect_center(x, y, rect_w, rect_h))
            inside = sum(1 for px, py in points if is_inside_circle(px, py, 0.0, 0.0, radius))
            if inside >= min_overlapping:
                positions.append({"x": x + radius, "y": y + radius})
    return positions


def get_relative_die_positions(cfg: Dict[str, Any]):
    die_w = cfg["die_width_mm"]
    die_h = cfg["die_height_mm"]
    scribe_x = cfg["scribe_x_mm"]
    scribe_y = cfg["scribe_y_mm"]
    field_w = cfg["reticle_width_mm"]
    field_h = cfg["reticle_height_mm"]
    trim = cfg["reticle_enabled"]

    dies = rectangles_in_rectangle(
        field_w, field_h,
        die_w, die_h,
        scribe_x, scribe_y,
        0.0, 0.0,
        center=not trim,
        include_partials=False,
    )

    if trim and dies["positions"]:
        last = dies["positions"][-1]
        trimmed_w = last["x"] + die_w + scribe_x / 2.0
        trimmed_h = last["y"] + die_h + scribe_y / 2.0
    else:
        trimmed_w = field_w
        trimmed_h = field_h
    return dies, trimmed_w, trimmed_h


def create_die_map(cfg: Dict[str, Any], trans_x: float, trans_y: float):
    diameter = cfg["wafer_diameter_mm"]
    die_w = cfg["die_width_mm"]
    die_h = cfg["die_height_mm"]
    edge_loss = cfg["edge_loss_mm"]
    notch_keep_out = cfg["notch_keep_out_mm"]
    field_w = cfg["reticle_width_mm"]
    field_h = cfg["reticle_height_mm"]
    reticle_enabled = cfg["reticle_enabled"]

    dies_in_shot, trimmed_w, trimmed_h = get_relative_die_positions(cfg)
    if reticle_enabled:
        offset_x, offset_y = trans_x, trans_y
    else:
        offset_x = trans_x - field_w * 0.5
        offset_y = trans_y - field_h * 0.5

    shots = rectangles_in_circle(
        diameter,
        trimmed_w,
        trimmed_h,
        0.0,
        0.0,
        offset_x,
        offset_y,
        include_partials=True,
    )

    radius_inside_lossy_edge = diameter / 2.0 - edge_loss
    dies = []
    full_shots = 0
    partial_shots = 0
    shots_on_wafer = []

    for shot_index, shot in enumerate(shots):
        dies_this_shot = []
        full_in_shot = 0
        for die_index, rel in enumerate(dies_in_shot["positions"]):
            x = rel["x"] + shot["x"]
            y = rel["y"] + shot["y"]
            corners = get_rect_corners(x, y, die_w, die_h)
            good_corners = 0
            for cx, cy in corners:
                in_edge = is_inside_circle(
                    cx, cy,
                    diameter / 2.0,
                    diameter / 2.0,
                    radius_inside_lossy_edge,
                )
                above_notch = cy < diameter - notch_keep_out
                if in_edge and above_notch:
                    good_corners += 1

            if good_corners == 0:
                state = "lost"
            elif good_corners < 4:
                state = "partial"
            else:
                state = "full"
                full_in_shot += 1

            dies_this_shot.append({
                "key": f"{shot_index}:{die_index}",
                "x": x,
                "y": y,
                "width": die_w,
                "height": die_h,
                "state": state,
            })

        # Mirror the TS behavior: include a shot only if at least one die is geometrically full.
        if full_in_shot:
            shots_on_wafer.append(shot)
            if full_in_shot == len(dies_this_shot):
                full_shots += 1
            else:
                partial_shots += 1
            dies.extend(dies_this_shot)

    return {
        "dies": dies,
        "shots": shots_on_wafer,
        "full_shot_count": full_shots,
        "partial_shot_count": partial_shots,
        "dies_per_reticle_row": dies_in_shot["numCols"],
        "dies_per_reticle_col": dies_in_shot["numRows"],
        "trimmed_reticle_width_mm": trimmed_w,
        "trimmed_reticle_height_mm": trimmed_h,
    }


def count_geometric_states(dies: List[Dict[str, Any]]) -> Dict[str, int]:
    counts = {"full": 0, "partial": 0, "lost": 0}
    for die in dies:
        counts[die["state"]] += 1
    return counts


def get_search_period(cfg: Dict[str, Any]) -> Tuple[float, float]:
    die_pitch_x = cfg["die_width_mm"] + cfg["scribe_x_mm"]
    die_pitch_y = cfg["die_height_mm"] + cfg["scribe_y_mm"]
    if cfg["reticle_enabled"]:
        num_cols = math.floor(cfg["reticle_width_mm"] / die_pitch_x)
        num_rows = math.floor(cfg["reticle_height_mm"] / die_pitch_y)
        return (
            max(die_pitch_x, num_cols * die_pitch_x),
            max(die_pitch_y, num_rows * die_pitch_y),
        )
    return die_pitch_x, die_pitch_y


def js_grid_values(start: float, end: float, step: float):
    # Match a JS for-loop closely enough for this deterministic grid search.
    v = start
    guard = 0
    while v <= end + 1e-12:
        yield v
        v += step
        guard += 1
        if guard > 100000:
            raise RuntimeError("grid search loop guard exceeded")


def optimize_offset(cfg: Dict[str, Any], initial_x: float, initial_y: float):
    initial_map = create_die_map(cfg, initial_x, initial_y)
    initial_full = count_geometric_states(initial_map["dies"])["full"]
    best = {"x": initial_x, "y": initial_y, "full": initial_full}
    period_x, period_y = get_search_period(cfg)
    steps_per_dim = 25
    coarse_x = max(0.01, period_x / steps_per_dim)
    coarse_y = max(0.01, period_y / steps_per_dim)

    def grid_search(min_x, max_x, step_x, min_y, max_y, step_y, best_in):
        best_local = dict(best_in)
        for ty in js_grid_values(min_y, max_y, step_y):
            for tx in js_grid_values(min_x, max_x, step_x):
                tx4 = float(f"{tx:.4f}")
                ty4 = float(f"{ty:.4f}")
                m = create_die_map(cfg, tx4, ty4)
                full = count_geometric_states(m["dies"])["full"]
                if full > best_local["full"]:
                    best_local = {"x": tx4, "y": ty4, "full": full}
        return best_local

    best = grid_search(
        -period_x / 2.0, period_x / 2.0, coarse_x,
        -period_y / 2.0, period_y / 2.0, coarse_y,
        best,
    )
    fine_x = coarse_x / 5.0
    fine_y = coarse_y / 5.0
    best = grid_search(
        best["x"] - coarse_x, best["x"] + coarse_x, fine_x,
        best["y"] - coarse_y, best["y"] + coarse_y, fine_y,
        best,
    )
    ultra_x = fine_x / 5.0
    ultra_y = fine_y / 5.0
    best = grid_search(
        best["x"] - fine_x, best["x"] + fine_x, ultra_x,
        best["y"] - fine_y, best["y"] + fine_y, ultra_y,
        best,
    )
    return {
        "offset_x_mm": best["x"],
        "offset_y_mm": best["y"],
        "max_full_dies": best["full"],
        "search_period_x_mm": period_x,
        "search_period_y_mm": period_y,
    }


def die_region(die: Dict[str, Any], diameter: float) -> str:
    center = diameter / 2.0
    die_cx = die["x"] + die["width"] / 2.0
    die_cy = die["y"] + die["height"] / 2.0
    radius = diameter / 2.0
    square_radius = max(abs(die_cx - center), abs(die_cy - center))
    normalized = square_radius / radius if radius > 0 else 0.0
    if normalized <= 0.2:
        return "A"
    if normalized <= 0.4:
        return "B"
    if normalized <= 0.6:
        return "C"
    if normalized <= 0.8:
        return "D"
    return "E"


def region_stats(dies: List[Dict[str, Any]], diameter: float):
    stats = {
        r: {"full_dies": 0, "partial_dies": 0, "total_dies": 0}
        for r in REGIONS
    }
    for die in dies:
        if die["state"] == "lost":
            continue
        region = die_region(die, diameter)
        if die["state"] == "partial":
            stats[region]["partial_dies"] += 1
        else:
            stats[region]["full_dies"] += 1
        stats[region]["total_dies"] += 1

    for region in REGIONS:
        total = stats[region]["total_dies"]
        stats[region]["full_die_percent"] = (
            stats[region]["full_dies"] / total * 100.0 if total else 0.0
        )
    return stats


def normalize_input(data: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "die_width_mm": float(data["die_size_um"]["width"]) / 1000.0,
        "die_height_mm": float(data["die_size_um"]["height"]) / 1000.0,
        "scribe_x_mm": float(data["scribe_line_um"]["x"]) / 1000.0,
        "scribe_y_mm": float(data["scribe_line_um"]["y"]) / 1000.0,
        "wafer_diameter_mm": float(data["wafer"]["diameter_mm"]),
        "edge_loss_mm": float(data["wafer"].get("edge_loss_mm", 0.0)),
        "notch_keep_out_mm": float(data["wafer"].get("notch_keep_out_mm", 0.0)),
        "reticle_enabled": bool(data.get("reticle", {}).get("enabled", False)),
        "reticle_width_mm": float(data.get("reticle", {}).get("width_mm", data["die_size_um"]["width"] / 1000.0)),
        "reticle_height_mm": float(data.get("reticle", {}).get("height_mm", data["die_size_um"]["height"] / 1000.0)),
        "offset_x_mm": float(data.get("reticle", {}).get("offset_x_mm", 0.0)),
        "offset_y_mm": float(data.get("reticle", {}).get("offset_y_mm", 0.0)),
        "auto_optimize_offset": bool(data.get("reticle", {}).get("auto_optimize_offset", False)),
        "substrate_cost": float(data.get("substrate_cost", 0.0)),
    }


def calculate(data: Dict[str, Any]) -> Dict[str, Any]:
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
    region = region_stats(die_map["dies"], cfg["wafer_diameter_mm"])
    full_dies = counts["full"]
    partial_dies = counts["partial"]
    lost_dies = counts["lost"]

    yield_scenarios = []
    for y in data.get("fab_yield_percent", []):
        percent = float(y)
        expected_good = full_dies * percent / 100.0
        expected_defective = full_dies - expected_good
        cost_per_expected_good = cfg["substrate_cost"] / expected_good if expected_good > 0 else None
        yield_scenarios.append({
            "fab_yield_percent": percent,
            "expected_good_full_dies": round(expected_good, 6),
            "expected_defective_full_dies": round(expected_defective, 6),
            "substrate_cost_per_expected_good_die": (
                round(cost_per_expected_good, 6) if cost_per_expected_good is not None else None
            ),
        })

    result = {
        "input_summary": {
            "die_size_mm": {"width": cfg["die_width_mm"], "height": cfg["die_height_mm"]},
            "scribe_line_mm": {"x": cfg["scribe_x_mm"], "y": cfg["scribe_y_mm"]},
            "wafer": {
                "diameter_mm": cfg["wafer_diameter_mm"],
                "edge_loss_mm": cfg["edge_loss_mm"],
                "notch_keep_out_mm": cfg["notch_keep_out_mm"],
            },
            "reticle": {
                "enabled": cfg["reticle_enabled"],
                "width_mm": cfg["reticle_width_mm"],
                "height_mm": cfg["reticle_height_mm"],
                "requested_offset_x_mm": cfg["offset_x_mm"],
                "requested_offset_y_mm": cfg["offset_y_mm"],
                "auto_optimize_offset": cfg["auto_optimize_offset"],
                "used_offset_x_mm": offset_x,
                "used_offset_y_mm": offset_y,
            },
        },
        "geometry": {
            "full_dies": full_dies,
            "partial_dies": partial_dies,
            "excluded_lost_dies": lost_dies,
            "total_included_dies": full_dies + partial_dies,
            "full_shot_count": die_map["full_shot_count"],
            "partial_shot_count": die_map["partial_shot_count"],
            "dies_per_reticle": die_map["dies_per_reticle_row"] * die_map["dies_per_reticle_col"],
            "dies_per_reticle_row": die_map["dies_per_reticle_row"],
            "dies_per_reticle_col": die_map["dies_per_reticle_col"],
            "trimmed_reticle_width_mm": die_map["trimmed_reticle_width_mm"],
            "trimmed_reticle_height_mm": die_map["trimmed_reticle_height_mm"],
        },
        "regions": region,
        "fab_yield_scenarios": yield_scenarios,
        "notes": {
            "region_assignment": "die-center unique ownership using square radius max(|dx|, |dy|)",
            "full_die_definition": "all 4 die corners are inside the usable wafer boundary; fab yield does not change geometric full/partial counts",
            "fab_yield_scenarios": "expected values only; no random defective-die placement is performed",
            "yield_model_input": data.get("yield_model"),
            "all_die_area_critical_input": data.get("all_die_area_critical"),
            "critical_area_mm2_input": data.get("critical_area_mm2"),
        },
    }
    if optimization:
        result["offset_optimization"] = optimization
    return result


def main():
    parser = argparse.ArgumentParser(description="Wafer geometry and A-E region die counter")
    parser.add_argument("input_json", help="Path to input JSON")
    parser.add_argument("-o", "--output", help="Optional output JSON path")
    args = parser.parse_args()

    with open(args.input_json, "r", encoding="utf-8") as f:
        data = json.load(f)
    result = calculate(data)
    text = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(text + "\n", encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
