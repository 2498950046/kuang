<template>
  <!--
    说明：真正的页面内容由 App.vue 根据路由(/qa)内部切换 currentView 来渲染。
    这里必须保持为“空壳”，否则会出现 App.vue -> router-view -> QAView -> App.vue 的递归渲染，导致空白/跳转异常。
  -->
  <div class="route-shell" />
</template>

<script setup>
</script>


