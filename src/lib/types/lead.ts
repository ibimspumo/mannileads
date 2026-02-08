export type Segment = 'HOT' | 'WARM' | 'COLD' | 'DISQUALIFIED';
export type LeadStatus = 'Neu' | 'Kontaktiert' | 'Interessiert' | 'Angebot' | 'Gewonnen' | 'Verloren';

export interface Lead {
	id: string;
	// Firma
	firma: string;
	website: string;
	branche: string;
	groesse: string;
	plz: string;
	ort: string;
	// Kontakt
	ansprechpartner: string;
	position: string;
	email: string;
	telefon: string;
	// Online-Präsenz
	websiteQualitaet: number; // 1-5
	socialMedia: boolean;
	socialMediaLinks: string;
	googleBewertung: string;
	// Analyse
	score: number; // 0-100
	kiZusammenfassung: string;
	segment: Segment;
	segmentManuell: boolean;
	tags: string[];
	// Status
	status: LeadStatus;
	// Notizen
	notizen: string;
	// History
	history: HistoryEntry[];
	// Timestamps
	erstelltAm: string;
	bearbeitetAm: string;
	// KI-Analyse (Gemini)
	kiAnalysiert?: boolean;
	kiAnalysiertAm?: string;
	kiZielgruppe?: string;
	kiOnlineAuftritt?: string;
	kiSchwaechen?: string;
	kiChancen?: string;
	kiWettbewerb?: string;
	kiAnsprache?: string;
	kiAnspracheSig?: string;
	kiScore?: number;
	kiScoreBegruendung?: string;
	kiSegment?: string;
	// Website Content
	websiteText?: string;
}

export interface HistoryEntry {
	timestamp: string;
	aktion: string;
	details: string;
}

export interface ScoreBreakdownItem {
	label: string;
	punkte: number;
	maxPunkte: number;
	erfuellt: boolean;
}

export const SEGMENTS: Segment[] = ['HOT', 'WARM', 'COLD', 'DISQUALIFIED'];
export const STATUSES: LeadStatus[] = ['Neu', 'Kontaktiert', 'Interessiert', 'Angebot', 'Gewonnen', 'Verloren'];
export const BRANCHEN = [
	'Gastronomie', 'Handwerk', 'Einzelhandel', 'Dienstleistung', 'IT/Tech',
	'Gesundheit', 'Immobilien', 'Bildung', 'Tourismus', 'Automotive',
	'Finanzen', 'Medien', 'Logistik', 'Sonstiges'
];
