<script setup lang="ts">
/** 全局设置页：API 密钥状态、默认模型与语调（模型选择当前为只读占位）。 */
import { computed, ref } from "vue";
import {
  Settings,
  AlertTriangle,
  CheckCircle2,
  Cpu,
  Lock,
  ShieldAlert,
} from "lucide-vue-next";
import { TONE_STYLES, DEFAULT_GLM_MODEL } from "../types";
import { useWorkspaceStore } from "../stores/workspace";

const workspace = useWorkspaceStore();
const apiConnected = computed(() => workspace.apiConnected);

const defaultTone = ref<
  "Professional" | "Conversational" | "Technical" | "Academic" | "Creative"
>("Professional");
const preferredModel = ref(DEFAULT_GLM_MODEL);

const modelOptions = [
  { value: DEFAULT_GLM_MODEL, label: `${DEFAULT_GLM_MODEL}（推荐，已锁定）` },
  { value: "glm-4-plus", label: "glm-4-plus（较慢，可选）" },
];
const toneOptions = TONE_STYLES.map((t) => ({
  value: t.value,
  label: t.label,
}));
</script>

<template>
  <div
    class="space-y-6 p-4 sm:p-6 md:p-8 max-w-6xl mx-auto w-full min-w-0 overflow-x-hidden"
    id="settings-view"
  >
    <div class="border-b border-[var(--color-outline-variant)]/40 pb-5">
      <h2
        class="font-display text-2xl font-bold text-ui flex items-center gap-2"
      >
        <Settings class="w-6 h-6 text-[#00a67e]" />
        全局系统设置
      </h2>
      <p class="text-xs text-ui-muted mt-1">
        查看默认模型行为、密钥配置状态与服务端隔离说明。
      </p>
    </div>

    <div
      class="rounded border border-[var(--color-outline-variant)] bg-[var(--color-surface)] p-5 space-y-4"
    >
      <div class="flex items-center justify-between mb-2">
        <div class="flex items-center gap-2">
          <Lock class="w-4 h-4 text-[#00a67e]" />
          <div class="text-sm font-semibold text-ui">GLM API 密钥状态</div>
        </div>
        <span
          :class="[
            'px-2.5 py-0.5 rounded text-[10px] font-mono font-bold uppercase tracking-wide border',
            apiConnected
              ? 'bg-[#00a67e]/10 text-[#00a67e] border-[#00a67e]/20'
              : 'bg-red-500/10 text-red-400 border-red-500/20',
          ]"
        >
          {{ apiConnected ? "引擎已就绪" : "离线" }}
        </span>
      </div>

      <p class="text-xs text-ui-muted leading-relaxed mb-1!">
        AdaWorks AI通过 AdaWorks Python Sidecar 调用
        GLM，密钥仅保存在服务端，不会暴露给浏览器。
      </p>

      <div
        class="p-4 rounded bg-[var(--color-surface-header)]/80 border border-[var(--color-outline-variant)]/60 space-y-3"
      >
        <div class="flex gap-2.5 items-start text-xs text-ui">
          <component
            :is="apiConnected ? CheckCircle2 : AlertTriangle"
            :class="[
              'w-4 h-4 shrink-0 mt-0.5',
              apiConnected ? 'text-[#00a67e]' : 'text-amber-500',
            ]"
          />
          <div>
            <span class="font-semibold block">
              {{
                apiConnected
                  ? "密钥已生效，服务已同步。"
                  : "未检测到 GLM_API_KEY 环境变量。"
              }}
            </span>
            <span class="text-ui-muted text-[11px] leading-relaxed">
              {{
                apiConnected
                  ? "密钥已在 backend/.env 中注册，翻译与总结功能已解锁。"
                  : "请在 backend/.env 中设置 GLM_API_KEY，并重启 Sidecar（npm run sidecar）。"
              }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
      <div
        id="settings-model-box"
        class="rounded border border-[var(--color-outline-variant)] bg-[var(--color-surface)] p-5 space-y-4"
      >
        <div class="flex items-center gap-2">
          <Cpu class="w-4 h-4 text-[#00a67e]" />
          <div class="text-sm font-semibold text-ui">主引擎选择</div>
        </div>
        <p class="text-xs text-ui-muted">
          翻译与总结默认使用智谱 GLM OpenAPI。
        </p>
        <div class="space-y-1.5 mt-1">
          <label
            class="block text-[10px] font-mono text-ui-muted uppercase tracking-wider"
            >当前模型</label
          >
          <a-select
            v-model:value="preferredModel"
            size="small"
            disabled
            :options="modelOptions"
            class="form-select w-full"
          />
        </div>
      </div>

      <div
        id="settings-defaults-box"
        class="rounded border border-[var(--color-outline-variant)] bg-[var(--color-surface)] p-5 space-y-4"
      >
        <div class="flex items-center gap-2">
          <Settings class="w-4 h-4 text-[#00a67e]" />
          <div class="text-sm font-semibold text-ui">工作区默认预设</div>
        </div>
        <p class="text-xs text-ui-muted">
          新建会话时的默认语调，可在各功能页面临时修改。
        </p>
        <div class="space-y-1.5 mt-1">
          <label
            class="block text-[10px] font-mono text-ui-muted uppercase tracking-wider"
            >默认译文语调</label
          >
          <a-select
            v-model:value="defaultTone"
            size="small"
            :options="toneOptions"
            class="form-select w-full"
          />
        </div>
      </div>
    </div>

    <div
      class="p-4 rounded border border-sky-500/20 bg-sky-500/5 flex items-start gap-3"
    >
      <ShieldAlert class="w-5 h-5 text-sky-400 shrink-0 mt-0.5" />
      <div>
        <span class="text-xs font-semibold text-ui block">安全隔离说明</span>
        <span class="text-xs text-ui-muted leading-relaxed block mt-1">
          API 密钥不会出现在浏览器中。所有大模型调用均通过 AdaWorks FastAPI
          Sidecar（端口 18765）在服务端完成。
        </span>
      </div>
    </div>
  </div>
</template>
