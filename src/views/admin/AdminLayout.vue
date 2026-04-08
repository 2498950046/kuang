<template>
  <div class="admin-layout">
    <router-view />
  </div>
</template>

<script setup>
import { onMounted, onBeforeUnmount } from 'vue';

onMounted(() => {
  // 允许后台页面滚动
  document.body.classList.add('admin-route');
  const app = document.getElementById('app');
  if (app) {
    app.classList.add('admin-route');
  }
});

onBeforeUnmount(() => {
  // 离开后台页面时恢复
  document.body.classList.remove('admin-route');
  const app = document.getElementById('app');
  if (app) {
    app.classList.remove('admin-route');
  }
});
</script>

<style scoped>
.admin-layout {
  min-height: 100vh;
  background: #f6f7fb;
  width: 100%;
  overflow-y: auto;
  overflow-x: hidden;
}
</style>

<style>
/* 后台管理页面允许滚动 */
body.admin-route {
  overflow-y: auto !important;
  overflow-x: hidden !important;
}

#app.admin-route {
  overflow-y: auto !important;
  overflow-x: hidden !important;
  height: auto !important;
  min-height: 100vh;
}
</style>

