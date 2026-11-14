import React, { useEffect, useState } from "react";
import {
	Activity, ArrowUpRight, CircleAlert, FileClock, FlaskConical, Gauge,
	LockKeyhole, LogOut, MessageSquareText, RotateCcw, Shield, ShieldCheck,
	SlidersHorizontal, X,
} from "lucide-react";

import { api, post, setToken } from "./api.js";
import AttackModePage from "./pages/AttackModePage.jsx";
import AuditLogPage from "./pages/AuditLogPage.jsx";
import ChatPage from "./pages/ChatPage.jsx";
import DefensePage from "./pages/DefensePage.jsx";
import ScoreboardPage from "./pages/ScoreboardPage.jsx";
import ConfirmModal from "./components/ConfirmModal.jsx";
import { PageHeading, TEST_PROMPTS } from "./shared.jsx";


const NAV_ITEMS = [
	{ id: "chat", label: "Assistant", icon: MessageSquareText },
	{ id: "defenses", label: "Defense controls", icon: SlidersHorizontal },
	{ id: "attack", label: "Attack mode", icon: FlaskConical },
	{ id: "scoreboard", label: "Scoreboard", icon: Gauge },
	{ id: "audit", label: "Audit trail", icon: FileClock },
];


export default function App() {
	const [users, setUsers] = useState([]);
	const [assistantMode, setAssistantMode] = useState(null);
	const [sandboxMode, setSandboxMode] = useState("mock");
	const [user, setUser] = useState(null);
	const [account, setAccount] = useState(null);
	const [transactions, setTransactions] = useState([]);
	const [payees, setPayees] = useState([]);
	const [defenses, setDefenses] = useState({});
	const [lockedDefenses, setLockedDefenses] = useState([]);
	const [events, setEvents] = useState([]);
	const [scoreboard, setScoreboard] = useState([]);
	const [scoreboardCategories, setScoreboardCategories] = useState([]);
	const [view, setView] = useState("chat");
	const [busy, setBusy] = useState(false);
	const [savingDefense, setSavingDefense] = useState(false);
	const [error, setError] = useState("");
	const [chat, setChat] = useState([{ role: "assistant", text: "Good morning. I can check your balance, review recent activity, or prepare a transfer to a saved payee." }]);
	const [pipeline, setPipeline] = useState([]);
	const [pending, setPending] = useState(null);
	const [attackText, setAttackText] = useState(TEST_PROMPTS[0]);
	const [attackResult, setAttackResult] = useState(null);
	const [attackCount, setAttackCount] = useState(0);
	const [lastUpdated, setLastUpdated] = useState(null);

	async function refresh() {
		const [accountData, defenseData, eventData, scoreData] = await Promise.all([
			api("/account"), api("/defenses"), api("/events"), api("/scoreboard"),
		]);
		setAccount(accountData.account);
		setTransactions(accountData.transactions || []);
		setPayees(accountData.payees || []);
		setDefenses(defenseData.defenses || {});
		setLockedDefenses(defenseData.locked || []);
		setEvents(eventData.events || []);
		setScoreboard(scoreData.results || []);
		setScoreboardCategories(scoreData.categories || []);
		setLastUpdated(new Date());
	}

	useEffect(() => {
		Promise.all([api("/users"), api("/health")]).then(([data, health]) => {
			setUsers(data.users || []);
			setAssistantMode(health.ai || null);
			setSandboxMode(health.nessie?.mode || "mock");
			const saved = localStorage.getItem("bb_user");
			if (saved && localStorage.getItem("bb_access_token")) {
				const match = data.users?.find((item) => item.id === saved);
				if (match) {
					refresh().then(() => setUser(match)).catch(() => {
						setToken("");
						localStorage.removeItem("bb_user");
						setUser(null);
					});
				}
			}
		}).catch((exception) => setError(exception.message));
	}, []);

	async function chooseUser(userId) {
		setBusy(true);
		setError("");
		try {
			const result = await post("/login", { user_id: userId });
			setToken(result.access_token);
			try {
				await refresh();
			} catch (exception) {
				setToken("");
				localStorage.removeItem("bb_user");
				throw exception;
			}
			localStorage.setItem("bb_user", userId);
			setUser(result.user);
			setChat([{ role: "assistant", text: `Welcome, ${result.user.name.split(" ")[0]}. Your sandbox account is ready.` }]);
		} catch (exception) {
			setError(exception.message);
		} finally {
			setBusy(false);
		}
	}

	function signOut() {
		setToken("");
		localStorage.removeItem("bb_user");
		setUser(null);
		setAccount(null);
		setPending(null);
		setPipeline([]);
	}

	async function sendMessage(message) {
		if (!message.trim() || busy) return;
		setBusy(true);
		setError("");
		setChat((items) => [...items, { role: "user", text: message.trim() }]);
		try {
			const result = await post("/chat", { message: message.trim() });
			setChat((items) => [...items, { role: "assistant", text: result.reply }]);
			setPipeline(result.pipeline || []);
			setPending(result.pending_action || null);
			if (result.account) setAccount(result.account);
			await refresh();
		} catch (exception) {
			setError(exception.message);
		} finally {
			setBusy(false);
		}
	}

	async function resolvePending(approved) {
		if (!pending) return;
		setBusy(true);
		try {
			const result = await post(`/confirm/${pending.id}`, { approved });
			setChat((items) => [...items, { role: "assistant", text: result.reply }]);
			setPending(null);
			if (result.account) setAccount(result.account);
			await refresh();
		} catch (exception) {
			setError(exception.message);
			if (sandboxMode === "nessie") setPending(null);
		} finally {
			setBusy(false);
		}
	}

	async function toggleDefense(key, enabled) {
		if (savingDefense) return;
		const next = { ...defenses, [key]: enabled };
		setSavingDefense(true);
		setError("");
		try {
			const result = await post("/defenses", next);
			setDefenses(result.defenses);
		} catch (exception) {
			setError(exception.message);
			try {
				const result = await api("/defenses");
				setDefenses(result.defenses || {});
				setLockedDefenses(result.locked || []);
			} catch {
				setError(`${exception.message} The saved defense settings could not be reloaded.`);
			}
		} finally {
			setSavingDefense(false);
		}
	}

	async function resetDemo() {
		setBusy(true);
		setError("");
		try {
			const result = await post("/reset");
			setAccount(result.account);
			setPending(null);
			setAttackResult(null);
			setChat([{ role: "assistant", text: "Sandbox reset. Your demo balance and transfer history are back to their starting state." }]);
			setPipeline([]);
			await refresh();
		} catch (exception) {
			setError(exception.message);
		} finally {
			setBusy(false);
		}
	}

	async function runAttack(message = attackText) {
		if (!message.trim() || busy) return;
		setBusy(true);
		setError("");
		setAttackResult(null);
		try {
			const result = await post("/attack", { attack_id: `live-${Date.now()}`, message: message.trim() });
			setAttackResult(result.attack_result);
			setAttackCount((count) => count + 1);
			setPipeline(result.pipeline || []);
			if (result.account) setAccount(result.account);
			await refresh();
		} catch (exception) {
			setError(exception.message);
		} finally {
			setBusy(false);
		}
	}

	if (!user) return <LoginScreen users={users} onChoose={chooseUser} busy={busy} error={error} />;

	return (
		<div className="app-shell">
			<aside className="sidebar">
				<div className="brand-lockup">
					<div className="brand-mark"><Shield size={20} strokeWidth={2.2} /></div>
					<div><span className="brand-name">break the bank</span><span className="brand-subtitle">AI SECURITY LAB</span></div>
				</div>
				<div className="workspace-label">WORKSPACE</div>
				<nav className="primary-nav" aria-label="Main navigation">
					{NAV_ITEMS.map(({ id, label, icon: Icon }) => (
						<button key={id} aria-label={label} title={label} className={`nav-item ${view === id ? "active" : ""}`} onClick={() => setView(id)}>
							<Icon size={17} /><span>{label}</span>{id === "attack" && <span className="nav-live-dot" />}
						</button>
					))}
				</nav>
				<div className="sidebar-lower">
					<div className="sidebar-status"><span className="status-dot" /> SANDBOX ENVIRONMENT <span className="status-lock"><LockKeyhole size={12} /></span></div>
					<div className="sidebar-profile">
						<div className="avatar">{user.name.split(" ").map((part) => part[0]).join("")}</div>
						<div className="profile-copy"><strong>{user.name}</strong><span>Demo account</span></div>
						<button className="icon-button profile-menu" title="Sign out" onClick={signOut}><LogOut size={15} /></button>
					</div>
				</div>
			</aside>

			<main className="main-area">
				<header className="topbar">
					<div className="breadcrumb"><span>Security workspace</span><span className="crumb-slash">/</span><strong>{NAV_ITEMS.find((item) => item.id === view)?.label}</strong></div>
					<div className="topbar-actions">
						<div className="live-badge"><span /> {sandboxMode === "nessie" ? "NESSIE SANDBOX" : "LOCAL SANDBOX"}</div>
						<button
							className="button button-quiet reset-button"
							onClick={resetDemo}
							disabled={busy || sandboxMode === "nessie"}
							title={sandboxMode === "nessie" ? "A local reset cannot reverse an external Nessie transfer." : "Restore the local mock account"}
						>
							<RotateCcw size={15} /> {sandboxMode === "nessie" ? "Reset unavailable" : "Reset demo"}
						</button>
					</div>
				</header>
				{error && <div className="toast-error" role="alert"><CircleAlert size={16} />{error}<button onClick={() => setError("")} aria-label="Dismiss"><X size={15} /></button></div>}
				<div className="workspace-content">
					{view === "chat" && (
						<ChatPage
							account={account}
							transactions={transactions}
							payees={payees}
							chat={chat}
							pipeline={pipeline}
							assistantMode={assistantMode}
							sandboxMode={sandboxMode}
							busy={busy}
							onSend={sendMessage}
						/>
					)}
					{view === "defenses" && (
						<DefensePage
							defenses={defenses}
							locked={lockedDefenses}
							account={account}
							saving={savingDefense}
							sandboxMode={sandboxMode}
							onToggle={toggleDefense}
						/>
					)}
					{view === "attack" && (sandboxMode === "nessie"
						? <div className="standard-page">
							<PageHeading eyebrow="MOCK SANDBOX ONLY" title="Attack mode paused" description="Attack runs are disabled while Nessie is selected. External fake-money transfers cannot be rolled back safely." />
							<div className="policy-note"><LockKeyhole size={15} /><span>Switch the backend to NESSIE_MODE=mock to run the local red-team exercise.</span></div>
						</div>
						: <AttackModePage text={attackText} setText={setAttackText} onRun={runAttack} result={attackResult} pipeline={pipeline} count={attackCount} busy={busy} />
					)}
					{view === "scoreboard" && (
						<ScoreboardPage
							rows={scoreboard}
							categories={scoreboardCategories}
							lastUpdated={lastUpdated}
							onOpenAttack={() => setView("attack")}
						/>
					)}
					{view === "audit" && <AuditLogPage events={events} />}
				</div>
				<footer className="app-footer">
					<span><LockKeyhole size={12} /> {sandboxMode === "nessie" ? "Fake-money transfers use your configured Nessie sandbox." : "No real funds. Transfers stay inside this local sandbox."}</span>
					<span>POLICY ENGINE v1.0 <i /> {account?.id || "ACCOUNT"}</span>
				</footer>
			</main>
			{pending && <ConfirmModal pending={pending} busy={busy} onResolve={resolvePending} />}
		</div>
	);
}


