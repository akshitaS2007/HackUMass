import React from "react";
import { Banknote, BookOpen, FlaskConical, Gauge, SlidersHorizontal } from "lucide-react";

import { money } from "../shared.jsx";


export default function ScoreChart({ rows, categories, onOpenAttack }) {
	const maxSuccess = Math.max(1, ...rows.map((row) => row.successes || 0));
	return (
		<>
			<div className="score-summary">
				{[
					{ label: "CONFIGURATIONS", value: rows.length, icon: SlidersHorizontal },
					{ label: "ATTEMPTS RECORDED", value: rows.reduce((sum, row) => sum + row.total, 0), icon: FlaskConical },
					{ label: "MONEY LOST", value: money(rows.reduce((sum, row) => sum + row.money_lost, 0)), icon: Banknote },
				].map(({ label, value, icon: Icon }) => (
					<div className="score-metric" key={label}>
						<div className="score-metric-icon"><Icon size={17} /></div><span>{label}</span><strong>{value}</strong>
					</div>
				))}
			</div>
			<section className="chart-panel">
				<div className="chart-panel-head">
					<div><h2>Attack outcomes by configuration</h2><p>Successful actions out of observed runs</p></div>
					<span className="chart-legend"><i /> Successful actions</span>
				</div>
				{rows.length ? <div className="bar-chart">{rows.map((row) => (
					<div className="bar-row" key={row.config}>
						<span>{row.config.replaceAll("_", " ")}</span>
						<div className="bar-track"><div className="bar-fill" style={{ width: `${Math.max(2, (row.successes / maxSuccess) * 100)}%` }} /></div>
						<strong>{row.successes} <small>/ {row.total}</small></strong>
						<span className="bar-loss">{money(row.money_lost)} lost</span>
					</div>
				))}</div> : <div className="score-empty">
					<div className="score-empty-icon"><Gauge size={23} /></div>
					<h3>Waiting on evidence</h3>
					<p>Run a test in Attack Mode or the local harness. Real outcomes will build the comparison chart here.</p>
					<button className="button button-outline" onClick={onOpenAttack}>
						<FlaskConical size={15} /> Open Attack Mode
					</button>
				</div>}
				<div className="honesty-note"><BookOpen size={15} /><span>LLM output can vary between runs. Compare observed money movement and data exposure, not just model wording.</span></div>
			</section>
			<section className="chart-panel category-panel">
				<div className="chart-panel-head">
					<div><h2>Outcomes by attack family</h2><p>Observed detections, grouped by the harness category and defense configuration</p></div>
					<span className="category-count">{new Set(categories.map((row) => row.category)).size} FAMILIES</span>
				</div>
				{categories.length ? <div className="category-chart">{categories.map((row) => (
					<div className="category-row" key={`${row.config}-${row.category}`}>
						<div className="category-name"><strong>{row.category}</strong><span>{row.config.replaceAll("_", " ")}</span></div>
						<div className="bar-track"><div className="bar-fill" style={{ width: `${Math.max(2, (row.successes / row.total) * 100)}%` }} /></div>
						<strong className="category-rate">{row.successes}<small> / {row.total}</small></strong>
						<span className="bar-loss">{money(row.money_lost)} lost</span>
					</div>
				))}</div> : <div className="category-empty">Run the local red-team harness to compare outcomes across attack families.</div>}
			</section>
		</>
	);
}