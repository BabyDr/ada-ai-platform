<script setup lang="ts">
import { computed } from "vue";
import { useRoute } from "vue-router";
import {
  Sparkles,
  LayoutDashboard,
  Languages,
  FileText,
  History,
  Settings,
  CheckCircle2,
  AlertCircle,
  MessageSquare,
  Sun,
  Moon,
} from "lucide-vue-next";
import { useWorkspaceStore } from "../stores/workspace";

const route = useRoute();
const workspace = useWorkspaceStore();
const apiConnected = computed(() => workspace.apiConnected);

const menuItems = [
  { name: "dashboard", title: "Dashboard", label: "工作台", icon: LayoutDashboard },
  { name: "translation", title: "Translation", label: "文本翻译", icon: Languages },
  { name: "summarization", title: "Summarizer", label: "智能要点总结", icon: FileText },
  { name: "chat", title: "Agent Chat", label: "智能体对话", icon: MessageSquare },
  { name: "history", title: "History Logs", label: "API 运行日志", icon: History },
  { name: "settings", title: "Settings", label: "全局设置", icon: Settings },
] as const;
</script>

<template>
  <aside
    id="sidebar-container"
    class="w-64 border-r border-[#26384d] bg-[#020c15] flex flex-col justify-between h-screen sticky top-0 shrink-0"
  >
    <div class="p-6">
      <div class="flex items-center gap-3">
        <div
          class="w-10 h-10 rounded-xl bg-gradient-to-tr from-[#00a67e]/20 to-[#00a67e]/40 border border-[#00a67e]/40 flex items-center justify-center"
        >
          <Sparkles class="w-5 h-5 text-[#00a67e]" />
        </div>
        <div>
          <h1 class="font-display font-semibold text-white tracking-wide text-base leading-tight">Linguist AI</h1>
          <span class="font-mono text-[10px] text-[#bccac2] uppercase tracking-wider">工作区 v1.2</span>
        </div>
      </div>
    </div>

    <nav class="flex-1 px-4 space-y-1">
      <router-link
        v-for="item in menuItems"
        :key="item.name"
        :id="'sidebar-btn-' + item.name"
        :to="{ name: item.name }"
        :class="[
          'w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-all duration-150',
          route.name === item.name
            ? 'bg-gradient-to-r from-[#2c3a4c] to-[#162537] text-white border-l-2 border-[#00a67e]'
            : 'text-[#acb5c9] hover:text-white hover:bg-[#162537]/50',
        ]"
      >
        <component
          :is="item.icon"
          :class="['w-4 h-4 shrink-0', route.name === item.name ? 'text-[#00a67e]' : 'text-[#acb5c9]']"
        />
        <div class="flex flex-col items-start leading-tight">
          <span class="text-xs text-[#acb5c9]">{{ item.title }}</span>
          <span class="text-[10px] font-medium text-[#bccac2]/70">{{ item.label }}</span>
        </div>
      </router-link>
    </nav>

    <div class="p-4 border-t border-[#26384d] bg-[#01060c]/60 space-y-3">
      <button
        type="button"
        id="theme-toggle"
        @click="workspace.toggleTheme()"
        class="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-xl bg-[#08121e]/80 border border-[#26384d]/60 text-[#acb5c9] hover:text-white hover:border-[#00a67e]/50 text-xs font-medium transition-colors cursor-pointer"
      >
        <component :is="workspace.isDark ? Sun : Moon" class="w-3.5 h-3.5 text-[#00a67e]" />
        <span>{{ workspace.isDark ? "切换浅色主题" : "切换深色主题" }}</span>
      </button>

      <div class="flex items-center justify-between p-3 rounded-xl bg-[#08121e]/80 border border-[#26384d]/60">
        <div class="flex items-center gap-2">
          <div class="relative flex h-2 w-2">
            <span
              v-if="apiConnected"
              class="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#00a67e] opacity-75"
            ></span>
            <span :class="['relative inline-flex rounded-full h-2 w-2', apiConnected ? 'bg-[#00a67e]' : 'bg-red-400']"></span>
          </div>
          <div class="flex flex-col">
            <span class="text-[10px] font-mono font-semibold text-white uppercase tracking-wider">
              {{ apiConnected ? "系统正常" : "需配置密钥" }}
            </span>
            <span class="text-[9px] text-[#bccac2]/80">
              {{ apiConnected ? "API 已连接" : "请查看设置" }}
            </span>
          </div>
        </div>
        <component :is="apiConnected ? CheckCircle2 : AlertCircle" :class="['w-4 h-4', apiConnected ? 'text-[#00a67e]' : 'text-red-400']" />
      </div>
    </div>
  </aside>
</template>
