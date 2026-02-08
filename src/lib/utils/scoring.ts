import type { Lead, ScoreBreakdownItem, Segment } from '$lib/types/lead';

export function berechneScore(lead: Partial<Lead>): number {
	const breakdown = getScoreBreakdown(lead);
	return breakdown.reduce((sum, item) => sum + item.punkte, 0);
}

export function getScoreBreakdown(lead: Partial<Lead>): ScoreBreakdownItem[] {
	const items: ScoreBreakdownItem[] = [
		{
			label: 'Website vorhanden',
			punkte: lead.website ? 15 : 0,
			maxPunkte: 15,
			erfuellt: !!lead.website
		},
		{
			label: 'Website-Qualität',
			punkte: Math.min((lead.websiteQualitaet ?? 0) * 3, 15),
			maxPunkte: 15,
			erfuellt: (lead.websiteQualitaet ?? 0) >= 3
		},
		{
			label: 'Social Media vorhanden',
			punkte: lead.socialMedia ? 10 : 0,
			maxPunkte: 10,
			erfuellt: !!lead.socialMedia
		},
		{
			label: 'Ansprechpartner bekannt',
			punkte: lead.ansprechpartner ? 15 : 0,
			maxPunkte: 15,
			erfuellt: !!lead.ansprechpartner
		},
		{
			label: 'Email vorhanden',
			punkte: lead.email ? 10 : 0,
			maxPunkte: 10,
			erfuellt: !!lead.email
		},
		{
			label: 'Telefon vorhanden',
			punkte: lead.telefon ? 5 : 0,
			maxPunkte: 5,
			erfuellt: !!lead.telefon
		},
		{
			label: 'Branche angegeben',
			punkte: lead.branche ? 10 : 0,
			maxPunkte: 10,
			erfuellt: !!lead.branche
		},
		{
			label: 'Firmengröße angegeben',
			punkte: lead.groesse ? 5 : 0,
			maxPunkte: 5,
			erfuellt: !!lead.groesse
		},
		{
			label: 'Google-Bewertung vorhanden',
			punkte: lead.googleBewertung ? 10 : 0,
			maxPunkte: 10,
			erfuellt: !!lead.googleBewertung
		},
		{
			label: 'Notizen/KI-Zusammenfassung',
			punkte: (lead.kiZusammenfassung || lead.notizen) ? 5 : 0,
			maxPunkte: 5,
			erfuellt: !!(lead.kiZusammenfassung || lead.notizen)
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
