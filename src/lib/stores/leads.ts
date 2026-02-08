import { writable, derived } from 'svelte/store';
import { browser } from '$app/environment';
import type { Lead, HistoryEntry } from '$lib/types/lead';
import { berechneScore, berechneSegment } from '$lib/utils/scoring';

const STORAGE_KEY = 'mannileads_data';

function loadLeads(): Lead[] {
	if (!browser) return [];
	try {
		const data = localStorage.getItem(STORAGE_KEY);
		return data ? JSON.parse(data) : [];
	} catch {
		return [];
	}
}

function saveLeads(leads: Lead[]) {
	if (browser) localStorage.setItem(STORAGE_KEY, JSON.stringify(leads));
}

function generateId(): string {
	return Date.now().toString(36) + Math.random().toString(36).substring(2, 8);
}

function createLeadsStore() {
	const { subscribe, set, update } = writable<Lead[]>(loadLeads());

	subscribe(leads => saveLeads(leads));

	return {
		subscribe,
		add(data: Partial<Lead>): string {
			const id = generateId();
			const now = new Date().toISOString();
			const score = berechneScore(data);
			const segment = data.segmentManuell ? (data.segment ?? berechneSegment(score)) : berechneSegment(score);
			const lead: Lead = {
				id,
				firma: data.firma ?? '',
				website: data.website ?? '',
				branche: data.branche ?? '',
				groesse: data.groesse ?? '',
				plz: data.plz ?? '',
				ort: data.ort ?? '',
				ansprechpartner: data.ansprechpartner ?? '',
				position: data.position ?? '',
				email: data.email ?? '',
				telefon: data.telefon ?? '',
				websiteQualitaet: data.websiteQualitaet ?? 0,
				socialMedia: data.socialMedia ?? false,
				socialMediaLinks: data.socialMediaLinks ?? '',
				googleBewertung: data.googleBewertung ?? '',
				score,
				kiZusammenfassung: data.kiZusammenfassung ?? '',
				segment,
				segmentManuell: data.segmentManuell ?? false,
				tags: data.tags ?? [],
				status: data.status ?? 'Neu',
				notizen: data.notizen ?? '',
				history: [{ timestamp: now, aktion: 'Erstellt', details: 'Lead angelegt' }],
				erstelltAm: now,
				bearbeitetAm: now
			};
			update(leads => [...leads, lead]);
			return id;
		},
		update_lead(id: string, data: Partial<Lead>, aktion?: string) {
			update(leads => leads.map(l => {
				if (l.id !== id) return l;
				const updated = { ...l, ...data, bearbeitetAm: new Date().toISOString() };
				// Recalculate score
				updated.score = berechneScore(updated);
				if (!updated.segmentManuell) {
					updated.segment = berechneSegment(updated.score);
				}
				if (aktion) {
					const entry: HistoryEntry = {
						timestamp: new Date().toISOString(),
						aktion,
						details: typeof data.status === 'string' ? `Status → ${data.status}` :
								typeof data.segment === 'string' ? `Segment → ${data.segment}` : aktion
					};
					updated.history = [...(updated.history ?? []), entry];
				}
				return updated;
			}));
		},
		remove(id: string) {
			update(leads => leads.filter(l => l.id !== id));
		},
		importLeads(newLeads: Partial<Lead>[]) {
			const ids: string[] = [];
			for (const data of newLeads) {
				// If full lead with id, use as-is
				if (data.id && data.firma) {
					update(leads => {
						if (leads.find(l => l.id === data.id)) return leads;
						const score = berechneScore(data);
						const lead: Lead = {
							id: data.id!,
							firma: data.firma ?? '',
							website: data.website ?? '',
							branche: data.branche ?? '',
							groesse: data.groesse ?? '',
							plz: data.plz ?? '',
							ort: data.ort ?? '',
							ansprechpartner: data.ansprechpartner ?? '',
							position: data.position ?? '',
							email: data.email ?? '',
							telefon: data.telefon ?? '',
							websiteQualitaet: data.websiteQualitaet ?? 0,
							socialMedia: data.socialMedia ?? false,
							socialMediaLinks: data.socialMediaLinks ?? '',
							googleBewertung: data.googleBewertung ?? '',
							score: data.score ?? score,
							kiZusammenfassung: data.kiZusammenfassung ?? '',
							segment: data.segment ?? berechneSegment(score),
							segmentManuell: data.segmentManuell ?? false,
							tags: data.tags ?? [],
							status: data.status ?? 'Neu',
							notizen: data.notizen ?? '',
							history: data.history ?? [{ timestamp: new Date().toISOString(), aktion: 'Importiert', details: 'Via Import' }],
							erstelltAm: data.erstelltAm ?? new Date().toISOString(),
							bearbeitetAm: data.bearbeitetAm ?? new Date().toISOString()
						};
						return [...leads, lead];
					});
					ids.push(data.id);
				} else {
					ids.push(this.add(data));
				}
			}
			return ids;
		},
		replaceAll(newLeads: Lead[]) {
			set(newLeads);
		}
	};
}

export const leads = createLeadsStore();

export const leadCount = derived(leads, $leads => $leads.length);
