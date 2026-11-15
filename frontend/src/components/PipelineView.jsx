import React from "react";
import { BadgeCheck, Banknote, Check, Clock3, ShieldAlert, ShieldCheck, X } from "lucide-react";

import { LAYER_INFO } from "../shared.jsx";


export default function PipelineView({ pipeline, payees }) {
	const blocked = pipeline.some((step) => ["blocked", "deny"].includes(step.decision));
	const executor = pipeline.find((step) => step.layer === "executor");
	const decisionName = (decision) => ({
		passed: "Checked",
		approved: "Approved",
		executed: "Sent",
		blocked: "Stopped",
		deny: "Stopped",
		skipped: "Not needed",
		no_action: "No payment",
	}[decision] || decision.replaceAll("_", " "));
	return (
		<aside className="chat-rail">
			<div className="rail-heading">
				<div><span className="section-label">Before a payment goes through</span><p>Here’s what the checks are doing.</p></div>
				<div className={`pipeline-status ${blocked ? "blocked" : pipeline.length ? "passed" : "idle"}`}>
					{blocked ? <><ShieldAlert size={14} /> Stopped</> : pipeline.length ? <><ShieldCheck size={14} /> Checked</> : <><Clock3 size={14} /> Waiting</>}
				</div>
			</div>
			<div className="pipeline-list">
				{LAYER_INFO.map((layer) => {
					const result = pipeline.find((step) => step.layer === layer.id);
					const approved = result && ["passed", "approved", "executed"].includes(result.decision);
					return (
						<div className={`pipeline-step ${result ? result.decision : "pending"}`} key={layer.id}>
							<div className={`layer-node ${layer.color}`}>
								{result ? approved ? <Check size={13} /> : result.decision === "skipped" ? <span>–</span> : <X size={13} /> : layer.layer}
							</div>
							<div className="pipeline-step-copy"><strong>{layer.name}</strong><span>{result?.reason || layer.detail}</span></div>
							<div className="pipeline-arrow">{result ? decisionName(result.decision) : "—"}</div>
						</div>
					);
				})}
				<div className={`pipeline-step ${pipeline.some((step) => step.layer === "executor") ? "executed" : "pending"}`}>
					<div className="layer-node executor">{pipeline.some((step) => step.decision === "executed") ? <Check size={13} /> : <Banknote size={13} />}</div>
					<div className="pipeline-step-copy">
						<strong>Demo payment</strong>
						<span>{executor?.reason || "Nothing moves until the required checks pass."}</span>
					</div>
					<div className="pipeline-arrow">{executor ? decisionName(executor.decision) : "—"}</div>
				</div>
			</div>
			<div className="payee-box">
				<div className="section-label">Your payees <span>{payees.length}</span></div>
				{payees.slice(0, 4).map((payee) => (
					<div className="payee-line" key={payee.id}>
						<span className="payee-avatar">{payee.name.slice(0, 1)}</span>
						<span>{payee.name}</span>
						{payee.approved ? <BadgeCheck size={14} className="payee-approved" /> : <span className="pending-tag">NEW</span>}
					</div>
				))}
			</div>
			<div className="rail-footnote"><ShieldCheck size={15} /><span><strong>You’re in control.</strong> The assistant can suggest a payment; it can’t approve one for you.</span></div>
		</aside>
	);
}