<script setup lang="ts">
import { ref } from "vue";
import { Settings, AlertTriangle, CheckCircle2, Cpu, Lock, ShieldAlert } from "lucide-vue-next";
import { TONE_STYLES, DEFAULT_GLM_MODEL } from "../types";

interface Props {
  apiConnected: boolean;
}

defineProps<Props>();

const defaultTone = ref<"Professional" | "Conversational" | "Technical" | "Academic" | "Creative">("Professional");
const preferredModel = ref(DEFAULT_GLM_MODEL);
</script>

<template>
  <div class="space-y-6 p-8 max-w-4xl mx-auto" id="settings-view">
    <div class="border-b border-[#26384d]/40 pb-5">
      <h2 class="font-display text-2xl font-bold text-white flex items-center gap-2">
        <Settings class="w-6 h-6 text-[#00a67e]" />
        全局系统设置
      </h2>
      <p class="text-xs text-[#acb5c9] mt-1">查看默认模型行为、密钥配置状态与服务端隔离说明。</p>
    </div>

    <div class="rounded-2xl border border-[#26384d] bg-[#0c1622] p-5 space-y-4">
      <div class="flex items-center justify-between mb-2">
        <div class="flex items-center gap-2">
          <Lock class="w-4 h-4 text-[#00a67e]" />
          <h3 class="text-sm font-semibold text-white">GLM API 密钥状态</h3>
        </div>
        <span
          :class="[
            'px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold uppercase tracking-wide border',
            apiConnected ? 'bg-[#00a67e]/10 text-[#00a67e] border-[#00a67e]/20' : 'bg-red-500/10 text-red-400 border-red-500/20',
          ]"
        >
          {{ apiConnected ? "引擎已就绪" : "离线" }}
        </span>
      </div>

      <p class="text-xs text-[#acb5c9] leading-relaxed">
        Linguist AI 通过 AdaAgent Python Sidecar 调用 GLM，密钥仅保存在服务端，不会暴露给浏览器。
      </p>

      <div class="p-4 rounded-xl bg-[#08121e]/80 border border-[#26384d]/60 space-y-3">
        <div class="flex gap-2.5 items-start text-xs text-white">
          <component
            :is="apiConnected ? CheckCircle2 : AlertTriangle"
            :class="['w-4 h-4 shrink-0 mt-0.5', apiConnected ? 'text-[#00a67e]' : 'text-amber-500']"
          />
          <div>
            <span class="font-semibold block">
              {{ apiConnected ? "密钥已生效，服务已同步。" : "未检测到 GLM_API_KEY 环境变量。" }}
            </span>
            <span class="text-[#acb5c9] text-[11px] leading-relaxed">
              {{
                apiConnected
                  ? "密钥已在 backend/.env 中注册，翻译与总结功能已解锁。"
                  : "请在 backend/.env 中设置 GLM_API_KEY 或 ZHIPU_API_KEY，并重启 Sidecar（npm run sidecar）。"
              }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
      <div id="settings-model-box" class="rounded-2xl border border-[#26384d] bg-[#0c1622] p-5 space-y-4">
        <div class="flex items-center gap-2">
          <Cpu class="w-4 h-4 text-[#00a67e]" />
          <h3 class="text-sm font-semibold text-white">主引擎选择</h3>
        </div>
        <p class="text-xs text-[#acb5c9]">翻译与总结默认使用智谱 GLM OpenAPI。</p>
        <div class="space-y-1.5">
          <label class="block text-[10px] font-mono text-[#acb5c9] uppercase tracking-wider">当前模型</label>
          <select
            v-model="preferredModel"
            disabled
            class="w-full bg-[#122131] border border-[#26384d]/60 rounded-xl px-3 py-2 text-xs text-white outline-none cursor-not-allowed opacity-80"
          >
            <option :value="DEFAULT_GLM_MODEL">{{ DEFAULT_GLM_MODEL }}（推荐，已锁定）</option>
            <option value="glm-4-plus">glm-4-plus（较慢，可选）</option>
          </select>
        </div>
      </div>

      <div id="settings-defaults-box" class="rounded-2xl border border-[#26384d] bg-[#0c1622] p-5 space-y-4">
        <div class="flex items-center gap-2">
          <Settings class="w-4 h-4 text-[#00a67e]" />
          <h3 class="text-sm font-semibold text-white">工作区默认预设</h3>
        </div>
        <p class="text-xs text-[#acb5c9]">新建会话时的默认语调，可在各功能页面临时修改。</p>
        <div class="space-y-1.5">
          <label class="block text-[10px] font-mono text-[#acb5c9] uppercase tracking-wider">默认译文语调</label>
          <select
            v-model="defaultTone"
            class="w-full bg-[#122131] border border-[#26384d]/60 focus:border-[#00a67e] rounded-xl px-3 py-2 text-xs text-white outline-none"
          >
            <option v-for="t in TONE_STYLES" :key="t.value" :value="t.value">{{ t.label }}</option>
          </select>
        </div>
      </div>
    </div>

    <div class="p-4 rounded-xl border border-sky-500/20 bg-sky-500/5 flex items-start gap-3">
      <ShieldAlert class="w-5 h-5 text-sky-400 shrink-0 mt-0.5" />
      <div>
        <span class="text-xs font-semibold text-white block">安全隔离说明</span>
        <span class="text-xs text-[#acb5c9] leading-relaxed block mt-1">
          API 密钥不会出现在浏览器中。所有大模型调用均通过 AdaAgent FastAPI Sidecar（端口 18765）在服务端完成。
        </span>
      </div>
    </div>
  </div>
</template>
