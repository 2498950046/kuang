// main.js
import './style.css';
import { createApp } from 'vue';
import ElementPlus from 'element-plus';
import 'element-plus/dist/index.css';
import 'element-plus/theme-chalk/dark/css-vars.css';
import 'github-markdown-css/github-markdown.css';
import App from './App.vue';
import router from './router';

// 1. 先设置 localStorage（在创建 app 之前），用户删除或隐私模式下可能失败
try {
  localStorage.setItem('vueuse-color-scheme', 'dark');
} catch {}

// 2. 再创建和挂载应用
const app = createApp(App);
app.use(ElementPlus);
app.use(router);
app.mount('#app');