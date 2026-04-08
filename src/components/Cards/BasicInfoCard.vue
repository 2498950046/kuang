<template>
  <div class="card" v-if="gem">
    <h2 class="title">基本信息</h2>
    <div class="info-grid">
      <span class="label">标本名：</span><span>{{ gem.标本名 || gem.specimenName }}</span>
      <span class="label">英文名：</span><span>{{ gem.英文名 || gem.englishName || '-' }}</span>
      <span class="label">矿物名称：</span><span>{{ gem.矿物名称 || gem.mineralName }}</span>
      <span class="label">晶体化学式：</span>
      <span class="mono">{{ gem.晶体化学式 || gem.formula }}</span>
    </div>

    <hr class="separator" />

    <div class="category">
      <span class="label">标本分类：</span>
      <div class="badges">
        <span v-for="c in (gem.标本分类 || gem.category || [])" :key="c" class="badge">{{ c }}</span>
      </div>
    </div>

    <hr class="separator" />

    <div class="info-grid small">
      <span class="label">产地：</span><span>{{ gem.产地 || gem.origin || '-' }}</span>
      <span class="label">年代：</span><span>{{ gem.年代 || gem.era || '-' }}</span>
      <span class="label">编号：</span><span>{{ gem.编号 || gem.code || '-' }}</span>
      <span class="label">捐赠人：</span><span>{{ gem.捐赠人 || gem.donor || '-' }}</span>
    </div>
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
  height: fit-content;
}
.title {
  margin-bottom: 12px;
  opacity: 0.9;
  font-size: 1.2rem;
  font-weight: 600;
}
.info-grid {
  display: grid;
  grid-template-columns: 120px 1fr;
  gap: 6px;
}
.info-grid.small {
  grid-template-columns: 80px 1fr;
  font-size: 0.9em;
}
.label {
  color: rgba(255, 255, 255, 0.7);
}
.mono {
  font-family: monospace;
  font-size: 0.85em;
}
.separator {
  border: none;
  border-top: 1px solid rgba(255, 255, 255, 0.2);
  margin: 12px 0;
}
.badges {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 6px;
}
.badge {
  background: rgba(255, 255, 255, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 4px;
  padding: 2px 8px;
  font-size: 0.85em;
  color: white;
  cursor: pointer;
}
.badge:hover {
  background: rgba(255, 255, 255, 0.3);
}
</style>

