<script lang="ts">
	let {
		show = $bindable(false),
		subject = '',
		htmlBody = '',
		fromName = '',
		fromEmail = '',
		toFirma = '',
		toEmail = ''
	}: {
		show: boolean;
		subject: string;
		htmlBody: string;
		fromName: string;
		fromEmail: string;
		toFirma: string;
		toEmail: string;
	} = $props();

	let iframeEl: HTMLIFrameElement | undefined = $state();

	$effect(() => {
		if (show && iframeEl && htmlBody) {
			const doc = iframeEl.contentDocument;
			if (doc) {
				doc.open();
				doc.write(`<!DOCTYPE html><html><head><meta charset="utf-8"><style>body{margin:0;padding:16px;font-family:Arial,Helvetica,sans-serif;font-size:14px;line-height:1.6;color:#333;background:#fff;}</style></head><body>${htmlBody}</body></html>`);
				doc.close();
			}
		}
	});

	function close() {
		show = false;
	}
</script>

{#if show}
	<!-- svelte-ignore a11y_no_static_element_interactions -->
	<div
		class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
		onclick={close}
		onkeydown={(e) => e.key === 'Escape' && close()}
	>
		<!-- svelte-ignore a11y_no_static_element_interactions -->
		<div
			class="bg-[var(--color-surface-800)] border border-[var(--color-surface-600)] rounded-lg shadow-2xl w-full max-w-2xl max-h-[90vh] flex flex-col"
			onclick={(e) => e.stopPropagation()}
		>
			<!-- Header -->
			<div class="flex items-center justify-between px-4 py-3 border-b border-[var(--color-surface-600)]">
				<h3 class="text-sm font-mono font-bold text-[var(--color-accent)] uppercase tracking-wide">
					Email-Preview
				</h3>
				<button
					onclick={close}
					class="text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] text-lg leading-none"
				>✕</button>
			</div>

			<!-- Email Meta -->
			<div class="px-4 py-3 space-y-1 border-b border-[var(--color-surface-600)] text-xs font-mono">
				<div class="flex gap-2">
					<span class="text-[var(--color-text-muted)] w-12">Von:</span>
					<span class="text-[var(--color-text-primary)]">{fromName} &lt;{fromEmail}&gt;</span>
				</div>
				<div class="flex gap-2">
					<span class="text-[var(--color-text-muted)] w-12">An:</span>
					<span class="text-[var(--color-text-primary)]">{toFirma} &lt;{toEmail}&gt;</span>
				</div>
				<div class="flex gap-2">
					<span class="text-[var(--color-text-muted)] w-12">Betreff:</span>
					<span class="text-[var(--color-text-primary)] font-bold">{subject}</span>
				</div>
			</div>

			<!-- Email Body (white iframe) -->
			<div class="flex-1 overflow-hidden p-2 min-h-0">
				<iframe
					bind:this={iframeEl}
					title="Email Preview"
					class="w-full h-full min-h-[300px] rounded bg-white border border-[var(--color-surface-600)]"
					sandbox="allow-same-origin"
				></iframe>
			</div>
		</div>
	</div>
{/if}
