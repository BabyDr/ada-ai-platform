<script setup lang="ts">
/** OBSERVE：眼睛图标 + 右上角 SUCCESS 徽标（稿中观察结果） */
defineProps<{ content: string }>();
</script>

<template>
  <div class="relative overflow-hidden rounded-xl border border-arch-border bg-arch-observe shadow-arch">
    <div class="flex items-center gap-2 border-b border-arch-border/70 bg-white/60 px-4 py-2.5">
      <span class="flex h-7 w-7 items-center justify-center rounded-lg bg-arch-think text-arch-primary">
        <svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
          <circle cx="12" cy="12" r="3" />
        </svg>
      </span>
      <span class="text-[11px] font-bold uppercase tracking-widest text-arch-primary">Observe</span>
      <span
        class="ml-auto rounded-md bg-arch-primary/10 px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide text-arch-primary"
      >
        Success
      </span>
    </div>
    <pre
      class="m-0 max-h-48 overflow-auto whitespace-pre-wrap p-4 font-mono text-xs leading-relaxed text-arch-ink"
    >{{ content }}</pre>
  </div>
</template>
