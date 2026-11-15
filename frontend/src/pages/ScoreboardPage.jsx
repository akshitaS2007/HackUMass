import React from "react";
import { Clock3 } from "lucide-react";

import ScoreChart from "../components/ScoreChart.jsx";
import { PageHeading } from "../shared.jsx";


export default function ScoreboardPage({ rows, categories, lastUpdated, onOpenAttack }) {
	return (
		<div className="standard-page">
			<PageHeading
				eyebrow="Your test runs"
				title="How did the checks do?"
				description="This page only shows runs you’ve actually made. No made-up scores."
				aside={lastUpdated && <div className="updated-stamp"><Clock3 size={14} /> Updated {lastUpdated.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}</div>}
			/>
			<ScoreChart rows={rows} categories={categories} onOpenAttack={onOpenAttack} />
		</div>
	);
}