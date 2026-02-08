<script lang="ts">
	import { getScoreColor } from '$lib/utils/scoring';
	interface Props { score: number; }
	let { score }: Props = $props();
	const color = $derived(getScoreColor(score));
</script>

<span
	class="inline-flex items-center justify-center w-10 h-6 rounded text-xs font-bold tabular-nums"
	style="background: {color}25; color: {color}; border: 1px solid {color}50;"
>
	{score}
</span>
