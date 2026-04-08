<template>
  <div
    class="mac-glass floating-sidebar"
    :class="{ open: libraryListOpen }"
    ref="sidebarRef"
  >
    <button class="sidebar-header" @click="libraryListOpen = !libraryListOpen">
      <div class="sidebar-header-left">
        <img
          :src="changeIcon"
          class="sidebar-switch-img"
          :class="{ rotated: sidebarMode === 'graph' }"
          @click.stop="$emit('switch-mode')"
          alt="切换列表"
          title="切换到图谱列表"
        />
      <span class="sidebar-title">标本库列表</span>
      </div>
      <div class="icon-wrapper">
        <ChevronDown class="toggle-icon" :class="{ rotated: libraryListOpen }" :size="14" />
      </div>
    </button>
    <transition name="sidebar-expand">
      <ul v-show="libraryListOpen" class="sidebar-list">
        <li 
          class="sidebar-item"
          :class="{ active: selectedLibrary === '宝玉石' }"
          @click="handleLibraryClick('宝玉石')"
        >
          <div class="dot" style="background-color: #6200EA; box-shadow: 0 0 4px #6200EA;"></div>
          <span class="item-text">宝玉石</span>
        </li>
      </ul>
    </transition>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue';
import { ChevronDown } from 'lucide-vue-next';
import { useRouter, useRoute } from 'vue-router';
import changeIcon from '@/assets/change.png';

const props = defineProps({
  isGraphView: Boolean,
  sidebarMode: {
    type: String,
    default: 'graph',
  },
});

const emit = defineEmits(['switch-mode']);

const router = useRouter();
const route = useRoute();
const libraryListOpen = ref(true);
const selectedLibrary = ref(null);

// 监听路由变化，更新选中状态
watch(() => route.path, (newPath) => {
  if (newPath.startsWith('/specimen-library/')) {
    const parts = newPath.split('/');
    if (parts.length >= 3) {
      selectedLibrary.value = parts[2];
    }
  } else {
    selectedLibrary.value = null;
  }
}, { immediate: true });

function handleLibraryClick(library) {
  selectedLibrary.value = library;
  router.push({
    name: 'specimen-library',
    params: { type: library },
  });
}
</script>

<style scoped>
.floating-sidebar {
  position: fixed !important;
  top: 20px !important;
  left: 20px !important;
  width: 180px;
  border-radius: var(--radius-card);
  z-index: 120 !important;
  overflow: hidden;
  transition: all 0.3s ease;
  pointer-events: auto !important;
  display: block !important;
  visibility: visible !important;
  opacity: 1 !important;
  background: var(--glass-bg);
  backdrop-filter: blur(25px) saturate(180%);
  -webkit-backdrop-filter: blur(25px) saturate(180%);
  border: var(--glass-border);
  box-shadow: var(--panel-shadow);
}

.sidebar-header {
  width: 100%;
  padding: 14px 16px;
  background: transparent;
  border: none;
  display: flex;
  justify-content: space-between;
  align-items: center;
  color: var(--text-primary);
  cursor: pointer;
}

.sidebar-header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.sidebar-switch-img {
  width: 22px;
  height: 22px;
  object-fit: contain;
  cursor: pointer;
  transition: transform 0.25s ease, opacity 0.2s ease;
  filter: drop-shadow(0 0 4px rgba(0, 0, 0, 0.35));
  opacity: 0.9;
}

.sidebar-switch-img:hover {
  opacity: 1;
  transform: scale(1.04);
}

.sidebar-switch-img.rotated {
  transform: rotate(180deg);
}

.sidebar-title {
  font-weight: 600;
  font-size: 15px;
  letter-spacing: 0.5px;
  color: var(--text-primary);
}

.sidebar-list {
  padding: 0 8px 8px;
  margin: 0;
  list-style: none;
  overflow: hidden;
}

.sidebar-expand-enter-active,
.sidebar-expand-leave-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
}

.sidebar-expand-enter-from {
  max-height: 0;
  opacity: 0;
  padding-top: 0;
  padding-bottom: 0;
}

.sidebar-expand-leave-to {
  max-height: 0;
  opacity: 0;
  padding-top: 0;
  padding-bottom: 0;
}

.sidebar-expand-enter-to,
.sidebar-expand-leave-from {
  max-height: 500px;
  opacity: 1;
}

.sidebar-item {
  padding: 8px 12px;
  margin-bottom: 2px;
  border-radius: 6px;
  font-size: 13px;
  color: var(--text-secondary);
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  transition: background 0.2s, color 0.2s;
}

.sidebar-item:hover {
  background: var(--sidebar-hover);
  color: var(--text-primary);
}

.sidebar-item.active {
  background: rgba(0, 122, 255, 0.15);
  color: var(--accent-blue);
  font-weight: 600;
}

.sidebar-item.active .dot {
  box-shadow: 0 0 8px currentColor;
}

.dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  transition: all 0.2s ease;
}

.toggle-icon {
  transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  color: var(--text-secondary);
}

.icon-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
}

.toggle-icon.rotated {
  transform: rotate(180deg);
}
</style>

