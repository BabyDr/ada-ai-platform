<script setup lang="ts">
/** 全局侧栏导航：路由菜单、主题切换、API 连接状态指示。 */
import { computed } from "vue";
import { useRoute } from "vue-router";

const props = withDefaults(
  defineProps<{
    /** 嵌入 Drawer 时使用全高布局，去掉 sticky 与固定宽度。 */
    embedded?: boolean;
  }>(),
  { embedded: false },
);

const emit = defineEmits<{
  navigate: [];
}>();
import {
  Sparkles,
  Sparkle,
  FlaskConical,
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
const llmMode = computed(() => workspace.llmMode);

const menuItems = [
  {
    name: "dashboard",
    title: "Dashboard",
    label: "工作台",
    icon: LayoutDashboard,
  },
  {
    name: "translation",
    title: "Translation",
    label: "文本翻译",
    icon: Languages,
  },
  {
    name: "summarization",
    title: "Summarizer",
    label: "智能要点总结",
    icon: FileText,
  },
  {
    name: "chat",
    title: "Agent Chat",
    label: "智能体对话",
    icon: MessageSquare,
  },
  {
    name: "history",
    title: "History Logs",
    label: "API 运行日志",
    icon: History,
  },
  { name: "settings", title: "Settings", label: "全局设置", icon: Settings },
] as const;
</script>

<template>
  <aside
    id="sidebar-container"
    :class="[
      'bg-(--color-background) flex flex-col justify-between shrink-0',
      props.embedded
        ? 'h-full w-full'
        : 'w-64 border-r ui-border h-screen sticky top-0',
    ]"
  >
    <div class="p-6">
      <div class="flex items-center justify-between gap-3">
        <div class="flex items-center gap-3 min-w-0">
          <div
            class="w-10 h-10 rounded bg-linear-to-tr from-[#00a67e]/20 to-[#00a67e]/40 border border-[#00a67e]/40 flex items-center justify-center shrink-0"
          >
            <Sparkles class="w-5 h-5 text-[#00a67e]" />
          </div>
          <div class="min-w-0">
            <h1
              class="font-display font-semibold text-ui tracking-wide text-base leading-tight"
            >
              AdaWorks
            </h1>
            <span
              class="font-mono text-[10px] text-ui-subtle tracking-wider"
              >AI Workbench v0.x</span
            >
          </div>
        </div>
        <a-button
          type="text"
          size="small"
          shape="circle"
          class="icon-only-btn shrink-0"
          :title="workspace.isDark ? '切换浅色主题' : '切换深色主题'"
          @click="workspace.toggleTheme()"
        >
          <template #icon>
            <component
              :is="workspace.isDark ? Sun : Moon"
              class="w-4 h-4 text-[#00a67e]"
            />
          </template>
        </a-button>
      </div>
    </div>

    <nav class="flex-1 px-4 space-y-1">
      <router-link
        v-for="item in menuItems"
        :key="item.name"
        :id="'sidebar-btn-' + item.name"
        :to="{ name: item.name }"
        @click="emit('navigate')"
        :class="[
          'w-full flex items-center gap-3 px-4 py-3 rounded text-sm font-medium transition-all duration-150',
          route.name === item.name
            ? 'sidebar-nav-active'
            : 'sidebar-nav-inactive',
        ]"
      >
        <component
          :is="item.icon"
          :class="[
            'w-4 h-4 shrink-0',
            route.name === item.name ? 'text-[#00a67e]' : 'text-ui-muted',
          ]"
        />
        <div class="flex flex-col items-start leading-tight">
          <span class="text-xs text-ui-muted">{{ item.title }}</span>
          <span class="text-[10px] font-medium text-ui-subtle">{{
            item.label
          }}</span>
        </div>
      </router-link>
    </nav>

    <div class="p-4 border-t ui-border bg-(--color-sidebar-footer-bg)">
      <div class="flex gap-2 mb-2">
        <span
          v-if="apiConnected"
          class="flex-1 justify-center px-2 py-1 rounded text-[10px] font-mono tracking-wider font-semibold text-[#00a67e] bg-[#00a67e]/10 border border-[#00a67e]/30 flex items-center gap-1 whitespace-nowrap"
        >
          <Sparkle class="w-2.5 h-2.5 animate-pulse shrink-0" />
          工作区已就绪
        </span>
        <span
          v-else
          class="flex-1 justify-center px-2 py-1 rounded text-[10px] font-mono tracking-wider font-semibold text-red-400 bg-red-500/10 border border-red-500/30 flex items-center gap-1 whitespace-nowrap"
        >
          <AlertCircle class="w-2.5 h-2.5 shrink-0" />
          工作区未就绪
        </span>
        <span
          v-if="llmMode === 'mock'"
          class="flex-1 justify-center px-2 py-1 rounded text-[10px] font-mono tracking-wider font-semibold text-amber-300 bg-amber-500/10 border border-amber-500/30 flex items-center gap-1 whitespace-nowrap"
          title="当前为 Mock 模式，未调用真实大模型"
        >
          <FlaskConical class="w-2.5 h-2.5 shrink-0" />
          Mock 模式
        </span>
      </div>
      <div
        class="flex items-center justify-between p-3 rounded bg-(--color-sidebar-status-bg) border ui-border"
      >
        <div class="flex items-center gap-2">
          <div class="relative flex h-2 w-2">
            <span
              v-if="apiConnected"
              class="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#00a67e] opacity-75"
            ></span>
            <span
              :class="[
                'relative inline-flex rounded-full h-2 w-2',
                apiConnected ? 'bg-[#00a67e]' : 'bg-red-400',
              ]"
            ></span>
          </div>
          <div class="flex flex-col">
            <span
              class="text-[10px] font-mono font-semibold text-ui uppercase tracking-wider"
            >
              {{ apiConnected ? "系统正常" : "需配置密钥" }}
            </span>
            <span class="text-[9px] text-ui-subtle mt-1">
              {{ apiConnected ? "API 已连接" : "请查看设置" }}
            </span>
          </div>
        </div>
        <component
          :is="apiConnected ? CheckCircle2 : AlertCircle"
          :class="['w-4 h-4', apiConnected ? 'text-[#00a67e]' : 'text-red-400']"
        />
      </div>
    </div>
  </aside>
</template>
