<template>
  <div class="card">
    <h2 class="title">标本描述</h2>
    <p class="text">
     {{ gem.标本描述 || gem.description || '暂无描述' }}
    </p>
  </div>
</template>

<script setup>
const props = defineProps({
  gem: {
    type: Object,
    required: true
  }
});
</script>

<style scoped>
.card {
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 8px;
  padding: 16px;
  backdrop-filter: blur(6px);
  color: white;
}
.title {
  margin-bottom: 8px;
  opacity: 0.9;
  font-size: 1.2rem;
  font-weight: 600;
}
.text {
  color: rgba(255, 255, 255, 0.85);
  line-height: 1.6;
  font-size: 0.9em;
  margin: 0;
}
</style>

