import React from "react";
import { Clock3 } from "lucide-react";

import ScoreChart from "../components/ScoreChart.jsx";
import { PageHeading } from "../shared.jsx";


export default function ScoreboardPage({ rows, categories, lastUpdated, onOpenAttack }) {
	return (
		<div className="standard-page">
			<PageHeading
				eyebrow="MEASURED OUTCOMES"
				title="The scoreboard"
				description="Only recorded sandbox runs appear here. No pre-filled results, no estimated success rates."
				aside={lastUpdated && <div className="updated-stamp"><Clock3 size={14} /> UPDATED {lastUpdated.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</div>}
			/>
			<ScoreChart rows={rows} categories={categories} onOpenAttack={onOpenAttack} />
		</div>
	);
}