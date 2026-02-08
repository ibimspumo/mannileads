<script lang="ts">
	import type { ScoreBreakdownItem } from '$lib/types/lead';
	interface Props { items: ScoreBreakdownItem[]; }
	let { items }: Props = $props();
</script>

<div class="space-y-2">
	{#each items as item}
		<div class="flex items-center justify-between text-sm">
			<div class="flex items-center gap-2">
				<span class={item.erfuellt ? 'text-green-400' : 'text-[var(--color-text-muted)]'}>
					{item.erfuellt ? '✓' : '✗'}
				</span>
				<span class={item.erfuellt ? 'text-[var(--color-text-primary)]' : 'text-[var(--color-text-muted)]'}>
					{item.label}
				</span>
			</div>
			<span class="tabular-nums text-xs font-mono {item.erfuellt ? 'text-green-400' : 'text-[var(--color-text-muted)]'}">
				{item.punkte}/{item.maxPunkte}
			</span>
		</div>
	{/each}
</div>
