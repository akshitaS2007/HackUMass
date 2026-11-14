import React from "react";
import { Activity, ArrowUpRight, Check, FlaskConical, LockKeyhole, Shield, ShieldAlert, ShieldCheck, X } from "lucide-react";

import { PageHeading, TEST_PROMPTS, money } from "../shared.jsx";


export default function AttackModePage({ text, setText, onRun, result, pipeline, count, busy }) {
	const blocked = result && !result.success;
	return (
		<div className="standard-page">
			<PageHeading
				eyebrow="CONTROLLED RED-TEAM EXERCISE"
				title="Attack mode"
				description="Probe the demo assistant. Runs use fictional funds and are recorded against this sandbox account."
				aside={<div className="attempt-counter"><span>ATTEMPTS</span><strong>{String(count).padStart(2, "0")}</strong></div>}
			/>
			<div className="attack-grid">
				<section className="attack-console">
					<div className="console-head">
						<div><span className="console-indicator" /> LIVE TEST CONSOLE</div>
						<span><LockKeyhole size={12} /> SANDBOX ONLY</span>
					</div>
					<div className="attack-form">
						<label htmlFor="attack-input">TEST PROMPT</label>
						<textarea id="attack-input" value={text} onChange={(event) => setText(event.target.value)} rows={4} maxLength={2000} />
						<div className="attack-form-foot">
							<span>{text.length} / 2,000 characters</span>
							<button className="button button-dark" onClick={() => onRun()} disabled={busy || !text.trim()}>
								{busy ? <><Activity size={15} className="spin" /> Reviewing</> : <><FlaskConical size={15} /> Run test</>}
							</button>
						</div>
					</div>
					<div className="prompt-library">
						<div className="section-label">QUICK TESTS <span>SELECT TO LOAD</span></div>
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
					<div className="result-head"><span className="section-label">LATEST RESULT</span><span className="result-live">● LIVE</span></div>
					{result ? (
						<div className={`result-state ${blocked ? "stopped" : "breached"}`}>
							<div className="result-symbol">{blocked ? <ShieldCheck size={25} /> : <ShieldAlert size={25} />}</div>
							<span className="result-kicker">{blocked ? "ATTEMPT BLOCKED" : "ACTION EXECUTED"}</span>
							<h2>{blocked ? "The guard held." : "Funds moved."}</h2>
							<p>{blocked ? "No money left the sandbox account on this run." : "A sandbox transfer completed. Reset the demo to restore the starting balance."}</p>
							<div className="money-loss"><span>MONEY LOST</span><strong className={blocked ? "" : "loss"}>{money(result.money_lost)}</strong></div>
						</div>
					) : (
						<div className="result-empty">
							<div className="empty-rings"><Shield size={28} /></div>
							<strong>Waiting for a test</strong>
							<span>Submit a prompt to see what the active defenses do.</span>
						</div>
					)}
					<div className="attack-pipeline">
						<div className="section-label">PIPELINE TRACE</div>
						{pipeline.length ? pipeline.map((step, index) => {
							const stopped = ["blocked", "deny"].includes(step.decision);
							const muted = ["skipped", "no_action"].includes(step.decision);
							return (
								<div className="trace-line" key={`${step.layer}-${index}`}>
									<span className={`trace-mark ${stopped ? "red" : muted ? "muted" : "green"}`}>{stopped ? <X size={12} /> : muted ? "–" : <Check size={12} />}</span>
									<div><strong>{step.layer.replaceAll("_", " ")}</strong><span>{step.reason}</span></div>
								</div>
							);
						}) : <div className="trace-placeholder">A new trace appears here after each test.</div>}
					</div>
				</aside>
			</div>
		</div>
	);
}