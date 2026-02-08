import { writable } from 'svelte/store';
import { browser } from '$app/environment';

const STORAGE_KEY = 'mannileads_auth';
const PASSWORD = 'AgentZ2026!';

function createAuthStore() {
	const initial = browser ? localStorage.getItem(STORAGE_KEY) === 'true' : false;
	const { subscribe, set } = writable(initial);

	return {
		subscribe,
		login(password: string): boolean {
			if (password === PASSWORD) {
				set(true);
				if (browser) localStorage.setItem(STORAGE_KEY, 'true');
				return true;
			}
			return false;
		},
		logout() {
			set(false);
			if (browser) localStorage.removeItem(STORAGE_KEY);
		}
	};
}

export const auth = createAuthStore();
