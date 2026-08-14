import { Die } from "../types";

export type WaferRegion = "A" | "B" | "C" | "D" | "E";

export type WaferRegionStats = {
	region: WaferRegion;
	fullDies: number;
	partialDies: number;
	totalDies: number;
};

export const waferRegions: WaferRegion[] = ["A", "B", "C", "D", "E"];

/**
 * Assign a die to exactly one square wafer region using the die center.
 *
 * The wafer radius is divided into five equal parts. Region A is the central
 * square, while B-E are successive square rings. The square radius of a point
 * is max(|dx|, |dy|), measured from the wafer center.
 */
export function getDieWaferRegion(
	die: Die,
	waferWidth: number,
	waferHeight: number,
): WaferRegion {
	const waferCenterX = waferWidth / 2;
	const waferCenterY = waferHeight / 2;
	const dieCenterX = die.x + die.width / 2;
	const dieCenterY = die.y + die.height / 2;
	const waferRadius = Math.min(waferWidth, waferHeight) / 2;
	const squareRadius = Math.max(
		Math.abs(dieCenterX - waferCenterX),
		Math.abs(dieCenterY - waferCenterY),
	);
	const normalizedRadius = waferRadius > 0 ? squareRadius / waferRadius : 0;

	if (normalizedRadius <= 0.2) return "A";
	if (normalizedRadius <= 0.4) return "B";
	if (normalizedRadius <= 0.6) return "C";
	if (normalizedRadius <= 0.8) return "D";
	return "E";
}

/**
 * Count full and partial dies in A-E using unique die-center ownership.
 * A full die is any geometrically full die, regardless of whether fab yield
 * later marks it good or defective. Lost dies are excluded from region totals.
 */
export function getWaferRegionStats(
	dies: Die[],
	waferWidth: number,
	waferHeight: number,
): WaferRegionStats[] {
	const stats = waferRegions.reduce((acc, region) => {
		acc[region] = {
			region,
			fullDies: 0,
			partialDies: 0,
			totalDies: 0,
		};
		return acc;
	}, {} as Record<WaferRegion, WaferRegionStats>);

	dies.forEach((die) => {
		if (die.dieState === "lost") {
			return;
		}

		const region = getDieWaferRegion(die, waferWidth, waferHeight);
		const regionStats = stats[region];

		if (die.dieState === "partial") {
			regionStats.partialDies += 1;
		} else {
			regionStats.fullDies += 1;
		}
		regionStats.totalDies += 1;
	});

	return waferRegions.map((region) => stats[region]);
}
