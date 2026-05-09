import { createApp } from "vue";
import { createPinia } from "pinia";
import Antd from "ant-design-vue";
import App from "./App.vue";
import router from "./router";
import "./style.css";

/** 应用入口：样式 → Pinia → 路由 → Ant Design Vue */
const app = createApp(App);
app.use(createPinia());
app.use(router);
app.use(Antd);
app.mount("#app");
