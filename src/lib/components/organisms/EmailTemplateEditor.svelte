<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { Editor } from '@tiptap/core';
	import StarterKit from '@tiptap/starter-kit';
	import Link from '@tiptap/extension-link';
	import TextAlign from '@tiptap/extension-text-align';
	import { Color } from '@tiptap/extension-color';
	import { TextStyle } from '@tiptap/extension-text-style';
	import { Underline } from '@tiptap/extension-underline';
	import { Image } from '@tiptap/extension-image';

	// Props
	interface Props {
		value: string;
		onUpdate?: (html: string) => void;
		placeholders?: string[];
		previewMode?: boolean;
	}

	let { 
		value = $bindable(''),
		onUpdate,
		placeholders = [],
		previewMode = false 
	}: Props = $props();

	let editor: Editor | null = null;
	let editorElement: HTMLDivElement;
	let showLinkDialog = $state(false);
	let linkUrl = $state('');
	let showImageDialog = $state(false);
	let imageUrl = $state('');
	let showPlaceholderMenu = $state(false);

	onMount(() => {
		editor = new Editor({
			element: editorElement,
			extensions: [
				StarterKit.configure({
					heading: {
						levels: [1, 2, 3]
					}
				}),
				Underline,
				Link.configure({
					openOnClick: false,
					HTMLAttributes: {
						style: 'color: #3b82f6; text-decoration: underline;'
					}
				}),
				TextAlign.configure({
					types: ['heading', 'paragraph']
				}),
				TextStyle,
				Color,
				Image.configure({
					inline: true,
					HTMLAttributes: {
						style: 'max-width: 100%; height: auto;'
					}
				})
			],
			content: value,
			editorProps: {
				attributes: {
					class: 'prose prose-sm max-w-none focus:outline-none min-h-[400px] p-4',
					style: 'background: white; color: #1f2937; border-radius: 4px;'
				}
			},
			onUpdate: ({ editor }) => {
				const html = editor.getHTML();
				value = html;
				if (onUpdate) onUpdate(html);
			}
		});
	});

	onDestroy(() => {
		if (editor) {
			editor.destroy();
		}
	});

	// Toolbar actions
	function toggleBold() {
		editor?.chain().focus().toggleBold().run();
	}

	function toggleItalic() {
		editor?.chain().focus().toggleItalic().run();
	}

	function toggleUnderline() {
		editor?.chain().focus().toggleUnderline().run();
	}

	function setHeading(level: 1 | 2 | 3) {
		editor?.chain().focus().toggleHeading({ level }).run();
	}

	function toggleBulletList() {
		editor?.chain().focus().toggleBulletList().run();
	}

	function toggleOrderedList() {
		editor?.chain().focus().toggleOrderedList().run();
	}

	function setTextAlign(align: 'left' | 'center' | 'right') {
		editor?.chain().focus().setTextAlign(align).run();
	}

	function setTextColor(color: string) {
		editor?.chain().focus().setColor(color).run();
	}

	function openLinkDialog() {
		const previousUrl = editor?.getAttributes('link').href;
		linkUrl = previousUrl || '';
		showLinkDialog = true;
	}

	function insertLink() {
		if (linkUrl) {
			editor
				?.chain()
				.focus()
				.extendMarkRange('link')
				.setLink({ href: linkUrl })
				.run();
		}
		showLinkDialog = false;
		linkUrl = '';
	}

	function openImageDialog() {
		showImageDialog = true;
	}

	function insertImage() {
		if (imageUrl) {
			editor?.chain().focus().setImage({ src: imageUrl }).run();
		}
		showImageDialog = false;
		imageUrl = '';
	}

	function insertPlaceholder(placeholder: string) {
		editor?.chain().focus().insertContent(`{{${placeholder}}}`).run();
		showPlaceholderMenu = false;
	}

	function isActive(type: string, attrs?: any) {
		return editor?.isActive(type, attrs) ?? false;
	}
</script>

