import React from "react";
import { Check, Fingerprint, LockKeyhole, ShieldAlert, X } from "lucide-react";

import { money } from "../shared.jsx";


export default function ConfirmModal({ pending, busy, onResolve }) {
	const addingPayee = pending.type === "add_payee";
	return (
		<div className="modal-backdrop">
			<section className="confirm-dialog" role="dialog" aria-modal="true" aria-labelledby="confirm-title">
				<div className="confirm-icon"><Fingerprint size={22} /></div>
				<span className="eyebrow">HUMAN ACTION REQUIRED</span>
				<h2 id="confirm-title">{addingPayee ? "Add this destination?" : "Confirm this transfer?"}</h2>
				<p>{addingPayee ? `Add ${pending.name} as a new, unverified payee?` : `Send ${money(pending.amount)} to ${pending.payee}?`}</p>
				<div className="confirm-reason"><ShieldAlert size={15} /><span>{pending.reason || (addingPayee ? "New destinations always require a separate confirmation." : "This action needs your explicit approval.")}</span></div>
				<div className="confirm-actions">
					<button className="button button-quiet" onClick={() => onResolve(false)} disabled={busy}><X size={15} /> Cancel</button>
					<button className="button button-dark" onClick={() => onResolve(true)} disabled={busy}><Check size={15} /> Confirm action</button>
				</div>
				<span className="confirm-footnote"><LockKeyhole size={12} /> Only your click can authorize this step.</span>
			</section>
		</div>
	);
}