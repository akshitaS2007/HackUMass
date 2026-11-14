import React, { useState } from "react";
import { LockKeyhole, Send, Sparkles } from "lucide-react";


function ChatComposer({ disabled, onSend }) {
	const [value, setValue] = useState("");

	function submit(event) {
		event.preventDefault();
		if (!value.trim()) return;
		onSend(value);
		setValue("");
	}

	return (
		<form className="composer" onSubmit={submit}>
			<textarea
				value={value}
				onChange={(event) => setValue(event.target.value)}
				onKeyDown={(event) => {
					if (event.key === "Enter" && !event.shiftKey) {
						event.preventDefault();
						submit(event);
					}
				}}
				placeholder="Try: Pay my electric bill $80"
				aria-label="Message the banking assistant"
				rows={1}
				disabled={disabled}
			/>
			<button className="send-button" type="submit" disabled={disabled || !value.trim()} title="Send message">
				<Send size={16} />
			</button>
		</form>
	);
}


export default function ChatBox({ chat, assistantMode, busy, onSend }) {
	const usesGemini = assistantMode?.provider === "gemini";
	const modeTitle = usesGemini
		? `Gemini is configured (${assistantMode.model}). Agent, guardian, and explainer use Gemini when requests succeed.`
		: "Using the deterministic local assistant and reviewer; no Gemini key is configured.";

	return (
		<div className="chat-card">
			<div className="chat-card-head">
				<div className="assistant-identity">
					<div className="assistant-icon"><Sparkles size={16} /></div>
					<div><strong>Banking assistant</strong><span>Connected to your demo account</span></div>
				</div>
				<span className="model-pill" title={modeTitle}>
					<span />{usesGemini ? `GEMINI · ${assistantMode.model || "CONFIGURED"}` : assistantMode ? "LOCAL · READY" : "CHECKING"}
				</span>
			</div>
			<div className="message-list">
				{chat.map((item, index) => (
					<div className={`message-row ${item.role}`} key={`${index}-${item.role}`}>
						<div className="message-avatar">{item.role === "assistant" ? <Sparkles size={15} /> : "Y"}</div>
						<div className="message-content">
							<span className="message-author">{item.role === "assistant" ? "ASSISTANT" : "YOU"}</span>
							<p>{item.text}</p>
						</div>
					</div>
				))}
				{busy && <div className="message-row assistant"><div className="message-avatar"><Sparkles size={15} /></div><div className="typing"><i /><i /><i /></div></div>}
			</div>
			<ChatComposer disabled={busy} onSend={onSend} />
			<div className="composer-hint"><LockKeyhole size={12} /> Every transfer passes through the policy engine.</div>
		</div>
	);
}