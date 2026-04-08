<template>
  <div class="card" v-if="gem && (gem.材料性质 || gem.properties)">
    <h2 class="title">材料性质</h2>
    <div class="info-grid">
      <!-- 遍历对象的 key-value -->
      <template v-for="(value, key) in (gem.材料性质 || gem.properties)" :key="key">
        <span class="label">{{ key }}：</span>
        <span class="mono">
          <!-- 判断 value 类型 -->
          <template v-if="Array.isArray(value)">
            {{ value.join('、') }}
          </template>
          <template v-else-if="typeof value === 'object'">
            <!-- 如果是对象，进一步展开 -->
            <div class="nested">
              <div v-for="(v, k) in value" :key="k">
                <span class="label">{{ k }}：</span>
                <span>{{ Array.isArray(v) ? v.join('、') : v }}</span>
              </div>
            </div>
          </template>
          <template v-else>
            {{ value }}
          </template>
        </span>
      </template>
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
}
.title {
  margin-bottom: 12px;
  opacity: 0.9;
  font-size: 1.2rem;
  font-weight: 600;
}
.info-grid {
  display: grid;
  grid-template-columns: 140px 1fr;
  gap: 6px;
  font-size: 0.9em;
}
.info-grid.small {
  grid-template-columns: 100px 1fr;
}
.label {
  color: rgba(255, 255, 255, 0.7);
}
.mono {
  font-family: monospace;
  font-size: 0.85em;
}
.nested {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.nested .label {
  display: inline-block;
  margin-right: 4px;
}
</style>

