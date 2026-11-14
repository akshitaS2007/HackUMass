import React from "react";

export default function DefenseToggle({ layer, enabled, required, saving, onToggle }) {
	const details = layer.id === "hard_rules"
		? "$200 max · $500 daily · 5 actions/min"
		: layer.id === "human_confirm"
			? "Required for transfers above $100 and new destinations"
			: layer.id === "guardian"
				? "Separate review context · fail closed if response is invalid"
				: "Pattern-based screen · not a complete security boundary";

	return (
		<div className={`defense-row ${enabled ? "enabled" : "disabled"}`}>
			<div className={`layer-token ${layer.color}`}>{layer.layer}</div>
			<div className="defense-copy">
				<div className="defense-title-line">
					<h3>{layer.name}</h3>
					<span className={`state-tag ${enabled ? "on" : "off"}`}>{required ? "LOCKED ON" : enabled ? "ACTIVE" : "DISABLED"}</span>
				</div>
				<p>{layer.detail}</p>
				<small>{details}</small>
			</div>
			<button
				role="switch"
				aria-checked={enabled}
				aria-label={`${layer.name} ${required ? "required" : enabled ? "enabled" : "disabled"}`}
				title={required ? "This layer cannot be disabled in Nessie mode." : undefined}
				className={`switch ${enabled ? "on" : ""}`}
				disabled={saving || required}
				onClick={() => onToggle(layer.id, !enabled)}
			>
				<span />
			</button>
		</div>
	);
}