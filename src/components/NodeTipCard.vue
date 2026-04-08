<template>
  <Transition name="tip-fade">
    <div
      v-if="visible"
      class="node-tip-card mac-glass"
      aria-label="节点操作提示"
    >
      <button
        type="button"
        class="tip-close-btn"
        aria-label="关闭"
        @click="handleClose"
      >
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round">
          <line x1="18" y1="6" x2="6" y2="18" />
          <line x1="6" y1="6" x2="18" y2="18" />
        </svg>
      </button>
      <p class="tip-content">
        单击节点可查看该节点的详细信息，双击节点即可展开/收缩图谱。
      </p>
      <div class="tip-footer">
        <button type="button" class="tip-never-btn" @click="handleNeverShow">
          不再提示
        </button>
      </div>
    </div>
  </Transition>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';

const STORAGE_KEY_NEVER_SHOW = 'kgraph-node-tip-never-show';

const closedThisSession = ref(false);

const visible = computed(() => {
  if (closedThisSession.value) return false;
  try {
    return !localStorage.getItem(STORAGE_KEY_NEVER_SHOW);
  } catch {
    return true;
  }
});

function handleClose() {
  closedThisSession.value = true;
}

function handleNeverShow() {
  try {
    localStorage.setItem(STORAGE_KEY_NEVER_SHOW, '1');
  } catch (_) {}
  closedThisSession.value = true;
}

onMounted(() => {
  // 仅依赖 visible 计算属性，无需额外初始化
});
</script>

<style scoped>
.node-tip-card {
  position: fixed;
  right: 20px;
  bottom: 270px;
  z-index: 26;
  width: 280px;
  padding: 16px 36px 16px 18px;
  border-radius: var(--radius-card);
  box-shadow: var(--panel-shadow);
  pointer-events: auto;
}

.tip-close-btn {
  position: absolute;
  top: 12px;
  right: 12px;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  border-radius: 8px;
  background: transparent;
  color: var(--text-secondary);
  cursor: pointer;
  transition: color 0.2s, background 0.2s;
}

.tip-close-btn:hover {
  color: var(--text-primary);
  background: var(--sidebar-hover);
}

.tip-content {
  margin: 0 0 8px 0;
  padding-right: 8px;
  font-size: 14px;
  line-height: 1.5;
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: 0.02em;
  max-width: 100%;
}

.tip-footer {
  display: flex;
  justify-content: flex-end;
}

.tip-never-btn {
  padding: 6px 14px;
  font-size: 12px;
  font-weight: 500;
  color: #fff;
  background: #007aff;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: opacity 0.2s, background 0.2s;
}

.tip-never-btn:hover {
  background: #0066dd;
  opacity: 0.95;
}

.tip-fade-enter-active,
.tip-fade-leave-active {
  transition: opacity 0.25s ease, transform 0.25s ease;
}

.tip-fade-enter-from,
.tip-fade-leave-to {
  opacity: 0;
  transform: translateY(8px);
}
</style>
