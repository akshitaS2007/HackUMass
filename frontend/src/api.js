const API_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000";

let token = localStorage.getItem("bb_access_token") || "";

export function setToken(value) {
	token = value;
	if (value) localStorage.setItem("bb_access_token", value);
	else localStorage.removeItem("bb_access_token");
}

export async function api(path, options = {}) {
	const headers = { "Content-Type": "application/json", ...options.headers };
	if (token) headers.Authorization = `Bearer ${token}`;
	let response;
	try {
		response = await fetch(`${API_BASE}${path}`, { ...options, headers });
	} catch (error) {
		if (error instanceof TypeError) {
			throw new Error(`Can't reach the local API at ${API_BASE}. Start the backend and try again.`);
		}
		throw error;
	}
	const data = await response.json().catch(() => ({}));
	if (!response.ok) throw new Error(data.detail || "The request could not be completed.");
	return data;
}

export function post(path, body = {}) {
	return api(path, { method: "POST", body: JSON.stringify(body) });
}
