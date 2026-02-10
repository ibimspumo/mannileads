<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { Editor } from '@tiptap/core';
	import StarterKit from '@tiptap/starter-kit';
	import Link from '@tiptap/extension-link';
	import TextAlign from '@tiptap/extension-text-align';
	import { TextStyle } from '@tiptap/extension-text-style';
	import { Color } from '@tiptap/extension-text-style';
	import Image from '@tiptap/extension-image';
	import Placeholder from '@tiptap/extension-placeholder';

	interface Props {
		content?: string;
		onchange?: (html: string) => void;
	}

	let { content = '', onchange }: Props = $props();

	let editorElement: HTMLDivElement;
	let editor: Editor | null = null;
	let showPlaceholders = $state(false);
	let showColorPicker = $state(false);

	const PLACEHOLDER_GROUPS = [
		{ group: 'Firma', items: [
			{ key: 'firma', label: 'Firmenname' },
			{ key: 'website', label: 'Website' },
			{ key: 'branche', label: 'Branche' },
			{ key: 'groesse', label: 'Größe' },
			{ key: 'plz', label: 'PLZ' },
			{ key: 'ort', label: 'Ort' },
		]},
		{ group: 'Kontakt', items: [
			{ key: 'ansprechpartner', label: 'Ansprechpartner' },
			{ key: 'position', label: 'Position' },
			{ key: 'email', label: 'Email' },
			{ key: 'telefon', label: 'Telefon' },
		]},
		{ group: 'Online-Präsenz', items: [
			{ key: 'websiteQualitaet', label: 'Website-Qualität (0-100)' },
			{ key: 'socialMediaLinks', label: 'Social Media Links' },
			{ key: 'googleBewertung', label: 'Google-Bewertung' },
		]},
		{ group: 'Scoring', items: [
			{ key: 'score', label: 'Score' },
			{ key: 'segment', label: 'Segment' },
			{ key: 'kiScore', label: 'KI-Score' },
			{ key: 'kiSegment', label: 'KI-Segment' },
			{ key: 'kiScoreBegruendung', label: 'KI-Score Begründung' },
		]},
		{ group: 'KI-Pitch & Analyse', items: [
			{ key: 'kiZusammenfassung', label: 'KI-Zusammenfassung' },
			{ key: 'kiAnsprache', label: 'Pitch AgentZ' },
			{ key: 'kiAnspracheSig', label: 'Pitch SIG-Werbung' },
			{ key: 'kiZielgruppe', label: 'Zielgruppe' },
			{ key: 'kiOnlineAuftritt', label: 'Online-Auftritt Bewertung' },
			{ key: 'kiSchwaechen', label: 'Schwächen' },
			{ key: 'kiChancen', label: 'Chancen für uns' },
			{ key: 'kiWettbewerb', label: 'Wettbewerbssituation' },
		]},
		{ group: 'Sonstiges', items: [
			{ key: 'status', label: 'Status' },
			{ key: 'tags', label: 'Tags' },
			{ key: 'notizen', label: 'Notizen' },
		]},
	];

	let placeholderSearch = $state('');
	let filteredGroups = $derived(
		PLACEHOLDER_GROUPS.map(g => ({
			...g,
			items: g.items.filter(i => 
				!placeholderSearch || 
				i.label.toLowerCase().includes(placeholderSearch.toLowerCase()) ||
				i.key.toLowerCase().includes(placeholderSearch.toLowerCase())
			)
		})).filter(g => g.items.length > 0)
	);

	const COLORS = ['#000000', '#333333', '#666666', '#ffa502', '#e74c3c', '#2ecc71', '#3498db', '#9b59b6', '#1abc9c', '#f39c12'];

	onMount(() => {
		editor = new Editor({
			element: editorElement,
			extensions: [
				StarterKit,
				Link.configure({ openOnClick: false }),
				TextAlign.configure({ types: ['heading', 'paragraph'] }),
				TextStyle,
				Color,
				Image,
				Placeholder.configure({ placeholder: 'Email-Inhalt hier eingeben...' }),
			],
			content: content || '',
			onUpdate: ({ editor: e }) => {
				onchange?.(e.getHTML());
			},
			editorProps: {
				attributes: {
					class: 'prose prose-sm max-w-none focus:outline-none min-h-[300px] p-4',
				},
			},
		});
	});

	onDestroy(() => {
		editor?.destroy();
	});

	function insertPlaceholder(key: string) {
		if (!editor) return;
		editor.chain().focus().insertContent(`{{${key}}}`).run();
		showPlaceholders = false;
	}

	function addLink() {
		if (!editor) return;
		const url = prompt('URL eingeben:');
		if (url) {
			editor.chain().focus().setLink({ href: url }).run();
		}
	}

	function addImage() {
		if (!editor) return;
		const url = prompt('Bild-URL eingeben:');
		if (url) {
			editor.chain().focus().setImage({ src: url }).run();
		}
	}

	function setColor(color: string) {
		if (!editor) return;
		editor.chain().focus().setColor(color).run();
		showColorPicker = false;
	}

	function btn(active: boolean): string {
		return `px-2 py-1.5 text-xs font-mono rounded transition-all ${active ? 'bg-[var(--color-accent)] text-[var(--color-surface-900)] font-bold' : 'bg-[var(--color-surface-600)] text-[var(--color-text-secondary)] hover:bg-[var(--color-surface-500)] hover:text-[var(--color-text-primary)]'}`;
	}
