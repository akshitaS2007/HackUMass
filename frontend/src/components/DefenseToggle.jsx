import React from "react";

export default function DefenseToggle({ layer, enabled, required, saving, onToggle }) {
	const details = layer.id === "hard_rules"
		? "$200 at a time · $500 a day · 5 a minute"
		: layer.id === "human_confirm"
			? "We ask before payments over $100 or to new payees"
			: layer.id === "guardian"
				? "A separate review checks the proposed payment"
				: "Looks for suspicious instructions before they reach the assistant";

	return (
		<div className={`defense-row ${enabled ? "enabled" : "disabled"}`}>
			<div className={`layer-token ${layer.color}`}>{layer.layer}</div>
			<div className="defense-copy">
				<div className="defense-title-line">
					<h3>{layer.name}</h3>
					<span className={`state-tag ${enabled ? "on" : "off"}`}>{required ? "STAYS ON" : enabled ? "ON" : "OFF"}</span>
				</div>
				<p>{layer.detail}</p>
				<small>{details}</small>
			</div>
			<button
				role="switch"
				aria-checked={enabled}
				aria-label={`${layer.name} ${required ? "required" : enabled ? "enabled" : "disabled"}`}
				title={required ? "This check stays on in Nessie mode." : undefined}
				className={`switch ${enabled ? "on" : ""}`}
				disabled={saving || required}
				onClick={() => onToggle(layer.id, !enabled)}
			>
				<span />
			</button>
		</div>
	);
}