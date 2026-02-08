import type { Lead } from '$lib/types/lead';

export function exportCSV(leads: Lead[]): string {
	const headers = [
		'Firma', 'Website', 'Branche', 'Größe', 'PLZ', 'Ort',
		'Ansprechpartner', 'Position', 'Email', 'Telefon',
		'Website-Qualität', 'Social Media', 'Google-Bewertung',
		'Score', 'Segment', 'Status', 'Tags', 'Notizen',
		'Erstellt', 'Bearbeitet'
	];
	const rows = leads.map(l => [
		l.firma, l.website, l.branche, l.groesse, l.plz, l.ort,
		l.ansprechpartner, l.position, l.email, l.telefon,
		String(l.websiteQualitaet), l.socialMedia ? 'Ja' : 'Nein', l.googleBewertung,
		String(l.score), l.segment, l.status, l.tags.join('; '), l.notizen,
		l.erstelltAm, l.bearbeitetAm
	].map(v => `"${(v ?? '').replace(/"/g, '""')}"`).join(','));
	return [headers.join(','), ...rows].join('\n');
}

export function exportJSON(leads: Lead[]): string {
	return JSON.stringify(leads, null, 2);
}

export function downloadFile(content: string, filename: string, mime: string) {
	const blob = new Blob([content], { type: mime });
	const url = URL.createObjectURL(blob);
	const a = document.createElement('a');
	a.href = url;
	a.download = filename;
	a.click();
	URL.revokeObjectURL(url);
}

export function parseCSVImport(csv: string): Partial<Lead>[] {
	const lines = csv.trim().split('\n');
	if (lines.length < 2) return [];
	const headers = lines[0].split(',').map(h => h.replace(/"/g, '').trim());
	const leads: Partial<Lead>[] = [];
	for (let i = 1; i < lines.length; i++) {
		const values = lines[i].match(/("([^"]*("")*)*"|[^,]*)(,|$)/g)?.map(v =>
			v.replace(/,$/, '').replace(/^"|"$/g, '').replace(/""/g, '"').trim()
		) ?? [];
		const lead: Record<string, string> = {};
		headers.forEach((h, idx) => { lead[h] = values[idx] ?? ''; });
		leads.push({
			firma: lead['Firma'] ?? lead['firma'] ?? '',
			website: lead['Website'] ?? lead['website'] ?? '',
			branche: lead['Branche'] ?? lead['branche'] ?? '',
			groesse: lead['Größe'] ?? lead['groesse'] ?? '',
			plz: lead['PLZ'] ?? lead['plz'] ?? '',
			ort: lead['Ort'] ?? lead['ort'] ?? '',
			ansprechpartner: lead['Ansprechpartner'] ?? lead['ansprechpartner'] ?? '',
			position: lead['Position'] ?? lead['position'] ?? '',
			email: lead['Email'] ?? lead['email'] ?? '',
			telefon: lead['Telefon'] ?? lead['telefon'] ?? '',
			notizen: lead['Notizen'] ?? lead['notizen'] ?? ''
		});
	}
	return leads;
}

export function parseJSONImport(json: string): Partial<Lead>[] {
	try {
		const data = JSON.parse(json);
		return Array.isArray(data) ? data : [];
	} catch {
		return [];
	}
}
