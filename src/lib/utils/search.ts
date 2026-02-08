import type { Lead } from '$lib/types/lead';

export function searchLeads(leads: Lead[], query: string): Lead[] {
	if (!query.trim()) return leads;
	const q = query.toLowerCase();
	return leads.filter(l =>
		l.firma.toLowerCase().includes(q) ||
		l.ort.toLowerCase().includes(q) ||
		l.branche.toLowerCase().includes(q) ||
		l.notizen.toLowerCase().includes(q) ||
		l.ansprechpartner.toLowerCase().includes(q) ||
		l.email.toLowerCase().includes(q) ||
		l.tags.some(t => t.toLowerCase().includes(q))
	);
}
