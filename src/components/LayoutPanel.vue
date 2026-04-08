<!-- src/components/InfoPanel.vue -->
<template>
  <div class="sidebar-section">
    <div class="section-header" style="display: flex; justify-content: space-between; align-items: center;">
      <h4> </h4>
    </div>

    <!-- 布局设置面板 -->
    <div >
      <div class="style-group">
        <label>节点距离 (斥力) <span>{{ localLayoutConfig.repulsion }}</span></label>
        <input type="range" v-model.number="localLayoutConfig.repulsion" min="100" max="800" step="20">
      </div>
      <div class="style-group">
        <label>边长 <span>{{ localLayoutConfig.edgeLength }}</span></label>
        <input type="range" v-model.number="localLayoutConfig.edgeLength" min="100" max="800" step="20">
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';

// 定义 Props
const props = defineProps({
  selectedItem: Object,
  layoutConfig: {
    type: Object,
    required: true,
  },
  nodes: {
    type: Array,
    required: true,
  },
  entityCategoryLabels: Object,
  edgeTypeLabels: Object,
  propertyLabels: Object,
});

// 定义 Emits
const emit = defineEmits(['update:layoutConfig']);



// 使用 computed 属性来代理 props，以便 v-model 可以安全地更新父组件状态
const localLayoutConfig = computed({
  get: () => props.layoutConfig,
  set: (newValue) => {
    emit('update:layoutConfig', newValue);
  },
});

// --- Helper Functions ---
// 这些辅助函数现在属于这个组件，因为只有它需要
function getEdgeTypeLabel(type) {
  return props.edgeTypeLabels[type] || type;
}

function getNodeName(nodeId) {
  const node = props.nodes.find(n => n.id === nodeId);
  return node ? node.name : '未知节点';
}




</script>

<style scoped>
/* 样式与原 App.vue 中 sidebar-section 和 property-display 相关部分一致 */
.sidebar-section {
  padding: 0 16px;
  min-height: 125px;
  background: transparent;
}

.section-header h4 {
  margin: 0;
  color: var(--text-primary);
}

.toggle-link {
  font-size: 0.8em;
  color: var(--accent-color);
  cursor: pointer;
  font-weight: normal;
}

.style-group {
  margin-bottom: 16px;
}

.style-group label {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  font-size: 0.9em;
  color: var(--text-secondary);
  font-weight: 600;
}

.style-group input[type="range"] {
  width: 100%;
}

.no-properties {
  color: #999;
  font-style: italic;
  text-align: center;
  margin-top: 30px;
  font-size: 14px;
}

.property-display {
  padding: 12px;
  background: var(--bg-secondary);
  border-radius: 8px;
  margin-top: 10px;
  max-height: 400px;
  overflow-y: auto;
}

.node-properties h5,
.edge-properties h5 {
  margin: 0 0 12px 0;
  font-size: 1.1em;
  color: var(--text-primary);
}

.category-tag {
  display: inline-block;
  padding: 2px 6px;
  background: var(--accent-color);
  color: white;
  border-radius: 4px;
  font-size: 0.8em;
  margin-left: 8px;
}

.property-item {
  display: flex;
  margin-bottom: 8px;
  font-size: 0.9em;
}

.property-key {
  font-weight: 500;
  color: var(--text-secondary);
  min-width: 80px;
  display: inline-block;
}

.property-value {
  color: var(--text-primary);
  flex: 1;
}

.no-hover {
  padding: 12px;
  color: var(--text-muted);
  text-align: center;
  font-size: 0.9em;
}


/* 添加到现有的样式中 */
.property-item {
  padding: 6px 0;
  border-bottom: 1px solid var(--border-color);
}

.property-item:last-child {
  border-bottom: none;
}

.property-key {
  color: var(--text-secondary);
  min-width: 80px;
  font-weight: 500;
}

.property-value {
  color: var(--text-primary);
  white-space: pre-line;
  /* 保留换行符 */
}
</style>