<div class="email-template-editor space-y-2">
	<!-- Toolbar -->
	<div class="toolbar bg-[var(--color-surface-700)] border border-[var(--color-surface-600)] rounded p-2 flex flex-wrap gap-1">
		<!-- Text Formatting -->
		<button
			onclick={toggleBold}
			class="toolbar-btn {isActive('bold') ? 'active' : ''}"
			title="Bold"
		>
			<svg class="w-4 h-4" fill="currentColor" viewBox="0 0 16 16">
				<path d="M8.21 13c2.106 0 3.412-1.087 3.412-2.823 0-1.306-.984-2.283-2.324-2.386v-.055a2.176 2.176 0 0 0 1.852-2.14c0-1.51-1.162-2.46-3.014-2.46H3.843V13H8.21zM5.908 4.674h1.696c.963 0 1.517.451 1.517 1.244 0 .834-.629 1.32-1.73 1.32H5.908V4.673zm0 6.788V8.598h1.73c1.217 0 1.88.492 1.88 1.415 0 .943-.643 1.449-1.832 1.449H5.907z"/>
			</svg>
		</button>

		<button
			onclick={toggleItalic}
			class="toolbar-btn {isActive('italic') ? 'active' : ''}"
			title="Italic"
		>
			<svg class="w-4 h-4" fill="currentColor" viewBox="0 0 16 16">
				<path d="M7.991 11.674 9.53 4.455c.123-.595.246-.71 1.347-.807l.11-.52H7.211l-.11.52c1.06.096 1.128.212 1.005.807L6.57 11.674c-.123.595-.246.71-1.346.806l-.11.52h3.774l.11-.52c-1.06-.095-1.129-.211-1.006-.806z"/>
			</svg>
		</button>

		<button
			onclick={toggleUnderline}
			class="toolbar-btn {isActive('underline') ? 'active' : ''}"
			title="Underline"
		>
			<svg class="w-4 h-4" fill="currentColor" viewBox="0 0 16 16">
				<path d="M5.313 3.136h-1.23V9.54c0 2.105 1.47 3.623 3.917 3.623s3.917-1.518 3.917-3.623V3.136h-1.23v6.323c0 1.49-.978 2.57-2.687 2.57-1.709 0-2.687-1.08-2.687-2.57V3.136zM12.5 15h-9v-1h9v1z"/>
			</svg>
		</button>

		<div class="h-6 w-px bg-[var(--color-surface-500)] mx-1"></div>

		<!-- Headings -->
		<button
			onclick={() => setHeading(1)}
			class="toolbar-btn {isActive('heading', { level: 1 }) ? 'active' : ''}"
			title="Heading 1"
		>
			H1
		</button>
		<button
			onclick={() => setHeading(2)}
			class="toolbar-btn {isActive('heading', { level: 2 }) ? 'active' : ''}"
			title="Heading 2"
		>
			H2
		</button>
		<button
			onclick={() => setHeading(3)}
			class="toolbar-btn {isActive('heading', { level: 3 }) ? 'active' : ''}"
			title="Heading 3"
		>
			H3
		</button>

		<div class="h-6 w-px bg-[var(--color-surface-500)] mx-1"></div>

		<!-- Lists -->
		<button
			onclick={toggleBulletList}
			class="toolbar-btn {isActive('bulletList') ? 'active' : ''}"
			title="Bullet List"
		>
			<svg class="w-4 h-4" fill="currentColor" viewBox="0 0 16 16">
				<path fill-rule="evenodd" d="M5 11.5a.5.5 0 0 1 .5-.5h9a.5.5 0 0 1 0 1h-9a.5.5 0 0 1-.5-.5zm0-4a.5.5 0 0 1 .5-.5h9a.5.5 0 0 1 0 1h-9a.5.5 0 0 1-.5-.5zm0-4a.5.5 0 0 1 .5-.5h9a.5.5 0 0 1 0 1h-9a.5.5 0 0 1-.5-.5zm-3 1a1 1 0 1 0 0-2 1 1 0 0 0 0 2zm0 4a1 1 0 1 0 0-2 1 1 0 0 0 0 2zm0 4a1 1 0 1 0 0-2 1 1 0 0 0 0 2z"/>
			</svg>
		</button>
		<button
			onclick={toggleOrderedList}
			class="toolbar-btn {isActive('orderedList') ? 'active' : ''}"
			title="Ordered List"
		>
			<svg class="w-4 h-4" fill="currentColor" viewBox="0 0 16 16">
				<path fill-rule="evenodd" d="M5 11.5a.5.5 0 0 1 .5-.5h9a.5.5 0 0 1 0 1h-9a.5.5 0 0 1-.5-.5zm0-4a.5.5 0 0 1 .5-.5h9a.5.5 0 0 1 0 1h-9a.5.5 0 0 1-.5-.5zm0-4a.5.5 0 0 1 .5-.5h9a.5.5 0 0 1 0 1h-9a.5.5 0 0 1-.5-.5z"/>
				<path d="M1.713 11.865v-.474H2c.217 0 .363-.137.363-.317 0-.185-.158-.31-.361-.31-.223 0-.367.152-.373.31h-.59c.016-.467.373-.787.986-.787.588-.002.954.291.957.703a.595.595 0 0 1-.492.594v.033a.615.615 0 0 1 .569.631c.003.533-.502.8-1.051.8-.656 0-1-.37-1.008-.794h.582c.008.178.186.306.422.309.254 0 .424-.145.422-.35-.002-.195-.155-.348-.414-.348h-.3zm-.004-4.699h-.604v-.035c0-.408.295-.844.958-.844.583 0 .96.326.96.756 0 .389-.257.617-.476.848l-.537.572v.03h1.054V9H1.143v-.395l.957-.99c.138-.142.293-.304.293-.508 0-.18-.147-.32-.342-.32a.33.33 0 0 0-.342.338v.041zM2.564 5h-.635V2.924h-.031l-.598.42v-.567l.629-.443h.635V5z"/>
			</svg>
		</button>

		<div class="h-6 w-px bg-[var(--color-surface-500)] mx-1"></div>

		<!-- Alignment -->
		<button
			onclick={() => setTextAlign('left')}
			class="toolbar-btn {isActive({ textAlign: 'left' }) ? 'active' : ''}"
			title="Align Left"
		>
			<svg class="w-4 h-4" fill="currentColor" viewBox="0 0 16 16">
				<path fill-rule="evenodd" d="M2 12.5a.5.5 0 0 1 .5-.5h7a.5.5 0 0 1 0 1h-7a.5.5 0 0 1-.5-.5zm0-3a.5.5 0 0 1 .5-.5h11a.5.5 0 0 1 0 1h-11a.5.5 0 0 1-.5-.5zm0-3a.5.5 0 0 1 .5-.5h7a.5.5 0 0 1 0 1h-7a.5.5 0 0 1-.5-.5zm0-3a.5.5 0 0 1 .5-.5h11a.5.5 0 0 1 0 1h-11a.5.5 0 0 1-.5-.5z"/>
			</svg>
		</button>
		<button
			onclick={() => setTextAlign('center')}
			class="toolbar-btn {isActive({ textAlign: 'center' }) ? 'active' : ''}"
			title="Align Center"
		>
			<svg class="w-4 h-4" fill="currentColor" viewBox="0 0 16 16">
				<path fill-rule="evenodd" d="M4 12.5a.5.5 0 0 1 .5-.5h7a.5.5 0 0 1 0 1h-7a.5.5 0 0 1-.5-.5zm-2-3a.5.5 0 0 1 .5-.5h11a.5.5 0 0 1 0 1h-11a.5.5 0 0 1-.5-.5zm2-3a.5.5 0 0 1 .5-.5h7a.5.5 0 0 1 0 1h-7a.5.5 0 0 1-.5-.5zm-2-3a.5.5 0 0 1 .5-.5h11a.5.5 0 0 1 0 1h-11a.5.5 0 0 1-.5-.5z"/>
			</svg>
		</button>
		<button
			onclick={() => setTextAlign('right')}
			class="toolbar-btn {isActive({ textAlign: 'right' }) ? 'active' : ''}"
			title="Align Right"
		>
			<svg class="w-4 h-4" fill="currentColor" viewBox="0 0 16 16">
				<path fill-rule="evenodd" d="M6 12.5a.5.5 0 0 1 .5-.5h7a.5.5 0 0 1 0 1h-7a.5.5 0 0 1-.5-.5zm-4-3a.5.5 0 0 1 .5-.5h11a.5.5 0 0 1 0 1h-11a.5.5 0 0 1-.5-.5zm4-3a.5.5 0 0 1 .5-.5h7a.5.5 0 0 1 0 1h-7a.5.5 0 0 1-.5-.5zm-4-3a.5.5 0 0 1 .5-.5h11a.5.5 0 0 1 0 1h-11a.5.5 0 0 1-.5-.5z"/>
			</svg>
		</button>

		<div class="h-6 w-px bg-[var(--color-surface-500)] mx-1"></div>

		<!-- Color -->
		<button
			onclick={() => setTextColor('#000000')}
			class="toolbar-btn"
			title="Black"
		>
			<div class="w-4 h-4 rounded" style="background: #000000;"></div>
		</button>
		<button
			onclick={() => setTextColor('#3b82f6')}
			class="toolbar-btn"
			title="Blue"
		>
			<div class="w-4 h-4 rounded" style="background: #3b82f6;"></div>
		</button>
		<button
			onclick={() => setTextColor('#ef4444')}
			class="toolbar-btn"
			title="Red"
		>
			<div class="w-4 h-4 rounded" style="background: #ef4444;"></div>
		</button>

		<div class="h-6 w-px bg-[var(--color-surface-500)] mx-1"></div>

		<!-- Link & Image -->
		<button
			onclick={openLinkDialog}
			class="toolbar-btn {isActive('link') ? 'active' : ''}"
			title="Insert Link"
		>
			<svg class="w-4 h-4" fill="currentColor" viewBox="0 0 16 16">
				<path d="M6.354 5.5H4a3 3 0 0 0 0 6h3a3 3 0 0 0 2.83-4H9c-.086 0-.17.01-.25.031A2 2 0 0 1 7 10.5H4a2 2 0 1 1 0-4h1.535c.218-.376.495-.714.82-1z"/>
				<path d="M9 5.5a3 3 0 0 0-2.83 4h1.098A2 2 0 0 1 9 6.5h3a2 2 0 1 1 0 4h-1.535a4.02 4.02 0 0 1-.82 1H12a3 3 0 1 0 0-6H9z"/>
			</svg>
		</button>
		<button
			onclick={openImageDialog}
			class="toolbar-btn"
			title="Insert Image"
		>
			<svg class="w-4 h-4" fill="currentColor" viewBox="0 0 16 16">
				<path d="M6.002 5.5a1.5 1.5 0 1 1-3 0 1.5 1.5 0 0 1 3 0z"/>
				<path d="M2.002 1a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V3a2 2 0 0 0-2-2h-12zm12 1a1 1 0 0 1 1 1v6.5l-3.777-1.947a.5.5 0 0 0-.577.093l-3.71 3.71-2.66-1.772a.5.5 0 0 0-.63.062L1.002 12V3a1 1 0 0 1 1-1h12z"/>
			</svg>
		</button>

		{#if placeholders && placeholders.length > 0}
			<div class="h-6 w-px bg-[var(--color-surface-500)] mx-1"></div>

			<!-- Placeholders -->
			<div class="relative">
				<button
					onclick={() => showPlaceholderMenu = !showPlaceholderMenu}
					class="toolbar-btn"
					title="Insert Placeholder"
				>
					{`{{}}`}
				</button>
				{#if showPlaceholderMenu}
					<div class="absolute top-full left-0 mt-1 bg-[var(--color-surface-800)] border border-[var(--color-surface-600)] rounded shadow-lg z-50 min-w-[160px]">
						{#each placeholders as placeholder}
							<button
								onclick={() => insertPlaceholder(placeholder)}
								class="block w-full text-left px-3 py-1.5 text-xs font-mono hover:bg-[var(--color-surface-700)] text-[var(--color-text-secondary)] hover:text-[var(--color-accent)]"
							>
								{`{{${placeholder}}}`}
							</button>
						{/each}
					</div>
				{/if}
			</div>
		{/if}
	</div>

	<!-- Editor -->
	<div 
		bind:this={editorElement}
		class="editor-content border border-[var(--color-surface-600)] rounded overflow-auto"
		style="max-height: 600px;"
	></div>
</div>

<!-- Link Dialog -->
{#if showLinkDialog}
	<div class="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onclick={() => showLinkDialog = false}>
		<div class="bg-[var(--color-surface-800)] border border-[var(--color-surface-600)] rounded p-4 w-96" onclick={(e) => e.stopPropagation()}>
			<h3 class="text-sm font-bold text-[var(--color-text-primary)] mb-3">Link einfügen</h3>
			<input
				type="url"
				bind:value={linkUrl}
				placeholder="https://example.com"
				class="w-full px-3 py-2 bg-[var(--color-surface-700)] border border-[var(--color-surface-600)] rounded text-sm text-[var(--color-text-primary)] focus:border-[var(--color-accent)] focus:outline-none mb-3"
			/>
			<div class="flex gap-2 justify-end">
				<button
					onclick={() => { showLinkDialog = false; linkUrl = ''; }}
					class="px-3 py-1.5 text-xs font-mono bg-[var(--color-surface-700)] hover:bg-[var(--color-surface-600)] text-[var(--color-text-secondary)] rounded"
				>
					ABBRECHEN
				</button>
				<button
					onclick={insertLink}
					class="px-3 py-1.5 text-xs font-mono bg-[var(--color-accent)] hover:opacity-90 text-[var(--color-surface-900)] rounded font-bold"
				>
					EINFÜGEN
				</button>
			</div>
		</div>
	</div>
{/if}

<!-- Image Dialog -->
{#if showImageDialog}
	<div class="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onclick={() => showImageDialog = false}>
		<div class="bg-[var(--color-surface-800)] border border-[var(--color-surface-600)] rounded p-4 w-96" onclick={(e) => e.stopPropagation()}>
			<h3 class="text-sm font-bold text-[var(--color-text-primary)] mb-3">Bild einfügen</h3>
			<input
				type="url"
				bind:value={imageUrl}
				placeholder="https://example.com/image.jpg"
				class="w-full px-3 py-2 bg-[var(--color-surface-700)] border border-[var(--color-surface-600)] rounded text-sm text-[var(--color-text-primary)] focus:border-[var(--color-accent)] focus:outline-none mb-3"
			/>
			<div class="flex gap-2 justify-end">
				<button
					onclick={() => { showImageDialog = false; imageUrl = ''; }}
					class="px-3 py-1.5 text-xs font-mono bg-[var(--color-surface-700)] hover:bg-[var(--color-surface-600)] text-[var(--color-text-secondary)] rounded"
				>
					ABBRECHEN
				</button>
				<button
					onclick={insertImage}
					class="px-3 py-1.5 text-xs font-mono bg-[var(--color-accent)] hover:opacity-90 text-[var(--color-surface-900)] rounded font-bold"
				>
					EINFÜGEN
				</button>
			</div>
		</div>
	</div>
{/if}

<style>
	.toolbar-btn {
		padding: 0.375rem;
		font-size: 0.75rem;
		font-weight: 600;
		font-family: var(--font-mono);
		background: var(--color-surface-800);
		color: var(--color-text-secondary);
		border-radius: 4px;
		transition: all 0.2s;
		border: 1px solid transparent;
	}

	.toolbar-btn:hover {
		background: var(--color-surface-600);
		color: var(--color-text-primary);
	}

	.toolbar-btn.active {
		background: var(--color-accent);
		color: var(--color-surface-900);
		border-color: var(--color-accent);
	}

	:global(.ProseMirror) {
		outline: none;
	}

	:global(.ProseMirror p) {
		margin: 0.5rem 0;
	}

	:global(.ProseMirror h1) {
		font-size: 2rem;
		font-weight: bold;
		margin: 1rem 0 0.5rem;
	}

	:global(.ProseMirror h2) {
		font-size: 1.5rem;
		font-weight: bold;
		margin: 1rem 0 0.5rem;
	}

	:global(.ProseMirror h3) {
		font-size: 1.25rem;
		font-weight: bold;
		margin: 1rem 0 0.5rem;
	}

	:global(.ProseMirror ul),
	:global(.ProseMirror ol) {
		padding-left: 1.5rem;
		margin: 0.5rem 0;
	}

	:global(.ProseMirror li) {
		margin: 0.25rem 0;
	}

	:global(.ProseMirror a) {
		color: #3b82f6;
		text-decoration: underline;
	}

	:global(.ProseMirror img) {
		max-width: 100%;
		height: auto;
		border-radius: 4px;
		margin: 0.5rem 0;
	}
</style>
