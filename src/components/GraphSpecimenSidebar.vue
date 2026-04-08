<template>
  <div class="mac-glass floating-sidebar-inner" :class="{ open: categoryListOpen }">
    <button class="sidebar-header" @click="toggleOpen">
      <div class="sidebar-header-left">
        <img
          :src="changeIcon"
          class="sidebar-switch-img"
          :class="{ rotated: sidebarMode === 'library' }"
          @click.stop="onToggleSidebarMode"
          alt="切换列表"
          title="切换到标本库列表"
        />
        <span class="sidebar-title">图谱列表</span>
      </div>
      <div class="icon-wrapper">
        <ChevronDown class="toggle-icon" :class="{ rotated: categoryListOpen }" :size="14" />
      </div>
    </button>
    <transition name="sidebar-expand">
      <ul v-show="categoryListOpen" class="sidebar-list">
        <li
          v-for="item in specimenList"
          :key="item"
          class="sidebar-item"
          :class="{ active: selectedSpecimenType === item }"
          @click="() => onSpecimenClick(item)"
        >
          <div
            class="dot"
            :style="{
              backgroundColor: specimenColorPalettes[item]?.dotColor || '#007aff',
              boxShadow: `0 0 4px ${specimenColorPalettes[item]?.dotColor || '#007aff'}`
            }"
          ></div>
          <span class="item-text">{{ item }}</span>
          <!-- 在宝玉石项后面添加标本库按钮 -->
          <button
            v-if="item === '宝玉石'"
            class="specimen-library-btn"
            @click.stop="onGoToSpecimenLibrary"
            title="进入宝玉石标本库"
          >
            标本库
          </button>
        </li>
      </ul>
    </transition>
  </div>
</template>

<script setup>
import { ChevronDown } from 'lucide-vue-next';
import changeIcon from '@/assets/change.png';

const props = defineProps({
  categoryListOpen: { type: Boolean, default: true },
  specimenList: { type: Array, default: () => [] },
  selectedSpecimenType: { type: String, default: '' },
  specimenColorPalettes: { type: Object, default: () => ({}) },
  sidebarMode: { type: String, default: 'graph' },
});

const emit = defineEmits([
  'update:categoryListOpen',
  'specimen-click',
  'toggle-sidebar-mode',
  'go-to-specimen-library',
]);

function toggleOpen() {
  emit('update:categoryListOpen', !props.categoryListOpen);
}

function onSpecimenClick(item) {
  emit('specimen-click', item);
}

function onToggleSidebarMode() {
  emit('toggle-sidebar-mode');
}

function onGoToSpecimenLibrary() {
  emit('go-to-specimen-library');
}
</script>

<style scoped>
.floating-sidebar-inner {
  width: 100%;
  overflow: hidden;
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

/* 展开/收缩动画 */
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

.specimen-library-btn {
  margin-left: auto;
  padding: 4px 12px;
  background: #6200EA;
  color: #ffffff;
  border: none;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s ease;
  white-space: nowrap;
}

.specimen-library-btn:hover {
  background: #7B1FA2;
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(98, 0, 234, 0.4);
}

.specimen-library-btn:active {
  transform: translateY(0);
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


