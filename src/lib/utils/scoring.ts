import type { Lead, ScoreBreakdownItem, Segment } from '$lib/types/lead';

export function berechneScore(lead: Partial<Lead>): number {
	if (lead.kiScore != null && lead.kiScore > 0) return lead.kiScore;
	return lead.score ?? 0;
}

export function getScoreBreakdown(lead: Partial<Lead>): ScoreBreakdownItem[] {
	// Nur noch für Datenvollständigkeit, nicht für Score-Berechnung
	return [
		{ label: 'Email', punkte: lead.email ? 1 : 0, maxPunkte: 1, erfuellt: !!lead.email },
		{ label: 'Telefon', punkte: lead.telefon ? 1 : 0, maxPunkte: 1, erfuellt: !!lead.telefon },
		{ label: 'Ansprechpartner', punkte: lead.ansprechpartner ? 1 : 0, maxPunkte: 1, erfuellt: !!lead.ansprechpartner },
		{ label: 'Social Media', punkte: lead.socialMedia ? 1 : 0, maxPunkte: 1, erfuellt: !!lead.socialMedia },
	];
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
