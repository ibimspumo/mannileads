import { writable, derived } from 'svelte/store';
import { browser } from '$app/environment';
import type { Lead, HistoryEntry } from '$lib/types/lead';
import { berechneScore, berechneSegment } from '$lib/utils/scoring';
import { convex, api } from '$lib/convex';
import type { Id } from '../../convex/_generated/dataModel';

// Local reactive store — synced with Convex
const { subscribe, set, update } = writable<Lead[]>([]);

let _loaded = false;
let _loading = false;

// Convert Convex doc to our Lead type
function docToLead(doc: any): Lead {
	return { ...doc, id: doc._id };
}

function leadToDoc(lead: Partial<Lead>): any {
	const { id, ...rest } = lead as any;
	return rest;
}

async function fetchAll(): Promise<Lead[]> {
	const docs = await convex.query(api.leads.list);
	return docs.map(docToLead);
}

async function syncFromConvex() {
	if (_loading) return;
	_loading = true;
	try {
		const leads = await fetchAll();
		set(leads);
		_loaded = true;
	} finally {
		_loading = false;
	}
}

// Initial load
if (browser) {
	syncFromConvex();
}

function createLeadsStore() {
	return {
		subscribe,
		async load() {
			await syncFromConvex();
		},
		get loaded() { return _loaded; },
		async add(data: Partial<Lead>): Promise<string> {
			const now = new Date().toISOString();
			const score = berechneScore(data);
			const segment = data.segmentManuell ? (data.segment ?? berechneSegment(score)) : berechneSegment(score);
			const leadData = {
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
				status: data.status ?? 'Neu' as const,
				notizen: data.notizen ?? '',
				history: [{ timestamp: now, aktion: 'Erstellt', details: 'Lead angelegt' }],
				erstelltAm: now,
				bearbeitetAm: now
			};
			const id = await convex.mutation(api.leads.create, leadData);
			// Optimistic update
			update(leads => [...leads, { ...leadData, id: id as string }]);
			return id as string;
		},
		async update_lead(id: string, data: Partial<Lead>, aktion?: string) {
			let updatedLead: Lead | undefined;
			// Optimistic: update local first
			update(leads => leads.map(l => {
				if (l.id !== id) return l;
				const updated = { ...l, ...data, bearbeitetAm: new Date().toISOString() };
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
				updatedLead = updated;
				return updated;
			}));
			// Push to Convex
			if (updatedLead) {
				const { id: _id, ...doc } = updatedLead;
				await convex.mutation(api.leads.update, { id: id as Id<"leads">, ...doc });
			}
		},
		async remove(id: string) {
			update(leads => leads.filter(l => l.id !== id));
			await convex.mutation(api.leads.remove, { id: id as Id<"leads"> });
		},
		async importLeads(newLeads: Partial<Lead>[]): Promise<string[]> {
			const now = new Date().toISOString();
			const leadsToCreate = newLeads.map(data => {
				const score = berechneScore(data);
				return {
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
					status: data.status ?? 'Neu' as const,
					notizen: data.notizen ?? '',
					history: data.history ?? [{ timestamp: now, aktion: 'Importiert', details: 'Via Import' }],
					erstelltAm: data.erstelltAm ?? now,
					bearbeitetAm: data.bearbeitetAm ?? now
				};
			});
			// Batch in chunks of 50 (Convex limits)
			const allIds: string[] = [];
			for (let i = 0; i < leadsToCreate.length; i += 50) {
				const chunk = leadsToCreate.slice(i, i + 50);
				const ids = await convex.mutation(api.leads.bulkCreate, { leads: chunk });
				allIds.push(...(ids as string[]));
			}
			await syncFromConvex();
			return allIds;
		},
		async replaceAll(newLeads: Lead[]) {
			const docs = newLeads.map(l => {
				const { id, ...rest } = l;
				return rest;
			});
			// Batch in chunks
			// First delete all via replaceAll with first chunk, then bulkCreate rest
			const chunks = [];
			for (let i = 0; i < docs.length; i += 50) {
				chunks.push(docs.slice(i, i + 50));
			}
			if (chunks.length > 0) {
				await convex.mutation(api.leads.replaceAll, { leads: chunks[0] });
				for (let i = 1; i < chunks.length; i++) {
					await convex.mutation(api.leads.bulkCreate, { leads: chunks[i] });
				}
			} else {
				await convex.mutation(api.leads.replaceAll, { leads: [] });
			}
			await syncFromConvex();
		}
	};
}

export const leads = createLeadsStore();
export const leadCount = derived({ subscribe }, $leads => $leads.length);
