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

	const PLACEHOLDERS = [
		{ key: 'firma', label: 'Firma' },
		{ key: 'email', label: 'Email' },
		{ key: 'ansprechpartner', label: 'Ansprechpartner' },
		{ key: 'telefon', label: 'Telefon' },
		{ key: 'strasse', label: 'Straße' },
		{ key: 'plz', label: 'PLZ' },
		{ key: 'ort', label: 'Ort' },
		{ key: 'bundesland', label: 'Bundesland' },
		{ key: 'branche', label: 'Branche' },
		{ key: 'website', label: 'Website' },
		{ key: 'score', label: 'Score' },
		{ key: 'segment', label: 'Segment' },
	];

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
				onclick={() => { showPlaceholders = !showPlaceholders; showColorPicker = false; }}
			>
				{'{{x}}'} PLATZHALTER
			</button>
			{#if showPlaceholders}
				<div class="absolute top-full left-0 mt-1 bg-[var(--color-surface-700)] border border-[var(--color-surface-600)] rounded shadow-lg z-20 w-52 max-h-64 overflow-y-auto">
					{#each PLACEHOLDERS as ph}
						<button
							class="w-full text-left px-3 py-2 text-xs font-mono hover:bg-[var(--color-surface-600)] text-[var(--color-text-secondary)] hover:text-[var(--color-accent)] transition-colors flex justify-between items-center"
							onclick={() => insertPlaceholder(ph.key)}
						>
							<span class="text-[var(--color-text-muted)]">{ph.label}</span>
							<span class="text-[var(--color-accent)]">{`{{${ph.key}}}`}</span>
						</button>
					{/each}
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
