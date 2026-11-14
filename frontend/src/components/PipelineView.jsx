import React from "react";
import { BadgeCheck, Banknote, Check, Clock3, ShieldAlert, ShieldCheck, X } from "lucide-react";

import { LAYER_INFO } from "../shared.jsx";


export default function PipelineView({ pipeline, payees }) {
	const blocked = pipeline.some((step) => ["blocked", "deny"].includes(step.decision));
	return (
		<aside className="chat-rail">
			<div className="rail-heading">
				<div><span className="section-label">LIVE PIPELINE</span><p>Every proposal is reviewed.</p></div>
				<div className={`pipeline-status ${blocked ? "blocked" : pipeline.length ? "passed" : "idle"}`}>
					{blocked ? <><ShieldAlert size={14} /> STOPPED</> : pipeline.length ? <><ShieldCheck size={14} /> CHECKED</> : <><Clock3 size={14} /> WAITING</>}
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
							<div className="pipeline-arrow">{result ? result.decision.toUpperCase() : "—"}</div>
						</div>
					);
				})}
				<div className={`pipeline-step ${pipeline.some((step) => step.layer === "executor") ? "executed" : "pending"}`}>
					<div className="layer-node executor">{pipeline.some((step) => step.decision === "executed") ? <Check size={13} /> : <Banknote size={13} />}</div>
					<div className="pipeline-step-copy">
						<strong>Sandbox executor</strong>
						<span>{pipeline.find((step) => step.layer === "executor")?.reason || "No funds move until every required check passes."}</span>
					</div>
					<div className="pipeline-arrow">{pipeline.find((step) => step.layer === "executor")?.decision?.toUpperCase() || "—"}</div>
				</div>
			</div>
			<div className="payee-box">
				<div className="section-label">SAVED PAYEES <span>{payees.length}</span></div>
				{payees.slice(0, 4).map((payee) => (
					<div className="payee-line" key={payee.id}>
						<span className="payee-avatar">{payee.name.slice(0, 1)}</span>
						<span>{payee.name}</span>
						{payee.approved ? <BadgeCheck size={14} className="payee-approved" /> : <span className="pending-tag">NEW</span>}
					</div>
				))}
			</div>
			<div className="rail-footnote"><ShieldCheck size={15} /><span><strong>Actions are not autonomous.</strong> The agent proposes. Code decides. Then, if needed, you approve.</span></div>
		</aside>
	);
}