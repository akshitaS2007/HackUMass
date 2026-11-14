import React from "react";
import { ArrowDownLeft, ArrowUpRight } from "lucide-react";

import { money, shortDate } from "../shared.jsx";


export default function AccountPanel({ account, transactions, sandboxMode }) {
	return (
		<>
			<div className="account-strip">
				<div className="balance-block">
					<span className="metric-label">AVAILABLE BALANCE</span>
					<strong>{money(account?.balance)}</strong>
					<span className="balance-caption">
						<span className="positive-tick"><ArrowDownLeft size={12} /></span>
						{sandboxMode === "nessie" ? "Nessie fake-money sandbox" : "Fictional sandbox funds"}
					</span>
				</div>
				<div className="account-meta">
					<div><span>ACCOUNT TYPE</span><strong>{account?.label || "Everyday checking"}</strong></div>
					<div><span>ACCOUNT ID</span><strong>{account?.id || "--"}</strong></div>
					<div><span>TRANSFER LIMIT</span><strong>$200.00 <small>per transfer</small></strong></div>
				</div>
			</div>
			<div className="recent-row">
				<div className="section-label">RECENT ACTIVITY <span>{transactions.length} items</span></div>
				<div className="transaction-list">
					{transactions.slice(0, 4).map((transaction) => (
						<div className="transaction-item" key={transaction.id}>
							<div className="transaction-icon"><ArrowUpRight size={15} /></div>
							<div className="transaction-name">
								<strong>{transaction.description}</strong>
								<span>{shortDate(transaction.created_at)}</span>
							</div>
							<strong className={transaction.amount < 0 ? "amount-negative" : ""}>{money(Math.abs(transaction.amount))}</strong>
						</div>
					))}
				</div>
			</div>
		</>
	);
}