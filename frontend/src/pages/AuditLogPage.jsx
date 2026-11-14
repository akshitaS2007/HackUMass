import React, { useState } from "react";
import { FileClock, LockKeyhole } from "lucide-react";

import { PageHeading } from "../shared.jsx";


export default function AuditLogPage({ events }) {
	const [filter, setFilter] = useState("all");
	const filtered = events.filter((event) => filter === "all" || event.layer === filter);
	const filters = ["all", "input_filter", "guardian", "hard_rules", "human_confirm", "explainer", "executor"];
	return (
		<div className="standard-page">
			<PageHeading
				eyebrow="TRANSPARENCY LOG"
				title="Audit trail"
				description="Every reviewed action is recorded with its layer, decision, and reason."
				aside={<div className="audit-count"><FileClock size={15} /> {events.length} EVENTS</div>}
			/>
			<div className="audit-toolbar">
				<div className="audit-tabs">
					{filters.map((item) => (
						<button key={item} className={filter === item ? "selected" : ""} onClick={() => setFilter(item)}>
							{item === "all" ? "All events" : item.replaceAll("_", " ")}
						</button>
					))}
				</div>
				<span><LockKeyhole size={13} /> ACCOUNT-SCOPED</span>
			</div>
			<div className="audit-table">
				<div className="audit-header"><span>TIME</span><span>LAYER</span><span>EVENT</span><span>DECISION</span><span>REASON</span></div>
				{filtered.length ? filtered.map((event) => {
					const negative = ["blocked", "deny", "cancelled"].includes(event.decision);
					const positive = ["executed", "approved", "passed", "complete"].includes(event.decision);
					return (
						<div className="audit-row" key={event.id}>
							<span className="audit-time">{new Date(event.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" })}</span>
							<span className="audit-layer">{event.layer.replaceAll("_", " ")}</span>
							<span>{event.event_type}</span>
							<span><i className={`decision-dot ${negative ? "red" : positive ? "green" : "gold"}`} />{event.decision}</span>
							<span className="audit-reason" title={event.reason}>{event.reason}</span>
						</div>
					);
				}) : <div className="audit-empty"><FileClock size={20} /><span>No events match this filter yet.</span></div>}
			</div>
		</div>
	);
}