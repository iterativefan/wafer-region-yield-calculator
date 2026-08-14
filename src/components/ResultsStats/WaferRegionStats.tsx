import React from "react";
import { Die } from "../../types";
import { getWaferRegionStats } from "../../utils/regions";

export function WaferRegionStats(props: {
	dies: Die[];
	waferWidth: number;
	waferHeight: number;
}) {
	const regionStats = getWaferRegionStats(
		props.dies,
		props.waferWidth,
		props.waferHeight,
	);
	const totals = regionStats.reduce(
		(acc, region) => ({
			fullDies: acc.fullDies + region.fullDies,
			partialDies: acc.partialDies + region.partialDies,
			totalDies: acc.totalDies + region.totalDies,
		}),
		{ fullDies: 0, partialDies: 0, totalDies: 0 },
	);

	function fullDiePercent(fullDies: number, totalDies: number) {
		return totalDies > 0 ? `${((fullDies / totalDies) * 100).toFixed(2)}%` : "—";
	}

	return (
		<section className="wafer-region-stats" aria-label="Wafer region die statistics">
			<h3>Wafer Region Statistics</h3>
			<p className="wafer-region-stats__description">
				Each die is assigned to exactly one A-E region by its center point. The wafer radius is split into five equal square-radius bands.
			</p>
			<div className="wafer-region-stats__table-wrap">
				<table className="wafer-region-stats__table">
					<thead>
						<tr>
							<th scope="col">Region</th>
							<th scope="col">Full Dies</th>
							<th scope="col">Partial Dies</th>
							<th scope="col">Total Dies</th>
							<th scope="col">Full Die %</th>
						</tr>
					</thead>
					<tbody>
						{regionStats.map((region) => (
							<tr key={region.region}>
								<th scope="row">{region.region}</th>
								<td>{region.fullDies}</td>
								<td>{region.partialDies}</td>
								<td>{region.totalDies}</td>
								<td>{fullDiePercent(region.fullDies, region.totalDies)}</td>
							</tr>
						))}
					</tbody>
					<tfoot>
						<tr>
							<th scope="row">Total</th>
							<td>{totals.fullDies}</td>
							<td>{totals.partialDies}</td>
							<td>{totals.totalDies}</td>
							<td>{fullDiePercent(totals.fullDies, totals.totalDies)}</td>
						</tr>
					</tfoot>
				</table>
			</div>
		</section>
	);
}
