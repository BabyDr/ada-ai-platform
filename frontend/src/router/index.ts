import { createRouter, createWebHistory } from "vue-router";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", redirect: "/dashboard" },
    { path: "/dashboard", name: "dashboard", component: () => import("../components/DashboardView.vue") },
    { path: "/translation", name: "translation", component: () => import("../components/TranslationView.vue") },
    { path: "/summarization", name: "summarization", component: () => import("../components/SummarizationView.vue") },
    { path: "/chat", name: "chat", component: () => import("../views/ChatView.vue") },
    { path: "/history", name: "history", component: () => import("../components/HistoryView.vue") },
    { path: "/settings", name: "settings", component: () => import("../components/SettingsView.vue") },
    { path: "/:pathMatch(.*)*", redirect: "/dashboard" },
  ],
});

export default router;
