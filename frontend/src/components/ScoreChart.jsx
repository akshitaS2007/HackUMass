import React from "react";
import { Banknote, BookOpen, FlaskConical, Gauge, SlidersHorizontal } from "lucide-react";

import { money } from "../shared.jsx";


const humanLabel = (value) => value.replaceAll("_", " ").replace(/\b[a-z]/g, (letter) => letter.toUpperCase());


export default function ScoreChart({ rows, categories, onOpenAttack }) {
	const maxSuccess = Math.max(1, ...rows.map((row) => row.successes || 0));
	return (
		<>
			<div className="score-summary">
				{[
					{ label: "Setups tested", value: rows.length, icon: SlidersHorizontal },
					{ label: "Tests run", value: rows.reduce((sum, row) => sum + row.total, 0), icon: FlaskConical },
					{ label: "Sent to risky payees", value: money(rows.reduce((sum, row) => sum + row.money_lost, 0)), icon: Banknote },
				].map(({ label, value, icon: Icon }) => (
					<div className="score-metric" key={label}>
						<div className="score-metric-icon"><Icon size={17} /></div><span>{label}</span><strong>{value}</strong>
					</div>
				))}
			</div>
			<section className="chart-panel">
				<div className="chart-panel-head">
					<div><h2>Which tests got through?</h2><p>Each bar shows how many runs led to an unsafe result.</p></div>
					<span className="chart-legend"><i /> Unsafe results</span>
				</div>
				{rows.length ? <div className="bar-chart">{rows.map((row) => (
					<div className="bar-row" key={row.config}>
						<span>{humanLabel(row.config)}</span>
						<div className="bar-track"><div className="bar-fill" style={{ width: `${Math.max(2, (row.successes / maxSuccess) * 100)}%` }} /></div>
						<strong>{row.successes} <small>/ {row.total}</small></strong>
						<span className="bar-loss">{money(row.money_lost)} lost</span>
					</div>
				))}</div> : <div className="score-empty">
					<div className="score-empty-icon"><Gauge size={23} /></div>
					<h3>No test runs yet</h3>
					<p>Try a few requests and the results will show up here. Only real runs count.</p>
					<button className="button button-outline" onClick={onOpenAttack}>
						<FlaskConical size={15} /> Try a test
					</button>
				</div>}
				<div className="honesty-note"><BookOpen size={15} /><span>The assistant can answer differently each time. This chart counts what the test actually did, not just what it said.</span></div>
			</section>
			<section className="chart-panel category-panel">
				<div className="chart-panel-head">
					<div><h2>What kind of request was it?</h2><p>See which types of tests were stopped and which got through.</p></div>
					<span className="category-count">{new Set(categories.map((row) => row.category)).size} types</span>
				</div>
				{categories.length ? <div className="category-chart">{categories.map((row) => (
					<div className="category-row" key={`${row.config}-${row.category}`}>
						<div className="category-name"><strong>{humanLabel(row.category)}</strong><span>{humanLabel(row.config)}</span></div>
						<div className="bar-track"><div className="bar-fill" style={{ width: `${Math.max(2, (row.successes / row.total) * 100)}%` }} /></div>
						<strong className="category-rate">{row.successes}<small> / {row.total}</small></strong>
						<span className="bar-loss">{money(row.money_lost)} lost</span>
					</div>
				))}</div> : <div className="category-empty">Run a few tests to compare results by request type.</div>}
			</section>
		</>
	);
}