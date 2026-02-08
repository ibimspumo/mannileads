import { writable } from 'svelte/store';
import { browser } from '$app/environment';

const STORAGE_KEY = 'mannileads_auth';

function createAuthStore() {
	const initial = browser ? localStorage.getItem(STORAGE_KEY) === 'true' : false;
	const { subscribe, set } = writable(initial);

	return {
		subscribe,
		async login(password: string): Promise<boolean> {
			try {
				const res = await fetch('/api/auth', {
					method: 'POST',
					headers: { 'Content-Type': 'application/json' },
					body: JSON.stringify({ password })
				});
				if (res.ok) {
					set(true);
					if (browser) localStorage.setItem(STORAGE_KEY, 'true');
					return true;
				}
				return false;
			} catch {
				return false;
			}
		},
		logout() {
			set(false);
			if (browser) localStorage.removeItem(STORAGE_KEY);
		}
	};
}

export const auth = createAuthStore();
