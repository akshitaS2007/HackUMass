import React from "react";
import { Activity, ArrowUpRight, Check, FlaskConical, LockKeyhole, Shield, ShieldAlert, ShieldCheck, X } from "lucide-react";

import { LAYER_INFO, PageHeading, TEST_PROMPTS, money } from "../shared.jsx";


const layerName = (id) => LAYER_INFO.find((layer) => layer.id === id)?.name || (id === "executor" ? "Demo payment" : id.replaceAll("_", " "));
const decisionName = (decision) => ({
	passed: "Checked",
	approved: "Approved",
	executed: "Sent",
	blocked: "Stopped",
	deny: "Stopped",
	skipped: "Not needed",
	no_action: "No payment",
}[decision] || decision.replaceAll("_", " "));


export default function AttackModePage({ text, setText, onRun, result, pipeline, count, busy }) {
	const blocked = result && !result.success;
	return (
		<div className="standard-page">
			<PageHeading
				eyebrow="Safe to try"
				title="Try to break it."
				description="Try an override or an unusual request. We’ll show which checks catch it. Everything here uses demo money."
				aside={<div className="attempt-counter"><span>YOUR RUNS</span><strong>{String(count).padStart(2, "0")}</strong></div>}
			/>
			<div className="attack-grid">
				<section className="attack-console">
					<div className="console-head">
						<div><span className="console-indicator" /> Your test</div>
						<span><LockKeyhole size={12} /> Demo only</span>
					</div>
					<div className="attack-form">
						<label htmlFor="attack-input">What should we try?</label>
						<textarea id="attack-input" value={text} onChange={(event) => setText(event.target.value)} rows={4} maxLength={2000} />
						<div className="attack-form-foot">
							<span>{text.length} / 2,000 characters</span>
							<button className="button button-dark" onClick={() => onRun()} disabled={busy || !text.trim()}>
								{busy ? <><Activity size={15} className="spin" /> Checking…</> : <><FlaskConical size={15} /> Try it</>}
							</button>
						</div>
					</div>
					<div className="prompt-library">
						<div className="section-label">Need an idea? <span>Pick one</span></div>
						<div className="test-prompt-list">
							{TEST_PROMPTS.map((prompt, index) => (
								<button key={prompt} onClick={() => setText(prompt)}>
									<span>0{index + 1}</span><span>{prompt}</span><ArrowUpRight size={14} />
								</button>
							))}
						</div>
					</div>
				</section>
				<aside className="attack-result-panel">
					<div className="result-head"><span className="section-label">What happened</span><span className="result-live">Just now</span></div>
					{result ? (
						<div className={`result-state ${blocked ? "stopped" : "breached"}`}>
							<div className="result-symbol">{blocked ? <ShieldCheck size={25} /> : <ShieldAlert size={25} />}</div>
							<span className="result-kicker">{blocked ? "STOPPED" : "IT WENT THROUGH"}</span>
							<h2>{blocked ? "That check caught it." : "The request got through."}</h2>
							<p>{blocked ? "No money moved on this run." : "A demo payment went through. Start over to restore the balance."}</p>
							<div className="money-loss"><span>Sent to an unapproved payee</span><strong className={blocked ? "" : "loss"}>{money(result.money_lost)}</strong></div>
						</div>
					) : (
						<div className="result-empty">
							<div className="empty-rings"><Shield size={28} /></div>
							<strong>Nothing tested yet</strong>
							<span>Try a request on the left to see what happens.</span>
						</div>
					)}
					<div className="attack-pipeline">
						<div className="section-label">Checks along the way</div>
						{pipeline.length ? pipeline.map((step, index) => {
							const stopped = ["blocked", "deny"].includes(step.decision);
							const muted = ["skipped", "no_action"].includes(step.decision);
							return (
								<div className="trace-line" key={`${step.layer}-${index}`}>
									<span className={`trace-mark ${stopped ? "red" : muted ? "muted" : "green"}`}>{stopped ? <X size={12} /> : muted ? "–" : <Check size={12} />}</span>
									<div><strong>{layerName(step.layer)} · {decisionName(step.decision)}</strong><span>{step.reason}</span></div>
								</div>
							);
						}) : <div className="trace-placeholder">The checks will show up here after a run.</div>}
					</div>
				</aside>
			</div>
		</div>
	);
}