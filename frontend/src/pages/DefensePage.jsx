import React from "react";
import { CircleAlert, LockKeyhole, ShieldCheck } from "lucide-react";

import DefenseToggle from "../components/DefenseToggle.jsx";
import { LAYER_INFO, PageHeading, money } from "../shared.jsx";


export default function DefensePage({ defenses, locked, account, saving, sandboxMode, onToggle }) {
	const description = sandboxMode === "nessie"
		? "In Nessie mode, these checks stay on and every payment needs your approval."
		: "Choose which checks to use. Your changes apply to the next request.";

	return (
		<div className="standard-page">
			<PageHeading
				eyebrow="Your safety settings"
				title="How careful should BTB be?"
				description={description}
				aside={<div className="balance-mini"><span>LIVE BALANCE</span><strong>{money(account?.balance)}</strong></div>}
			/>
			<div className="defense-layout">
				<div className="defense-list">
					{LAYER_INFO.map((layer) => (
						<DefenseToggle
							key={layer.id}
							layer={layer}
							enabled={!!defenses[layer.id]}
							required={locked.includes(layer.id)}
							saving={saving}
							onToggle={onToggle}
						/>
					))}
				</div>
				<aside className="policy-aside">
					<div className="policy-aside-head"><LockKeyhole size={17} /><span>Always on</span></div>
					<h3>Some limits can’t be switched off.</h3>
					<p>These checks run in code, not in the AI assistant.</p>
					<div className="policy-rule"><span>One payment</span><strong>Up to $200</strong></div>
					<div className="policy-rule"><span>Per day</span><strong>Up to $500</strong></div>
					<div className="policy-rule"><span>In one minute</span><strong>5 payments</strong></div>
					<div className="policy-rule"><span>New payee</span><strong>Needs your OK</strong></div>
					<div className="policy-note"><CircleAlert size={15} /><span>Try turning checks off only in the demo. They’re saved for this account until you change them back.</span></div>
				</aside>
			</div>
			<div className="defense-footer">
				<ShieldCheck size={16} /><span>{saving ? "Saving your settings…" : "These settings apply to this demo account."}</span>
			</div>
		</div>
	);
}