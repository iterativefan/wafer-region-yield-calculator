# Python wafer region calculator

Standalone Python port of the wafer placement geometry used by the calculator, with A/B/C/D/E square-region statistics.

## Run

```bash
cd python
python wafer_region_calculator.py example_input.json -o example_output.json
```

The script also prints the same JSON to stdout.

## Test

```bash
cd python
python -m unittest -v test_wafer_region_calculator.py
```

No third-party Python packages are required.

## Region definition

Each non-lost die belongs to exactly one region based on its center point. Let the wafer center be `(xc, yc)` and the die center be `(x, y)`. Define the square radius as:

```text
r_square = max(abs(x - xc), abs(y - yc))
```

The wafer radius is split into five equal ranges: A=0-20%, B=20-40%, C=40-60%, D=60-80%, E=80-100% and beyond for edge-overlapping partial dies whose centers remain near the edge.

Geometric Full/Partial classification remains independent of fab yield: a Full Die has all four corners inside the usable wafer boundary after edge-loss and notch keep-out are applied.
