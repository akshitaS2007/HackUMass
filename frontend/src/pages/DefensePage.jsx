import React from "react";
import { CircleAlert, LockKeyhole, ShieldCheck } from "lucide-react";

import DefenseToggle from "../components/DefenseToggle.jsx";
import { LAYER_INFO, PageHeading, money } from "../shared.jsx";


export default function DefensePage({ defenses, locked, account, saving, sandboxMode, onToggle }) {
	const description = sandboxMode === "nessie"
		? "Every Nessie sandbox transfer requires your approval. Hard rules and confirmation controls stay locked."
		: "Toggle each layer independently. Changes apply immediately to the next request.";

	return (
		<div className="standard-page">
			<PageHeading
				eyebrow="POLICY CONFIGURATION"
				title="Defense controls"
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
					<div className="policy-aside-head"><LockKeyhole size={17} /><span>FIXED POLICY</span></div>
					<h3>Code has the final say.</h3>
					<p>These controls are enforced by the backend, independently of model output.</p>
					<div className="policy-rule"><span>Single transfer</span><strong>$200 max</strong></div>
					<div className="policy-rule"><span>Daily outbound</span><strong>$500 max</strong></div>
					<div className="policy-rule"><span>Transfer velocity</span><strong>5 / minute</strong></div>
					<div className="policy-rule"><span>New payee</span><strong>Approval required</strong></div>
					<div className="policy-note"><CircleAlert size={15} /><span>Use disabled layers only for controlled demos. Toggle states are saved per account until changed.</span></div>
				</aside>
			</div>
			<div className="defense-footer">
				<ShieldCheck size={16} /><span>{saving ? "Saving defense settings…" : "Settings are account-scoped and recorded with every security decision."}</span>
			</div>
		</div>
	);
}