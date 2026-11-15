import React, { useState } from "react";
import { MessageCircle, Send, Sparkles, X } from "lucide-react";


export default function AssistantDock({ chat, busy, onSend }) {
	const [open, setOpen] = useState(false);
	const [draft, setDraft] = useState("");

	function submit(event) {
		event.preventDefault();
		if (!draft.trim() || busy) return;
		onSend(draft);
		setDraft("");
	}

	return (
		<div className={`assistant-dock ${open ? "open" : ""}`}>
			{open && (
				<section className="assistant-dock-panel" role="dialog" aria-label="Ask the assistant">
					<header className="assistant-dock-head">
						<div className="assistant-dock-avatar"><Sparkles size={16} /></div>
						<div><strong>Ask BTB</strong><span>Questions, transfers, or what just happened.</span></div>
						<button className="dock-close" aria-label="Close assistant" onClick={() => setOpen(false)}><X size={17} /></button>
					</header>
					<div className="assistant-dock-messages" aria-live="polite">
						{chat.slice(-5).map((message, index) => (
							<div className={`dock-message ${message.role}`} key={`${message.role}-${index}`}>
								<span>{message.role === "assistant" ? "BTB" : "YOU"}</span>
								<p>{message.text}</p>
							</div>
						))}
						{busy && <div className="dock-thinking"><i /><i /><i /> BTB is thinking</div>}
					</div>
					<form className="assistant-dock-form" onSubmit={submit}>
						<textarea
							value={draft}
							onChange={(event) => setDraft(event.target.value)}
							onKeyDown={(event) => {
								if (event.key === "Enter" && !event.shiftKey) {
									event.preventDefault();
									submit(event);
								}
							}}
							placeholder="Ask something..."
							aria-label="Ask BTB a question"
							rows={1}
							disabled={busy}
						/>
						<button type="submit" aria-label="Send message" disabled={busy || !draft.trim()}><Send size={16} /></button>
					</form>
				</section>
			)}
			<button
				className="assistant-dock-trigger"
				aria-label={open ? "Close Ask BTB" : "Ask BTB"}
				aria-expanded={open}
				onClick={() => setOpen((value) => !value)}
			>
				{open ? <X size={18} /> : <MessageCircle size={18} />}
				<span>{open ? "Close" : "Ask BTB"}</span>
			</button>
		</div>
	);
}
