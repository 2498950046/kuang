<template>
  <div class="bottom-dock-wrapper" ref="dockRef">
    <transition
      @enter="onDockPanelEnter"
      @leave="onDockPanelLeave"
      :css="false"
    >
      <div 
        v-if="dockPanel" 
        :class="['mac-glass dock-popup-panel', { 'level-panel-wrapper': dockPanel === 'level' }]"
        :style="levelPanelStyle"
        ref="popupPanelRef"
      >
        <StatsPanel
          v-if="dockPanel === 'stats'"
          :total-nodes="stats.totalNodes"
          v-bind="stats"
          :selected-specimen-type="selectedSpecimenType"
          :is-loading="isLoadingStats"
          @run-query="onRunQuery"
          class="mac-compact-grid"
        />
        <LayoutPanel
          v-else-if="dockPanel === 'layout'"
          v-model:layout-config="layoutConfigModel"
          :selected-item="selectedItem"
          :nodes="nodes"
          :entity-category-labels="entityCategoryLabels"
          :edge-type-labels="edgeTypeLabels"
          :property-labels="propertyLabels"
          class="mac-layout-content"
        />
        <div v-else-if="dockPanel === 'level'" class="level-panel">
          <div class="level-label">展开层级:</div>
          <div class="level-options">
            <label
              v-for="level in [1, 2, 3]"
              :key="level"
              :class="['level-option', { active: expandLevel === level }]"
            >
              <input
                type="checkbox"
                :checked="expandLevel === level"
                @change="onLevelChange(level)"
              />
              <span>{{ level }}级: {{ level === 1 ? '分类节点' : level === 2 ? '分类节点，矿物节点' : '所有节点' }}</span>
            </label>
          </div>
        </div>
      </div>
    </transition>

    <div class="mac-glass mac-dock">
      <div class="dock-section">
        <button
          :class="['dock-pill-btn', { active: dockPanel === 'stats' }]"
          @click="onToggleDock('stats')"
        >
          统计
        </button>
        <button
          :class="['dock-pill-btn', { active: dockPanel === 'layout' }]"
          @click="onToggleDock('layout')"
        >
          布局
        </button>
        <button
          :class="['dock-pill-btn', { active: dockPanel === 'level' }]"
          @click="onToggleDock('level')"
          ref="levelButtonRef"
        >
          层级
        </button>
      </div>

      <div class="dock-separator"></div>
      <div class="dock-section">
        <button class="dock-icon-btn" @click="onZoomOut">-</button>
        <span class="dock-label">{{ Math.round(zoomLevel * 100) }}%</span>
        <button class="dock-icon-btn" @click="onZoomIn">+</button>
      </div>

      <div class="dock-separator"></div>
      <div class="dock-section">
        <button 
          :class="['dock-icon-btn', 'gesture-toggle', { active: isGestureEnabled }]"
          @click="onToggleGesture"
          :title="isGestureEnabled ? '关闭手势控制' : '开启手势控制'"
        >
          <!-- <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 2v4M12 18v4M2 12h4M18 12h4" />
          </svg> -->
          <img src="@/assets/hand_finger.png" alt="手势控制" class="hand-finger-icon" >
        </button>
      </div>
      <div class="dock-separator"></div>
      <div class="dock-section">
        <button class="dock-icon-btn" @click="onToggleFullscreen" title="全屏">⛶</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, nextTick } from 'vue';
import gsap from 'gsap';
import StatsPanel from './StatsPanel.vue';
import LayoutPanel from './LayoutPanel.vue';

const props = defineProps({
  dockPanel: { type: String, default: null },
  stats: { type: Object, default: () => ({}) },
  isLoadingStats: { type: Boolean, default: false },
  selectedSpecimenType: { type: String, default: '' },
  layoutConfig: { type: Object, required: true },
  selectedItem: { type: Object, default: null },
  nodes: { type: Array, default: () => [] },
  entityCategoryLabels: { type: Object, default: () => ({}) },
  edgeTypeLabels: { type: Object, default: () => ({}) },
  propertyLabels: { type: Object, default: () => ({}) },
  zoomLevel: { type: Number, default: 1 },
  expandLevel: { type: Number, default: 3 },
  isGestureEnabled: { type: Boolean, default: false }
});

