import type { Lead, ScoreBreakdownItem, Segment } from '$lib/types/lead';

export function berechneScore(lead: Partial<Lead>): number {
	// Wenn KI-Score vorhanden, diesen verwenden
	if (lead.kiScore != null && lead.kiScore > 0) return lead.kiScore;
	// Fallback: statischer Score
	return lead.score ?? 0;
}

export function getScoreBreakdown(lead: Partial<Lead>): ScoreBreakdownItem[] {
	const items: ScoreBreakdownItem[] = [
		{
			label: 'KI-Bewertung',
			punkte: lead.kiScore ?? 0,
			maxPunkte: 100,
			erfuellt: (lead.kiScore ?? 0) >= 50
		},
		{
			label: 'Email vorhanden',
			punkte: lead.email ? 1 : 0,
			maxPunkte: 1,
			erfuellt: !!lead.email
		},
		{
			label: 'Telefon vorhanden',
			punkte: lead.telefon ? 1 : 0,
			maxPunkte: 1,
			erfuellt: !!lead.telefon
		},
		{
			label: 'Ansprechpartner bekannt',
			punkte: lead.ansprechpartner ? 1 : 0,
			maxPunkte: 1,
			erfuellt: !!lead.ansprechpartner
		},
		{
			label: 'Social Media vorhanden',
			punkte: lead.socialMedia ? 1 : 0,
			maxPunkte: 1,
			erfuellt: !!lead.socialMedia
		},
		{
			label: 'KI-Analyse durchgeführt',
			punkte: lead.kiAnalysiert ? 1 : 0,
			maxPunkte: 1,
			erfuellt: !!lead.kiAnalysiert
		}
	];
	return items;
}

export function berechneSegment(score: number): Segment {
	if (score >= 70) return 'HOT';
	if (score >= 40) return 'WARM';
	if (score >= 15) return 'COLD';
	return 'DISQUALIFIED';
}

export function getScoreColor(score: number): string {
	if (score >= 80) return '#22c55e';
	if (score >= 60) return '#84cc16';
	if (score >= 40) return '#eab308';
	if (score >= 20) return '#f97316';
	return '#ef4444';
}

export function getSegmentColor(segment: Segment): string {
	const map: Record<Segment, string> = {
		HOT: 'var(--color-hot)',
		WARM: 'var(--color-warm)',
		COLD: 'var(--color-cold)',
		DISQUALIFIED: 'var(--color-disqualified)'
	};
	return map[segment];
}
