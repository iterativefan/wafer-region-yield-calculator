import { Die } from "../types";
import { getDieWaferRegion, getWaferRegionStats } from "./regions";

function dieAtCenter(
	centerX: number,
	centerY: number,
	dieState: Die["dieState"] = "good",
): Die {
	return {
		key: `${centerX}:${centerY}:${dieState}`,
		x: centerX - 0.5,
		y: centerY - 0.5,
		width: 1,
		height: 1,
		dieState,
	};
}

describe("wafer regions", () => {
	it("assigns die centers to five square-radius bands", () => {
		const diameter = 300;
		const center = 150;

		expect(getDieWaferRegion(dieAtCenter(center, center), diameter, diameter)).toBe("A");
		expect(getDieWaferRegion(dieAtCenter(center + 30, center), diameter, diameter)).toBe("A");
		expect(getDieWaferRegion(dieAtCenter(center + 31, center), diameter, diameter)).toBe("B");
		expect(getDieWaferRegion(dieAtCenter(center, center + 61), diameter, diameter)).toBe("C");
		expect(getDieWaferRegion(dieAtCenter(center - 91, center - 20), diameter, diameter)).toBe("D");
		expect(getDieWaferRegion(dieAtCenter(center + 121, center), diameter, diameter)).toBe("E");
	});

	it("uses max axis distance rather than circular distance", () => {
		const diameter = 300;
		// dx=25, dy=25 => circular radius > 30 but square radius is only 25.
		expect(getDieWaferRegion(dieAtCenter(175, 175), diameter, diameter)).toBe("A");
	});

	it("counts good and defective geometry as full, partial separately, and excludes lost", () => {
		const diameter = 300;
		const dies: Die[] = [
			dieAtCenter(150, 150, "good"),
			dieAtCenter(160, 150, "defective"),
			dieAtCenter(190, 150, "partial"),
			dieAtCenter(230, 150, "lost"),
		];

		const stats = getWaferRegionStats(dies, diameter, diameter);
		expect(stats.find((region) => region.region === "A")).toEqual({
			region: "A",
			fullDies: 2,
			partialDies: 0,
			totalDies: 2,
		});
		expect(stats.find((region) => region.region === "B")).toEqual({
			region: "B",
			fullDies: 0,
			partialDies: 1,
			totalDies: 1,
		});
	});
});
