import { createRouter, createWebHistory } from "vue-router";
import ChatView from "@/views/ChatView.vue";

/** 路由表：当前仅对话页 */
const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [{ path: "/", name: "chat", component: ChatView }],
});

export default router;
