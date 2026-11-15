import React, { useState } from "react";
import { FileClock, LockKeyhole } from "lucide-react";

import { LAYER_INFO, PageHeading } from "../shared.jsx";


export default function AuditLogPage({ events }) {
	const [filter, setFilter] = useState("all");
	const filtered = events.filter((event) => filter === "all" || event.layer === filter);
	const filters = [
		{ id: "all", label: "Everything" },
		...LAYER_INFO.map((layer) => ({ id: layer.id, label: layer.name })),
		{ id: "explainer", label: "Explanation" },
		{ id: "executor", label: "Demo payment" },
		{ id: "output_guard", label: "Answer check" },
		{ id: "system", label: "Demo setup" },
	];
	const readable = (value) => value.replaceAll("_", " ");
	return (
		<div className="standard-page">
			<PageHeading
				eyebrow="A clear record"
				title="What happened, when?"
				description="See each check, what it decided, and why. These entries come from this demo account."
				aside={<div className="audit-count"><FileClock size={15} /> {events.length} events</div>}
			/>
			<div className="audit-toolbar">
				<div className="audit-tabs">
					{filters.map((item) => (
						<button key={item.id} className={filter === item.id ? "selected" : ""} onClick={() => setFilter(item.id)}>
							{item.label}
						</button>
					))}
				</div>
				<span><LockKeyhole size={13} /> THIS ACCOUNT</span>
			</div>
			<div className="audit-table">
				<div className="audit-header"><span>Time</span><span>Check</span><span>What happened</span><span>Decision</span><span>Why</span></div>
				{filtered.length ? filtered.map((event) => {
					const negative = ["blocked", "deny", "cancelled"].includes(event.decision);
					const positive = ["executed", "approved", "passed", "complete"].includes(event.decision);
					return (
						<div className="audit-row" key={event.id}>
							<span className="audit-time">{new Date(event.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" })}</span>
							<span className="audit-layer">{readable(event.layer)}</span>
							<span>{readable(event.event_type)}</span>
							<span><i className={`decision-dot ${negative ? "red" : positive ? "green" : "gold"}`} />{readable(event.decision)}</span>
							<span className="audit-reason" title={event.reason}>{event.reason}</span>
						</div>
					);
				}) : <div className="audit-empty"><FileClock size={20} /><span>No events match this filter yet.</span></div>}
			</div>
		</div>
	);
}