</script>

<div class="border border-[var(--color-surface-600)] rounded overflow-hidden">
	<!-- Toolbar -->
	{#if editor}
	<div class="flex flex-wrap items-center gap-1 p-2 bg-[var(--color-surface-800)] border-b border-[var(--color-surface-600)]">
		<!-- Text Format -->
		<button class={btn(editor.isActive('bold'))} onclick={() => editor?.chain().focus().toggleBold().run()} title="Fett">
			<strong>B</strong>
		</button>
		<button class={btn(editor.isActive('italic'))} onclick={() => editor?.chain().focus().toggleItalic().run()} title="Kursiv">
			<em>I</em>
		</button>
		<button class={btn(editor.isActive('strike'))} onclick={() => editor?.chain().focus().toggleStrike().run()} title="Durchgestrichen">
			<s>S</s>
		</button>

		<div class="w-px h-5 bg-[var(--color-surface-600)] mx-1"></div>

		<!-- Headings -->
		<button class={btn(editor.isActive('heading', { level: 1 }))} onclick={() => editor?.chain().focus().toggleHeading({ level: 1 }).run()}>
			H1
		</button>
		<button class={btn(editor.isActive('heading', { level: 2 }))} onclick={() => editor?.chain().focus().toggleHeading({ level: 2 }).run()}>
			H2
		</button>
		<button class={btn(editor.isActive('heading', { level: 3 }))} onclick={() => editor?.chain().focus().toggleHeading({ level: 3 }).run()}>
			H3
		</button>

		<div class="w-px h-5 bg-[var(--color-surface-600)] mx-1"></div>

		<!-- Lists -->
		<button class={btn(editor.isActive('bulletList'))} onclick={() => editor?.chain().focus().toggleBulletList().run()} title="Aufzählung">
			• Liste
		</button>
		<button class={btn(editor.isActive('orderedList'))} onclick={() => editor?.chain().focus().toggleOrderedList().run()} title="Nummerierung">
			1. Liste
		</button>

		<div class="w-px h-5 bg-[var(--color-surface-600)] mx-1"></div>

		<!-- Alignment -->
		<button class={btn(editor.isActive({ textAlign: 'left' }))} onclick={() => editor?.chain().focus().setTextAlign('left').run()} title="Links">
			≡←
		</button>
		<button class={btn(editor.isActive({ textAlign: 'center' }))} onclick={() => editor?.chain().focus().setTextAlign('center').run()} title="Mitte">
			≡↔
		</button>
		<button class={btn(editor.isActive({ textAlign: 'right' }))} onclick={() => editor?.chain().focus().setTextAlign('right').run()} title="Rechts">
			≡→
		</button>

		<div class="w-px h-5 bg-[var(--color-surface-600)] mx-1"></div>

		<!-- Color -->
		<div class="relative">
			<button class={btn(false)} onclick={() => { showColorPicker = !showColorPicker; showPlaceholders = false; }} title="Textfarbe">
				🎨
			</button>
			{#if showColorPicker}
				<div class="absolute top-full left-0 mt-1 p-2 bg-[var(--color-surface-700)] border border-[var(--color-surface-600)] rounded shadow-lg z-20 flex flex-wrap gap-1 w-36">
					{#each COLORS as color}
						<button
							class="w-6 h-6 rounded border border-[var(--color-surface-500)] hover:scale-110 transition-transform"
							style="background-color: {color}"
							onclick={() => setColor(color)}
						></button>
					{/each}
				</div>
			{/if}
		</div>

		<!-- Link & Image -->
		<button class={btn(editor.isActive('link'))} onclick={addLink} title="Link einfügen">
			🔗
		</button>
		<button class={btn(false)} onclick={addImage} title="Bild einfügen">
			🖼️
		</button>

		<div class="w-px h-5 bg-[var(--color-surface-600)] mx-1"></div>

		<!-- Placeholders -->
		<div class="relative">
			<button
				class="px-2 py-1.5 text-xs font-mono font-bold rounded bg-[var(--color-accent)] text-[var(--color-surface-900)] hover:opacity-90 transition-all shadow-[0_0_8px_rgba(255,165,2,0.2)]"
				onclick={() => { showPlaceholders = !showPlaceholders; showColorPicker = false; placeholderSearch = ''; }}
			>
				{'{{x}}'} PLATZHALTER
			</button>
			{#if showPlaceholders}
				<div class="absolute top-full left-0 mt-1 bg-[var(--color-surface-700)] border border-[var(--color-surface-600)] rounded shadow-lg z-20 w-72 max-h-80 overflow-hidden flex flex-col">
					<div class="p-2 border-b border-[var(--color-surface-600)]">
						<input
							bind:value={placeholderSearch}
							placeholder="Suchen..."
							class="w-full px-2 py-1 text-xs font-mono bg-[var(--color-surface-800)] border border-[var(--color-surface-600)] rounded text-[var(--color-text-primary)] focus:border-[var(--color-accent)] focus:outline-none"
						/>
					</div>
					<div class="overflow-y-auto max-h-64">
						{#each filteredGroups as group}
							<div class="px-3 py-1.5 text-[10px] font-bold font-mono uppercase tracking-wider text-[var(--color-accent)] bg-[var(--color-surface-800)] sticky top-0">
								{group.group}
							</div>
							{#each group.items as ph}
								<button
									class="w-full text-left px-3 py-1.5 text-xs font-mono hover:bg-[var(--color-surface-600)] text-[var(--color-text-secondary)] hover:text-[var(--color-accent)] transition-colors flex justify-between items-center gap-2"
									onclick={() => insertPlaceholder(ph.key)}
								>
									<span class="text-[var(--color-text-muted)] truncate">{ph.label}</span>
									<span class="text-[var(--color-accent)] text-[10px] shrink-0">{`{{${ph.key}}}`}</span>
								</button>
							{/each}
						{/each}
					</div>
				</div>
			{/if}
		</div>
	</div>
	{/if}

	<!-- Editor -->
	<div
		bind:this={editorElement}
		class="bg-white text-gray-900 min-h-[300px] [&_.ProseMirror]:min-h-[300px] [&_.ProseMirror]:p-4 [&_.ProseMirror]:focus:outline-none [&_.ProseMirror_p.is-editor-empty:first-child::before]:text-gray-400 [&_.ProseMirror_p.is-editor-empty:first-child::before]:content-[attr(data-placeholder)] [&_.ProseMirror_p.is-editor-empty:first-child::before]:float-left [&_.ProseMirror_p.is-editor-empty:first-child::before]:pointer-events-none [&_.ProseMirror_p.is-editor-empty:first-child::before]:h-0"
	></div>
</div>