const emit = defineEmits([
  'update:dockPanel',
  'run-query',
  'update:layoutConfig',
  'zoom-in',
  'zoom-out',
  'toggle-fullscreen',
  'update:expandLevel',
  'toggle-gesture'
]);

const dockRef = ref(null);
const popupPanelRef = ref(null);
const levelButtonRef = ref(null);
const levelPanelOffset = ref(0);

const layoutConfigModel = computed({
  get: () => props.layoutConfig,
  set: (val) => emit('update:layoutConfig', val)
});

// 计算层级面板的位置，使其与"层级"按钮对齐
const levelPanelStyle = computed(() => {
  if (props.dockPanel !== 'level') return {};
  return {
    marginLeft: `${levelPanelOffset.value}px`
  };
});

// 计算"层级"按钮的位置
function calculateLevelButtonPosition() {
  if (props.dockPanel !== 'level') return;
  nextTick(() => {
    if (!dockRef.value || !levelButtonRef.value) return;
    
    const dock = dockRef.value.querySelector('.mac-dock');
    if (!dock) return;
    
    const dockRect = dock.getBoundingClientRect();
    const levelButtonRect = levelButtonRef.value.getBoundingClientRect();
    
    // 计算"层级"按钮相对于dock中心的偏移
    const dockCenter = dockRect.left + dockRect.width / 2;
    const levelButtonLeft = levelButtonRect.left;
    // 面板宽度是95px，要让它与按钮的左边对齐
    const offset = levelButtonLeft - dockCenter;
    levelPanelOffset.value = offset;
  });
}

// 监听dockPanel变化，重新计算位置
watch(() => props.dockPanel, (newVal) => {
  if (newVal === 'level') {
    calculateLevelButtonPosition();
  }
});

onMounted(() => {
  if (props.dockPanel === 'level') {
    calculateLevelButtonPosition();
  }
});

function onToggleDock(panel) {
  const newPanel = props.dockPanel === panel ? null : panel;
  emit('update:dockPanel', newPanel);
}

function onRunQuery(cypher) {
  emit('run-query', cypher);
}

function onZoomIn() {
  emit('zoom-in');
}

function onZoomOut() {
  emit('zoom-out');
}

function onToggleFullscreen() {
  emit('toggle-fullscreen');
}

function onLevelChange(level) {
  emit('update:expandLevel', level);
}

function onToggleGesture() {
  emit('toggle-gesture');
}

const onDockPanelEnter = (el, done) => {
  gsap.fromTo(
    el,
    { y: 15, opacity: 0, scale: 0.96 },
    { y: 0, opacity: 1, scale: 1, duration: 0.4, ease: 'back.out(1.4)', onComplete: done }
  );
};

const onDockPanelLeave = (el, done) => {
  gsap.to(el, { y: 10, opacity: 0, scale: 0.98, duration: 0.2, onComplete: done });
};

defineExpose({
  dockRef
});
</script>

<style scoped>
.bottom-dock-wrapper {
  position: absolute;
  bottom: 15px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 30;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

:deep(.mac-glass) {
  background: var(--glass-bg);
  backdrop-filter: blur(25px) saturate(180%);
  -webkit-backdrop-filter: blur(25px) saturate(180%);
  border: var(--glass-border);
  box-shadow: var(--panel-shadow);
}

.mac-dock {
  display: flex;
  align-items: center;
  padding: 6px 8px;
  border-radius: 24px;
  gap: 8px;
}

.dock-section {
  display: flex;
  align-items: center;
  gap: 4px;
}

.dock-pill-btn {
  padding: 6px 16px;
  border-radius: 18px;
  border: none;
  background: var(--dock-pill-bg);
  color: var(--text-secondary);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.25, 0.46, 0.45, 0.94);
}

.dock-pill-btn:hover {
  color: var(--text-primary);
}

.dock-pill-btn.active {
  background: var(--dock-pill-active);
  color: var(--text-primary);
  box-shadow: var(--dock-pill-shadow);
  font-weight: 600;
}

