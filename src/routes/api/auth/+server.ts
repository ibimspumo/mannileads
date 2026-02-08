import { json } from '@sveltejs/kit';
import type { RequestHandler } from './$types';

const DEFAULT_PASSWORD = 'AgentZ2026!';

export const POST: RequestHandler = async ({ request }) => {
	const { password } = await request.json();
	const expected = process.env.AUTH_PASSWORD || DEFAULT_PASSWORD;

	if (password === expected) {
		return json({ success: true });
	}

	return json({ success: false }, { status: 401 });
};
