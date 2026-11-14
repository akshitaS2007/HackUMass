import React from "react";

import AccountPanel from "../components/AccountPanel.jsx";
import ChatBox from "../components/ChatBox.jsx";
import PipelineView from "../components/PipelineView.jsx";
import { PageHeading } from "../shared.jsx";


export default function ChatPage({
	account,
	transactions,
	payees,
	chat,
	pipeline,
	assistantMode,
	sandboxMode,
	busy,
	onSend,
}) {
	return (
		<div className="chat-page">
			<PageHeading
				eyebrow="ACCOUNT ASSISTANT"
				title="Money, with guardrails."
				description="Ask about your account or prepare a transfer. Every action is checked before it moves."
				aside={<div className="session-chip"><span className="status-dot" /> SESSION VERIFIED</div>}
			/>
			<div className="chat-layout">
				<section className="chat-column">
					<AccountPanel account={account} transactions={transactions} sandboxMode={sandboxMode} />
					<ChatBox chat={chat} assistantMode={assistantMode} busy={busy} onSend={onSend} />
				</section>
				<PipelineView pipeline={pipeline} payees={payees} />
			</div>
		</div>
	);
}