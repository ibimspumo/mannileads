import { writable } from 'svelte/store';
import type { Segment, LeadStatus } from '$lib/types/lead';

export interface FilterState {
	search: string;
	segment: Segment | '';
	status: LeadStatus | '';
	scoreMin: number;
	scoreMax: number;
	tags: string[];
	plz: string;
	sortBy: string;
	sortDir: 'asc' | 'desc';
}

export const filters = writable<FilterState>({
	search: '',
	segment: '',
	status: '',
	scoreMin: 0,
	scoreMax: 100,
	tags: [],
	plz: '',
	sortBy: 'score',
	sortDir: 'desc'
});