function LoginScreen({ users, onChoose, busy, error }) {
	return (
		<main className="login-screen">
			<div className="login-left">
				<div className="brand-lockup">
					<div className="brand-mark"><Shield size={20} /></div>
					<div><span className="brand-name">break the bank</span><span className="brand-subtitle">AI SECURITY LAB</span></div>
				</div>
				<div className="login-copy">
					<div className="eyebrow"><span className="eyebrow-line" /> AGENTIC FINANCE, UNDER PRESSURE</div>
					<h1>Trust is a<br /><em>system.</em></h1>
					<p>A financial AI sandbox built to show where safeguards hold, where they fail, and what happens next.</p>
					<div className="login-proof"><span><ShieldCheck size={16} /> Four defense layers</span><span><Activity size={16} /> Live policy trace</span></div>
				</div>
				<div className="login-foot">HACKUMASS · SECURITY TRACK</div>
			</div>
			<div className="login-right">
				<div className="login-panel">
					<div className="panel-kicker">DEMO ENVIRONMENT <span className="status-dot" /></div>
					<h2>Choose a test account</h2>
					<p className="login-note">Each account contains fictional funds and seeded payees.</p>
					<div className="user-options">
						{users.map((item, index) => (
							<button key={item.id} className="user-option" onClick={() => onChoose(item.id)} disabled={busy}>
								<div className={`avatar avatar-${index}`}>{item.name.split(" ").map((part) => part[0]).join("")}</div>
								<div><strong>{item.name}</strong><span>Personal checking · Sandbox</span></div>
								<ArrowUpRight size={17} />
							</button>
						))}
					</div>
					{error && <p className="form-error">{error}</p>}
					<div className="login-security"><LockKeyhole size={14} /> Local demo session · no real account access</div>
				</div>
			</div>
		</main>
	);
}