.dock-separator {
  width: 1px;
  height: 20px;
  background: var(--text-secondary);
  opacity: 0.2;
  margin: 0 4px;
}

.dock-icon-btn {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: none;
  background: transparent;
  color: var(--text-primary);
  font-size: 16px;
  cursor: pointer;
  transition: background 0.2s;
}

.dock-icon-btn:hover {
  background: var(--sidebar-hover);
}

.dock-icon-btn.gesture-toggle {
  position: relative;
}
.hand-finger-icon {
  position: absolute;
  top:50%;
  left:50%;
  transform: translate(-50%, -50%);
  width: 20px;
  height: 20px;
}
.dock-icon-btn.gesture-toggle.active {
  background: rgba(59, 130, 246, 0.2);
  color: #3b82f6;
}

.dock-icon-btn.gesture-toggle.active::after {
  content: '';
  position: absolute;
  top: 2px;
  right: 2px;
  width: 6px;
  height: 6px;
  background: #10b981;
  border-radius: 50%;
  animation: pulse 2s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.dock-label {
  min-width: 40px;
  text-align: center;
  font-variant-numeric: tabular-nums;
  font-size: 13px;
  font-weight: 600;
}

.dock-popup-panel {
  padding: 16px;
  border-radius: 20px;
  margin-bottom: 8px;
  width: 420px;
  max-width: 90vw;
  max-height: 50vh;
  overflow-y: auto;
}

.dock-popup-panel.level-panel-wrapper {
  width: 95px;
  min-width: 255px;
  max-width: 95px;
  border-radius: 5px;
  /* margin-left 由 JavaScript 动态计算，与"层级"按钮对齐 */
}

:deep(.mac-compact-grid) {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
}

:deep(.mac-compact-grid > div),
:deep(.stats-card) {
  background: var(--card-bg);
  border: 1px solid rgba(125, 125, 125, 0.1);
  border-radius: 12px;
  padding: 12px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  min-height: 60px;
  transition: transform 0.2s;
}

:deep(.stats-card:hover) {
  transform: translateY(-1px);
}

:deep(.stats-card .label),
:deep(.stats-card h4),
:deep(.mac-compact-grid span:first-child) {
  font-size: 18px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: var(--text-secondary);
  margin-bottom: 2px;
  display: flex;
  align-items: center;
  gap: 4px;
}

:deep(.stats-card .value),
:deep(.stats-card .number),
:deep(.mac-compact-grid strong) {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  font-family: -apple-system, BlinkMacSystemFont, sans-serif;
  line-height: 1.2;
}

:deep(.mac-layout-content) {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 4px;
}

:deep(.layout-row),
:deep(.slider-group) {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

:deep(.layout-row label) {
  font-size: 12px;
  font-weight: 500;
  color: var(--text-primary);
  min-width: 80px;
}

:deep(input[type=range]) {
  -webkit-appearance: none;
  appearance: none;
  background: transparent;
  height: 20px;
  width: 100%;
  cursor: pointer;
}

:deep(input[type=range]::-webkit-slider-runnable-track) {
  height: 4px;
  border-radius: 2px;
  background: rgba(120, 120, 128, 0.2);
}

:deep(input[type=range]::-webkit-slider-thumb) {
  -webkit-appearance: none;
  appearance: none;
  height: 16px;
  width: 16px;
  border-radius: 50%;
  background: #ffffff;
  box-shadow: 0 1px 3px rgba(0,0,0,0.3);
  margin-top: -6px;
  transition: transform 0.1s;
}

.level-panel {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 4px;
}

.level-label {
  font-size: 12px;
  font-weight: 500;
  color: var(--text-primary);
}

.level-options {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.level-option {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 6px 0;
  font-size: 14px;
  color: var(--text-primary);
  user-select: none;
}

.level-option input[type="checkbox"] {
  width: 18px;
  height: 18px;
  cursor: pointer;
  accent-color: #007AFF;
  border-radius: 4px;
}

.level-option.active {
  color: #007AFF;
  font-weight: 600;
}
</style>

