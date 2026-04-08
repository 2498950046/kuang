<template>
  <div class="top-actions" ref="actionsRef">
    <div class="mac-glass action-group">
      <!-- 伸展式搜索框 -->
      <div class="search-container" :class="{ 'expanded': searchExpanded }" @click="handleSearchClick">
        <button
          v-if="!searchExpanded"
          class="mac-icon-btn search-trigger"
          @click="onToggleSearch"
          title="搜索 (Cmd+K)"
        >
          <Search :size="16" />
        </button>
        <div v-else class="search-expanded">
          <!-- 搜索类型选择器 -->
          <select
            v-model="searchType"
            class="search-type-selector"
            @change="onSearchTypeChange"
            :disabled="searchLoading"
          >
            <option value="name">名称</option>
            <option value="location">产地</option>
          </select>

          <Search class="search-icon" :size="16" />
          <input
            ref="searchInputRef"
            v-model="searchKeyword"
            class="search-input"
            :placeholder="getPlaceholder(searchType)"
            @keyup.enter="onSearch"
            @keyup.esc="onCloseSearch"
            :disabled="searchLoading"
          />

          <!-- 加载指示器 -->
          <div v-if="searchLoading" class="search-loading">
            <div class="loading-spinner"></div>
          </div>
          <!-- 新增的关闭按钮 -->
          <button class="mac-icon-btn close-search-btn" @click="onCloseSearch" title="收起搜索">
            <X :size="16" />
          </button>
        </div>
      </div>

      <div class="separator"></div>
      <button class="mac-icon-btn admin-btn" @click="onGoToAdmin" title="后台管理">
        <img :src="adminIcon" alt="管理员" />
      </button>
      <div class="separator" v-if="false"></div>
      <button v-if="false" class="mac-icon-btn" @click="onToggleTheme" title="切换明暗">
        <Sun v-if="theme === 'dark'" :size="16" />
        <Moon v-else :size="16" />
      </button>
    </div>

    <button class="mac-glass mac-pill-btn" @click="onToggleMainView" @mouseenter="hoverBtn" @mouseleave="leaveBtn">
      {{ buttonLabel }}
    </button>
  </div>
</template>

<script setup>
import { ref, nextTick, onMounted, onBeforeUnmount, watch } from 'vue';
import { Sun, Moon, Search, X } from 'lucide-vue-next';
import adminIcon from '@/assets/管理员.png';
import gsap from 'gsap';

const props = defineProps({
  showSearch: { type: Boolean, default: true },
  theme: { type: String, default: 'dark' },
  buttonLabel: { type: String, default: '' },
  searchLoading: { type: Boolean, default: false },
  searchType: { type: String, default: 'name' }
});

const emit = defineEmits(['open-search', 'go-to-admin', 'toggle-theme', 'toggle-main-view', 'update:searchType']);

const actionsRef = ref(null);
const searchInputRef = ref(null);
const searchExpanded = ref(false);
const showCollapseButton = ref(false);
const searchKeyword = ref('');
const searchType = ref(props.searchType);

// 监听外部的searchType变化
watch(() => props.searchType, (newVal) => {
  searchType.value = newVal;
});

// 防止搜索框内部点击冒泡
function handleSearchClick(event) {
  event.stopPropagation();
}

// 切换搜索框展开/收起
function onToggleSearch() {
  onOpenSearch();
}

// 展开搜索框
function onOpenSearch() {
  searchExpanded.value = true;
  nextTick(() => {
    searchInputRef.value?.focus();
  });
}

// 关闭搜索框
function onCloseSearch() {
  searchExpanded.value = false;
  searchKeyword.value = '';
}

// 执行搜索
function onSearch() {
  if (searchKeyword.value.trim()) {
    emit('open-search', searchKeyword.value.trim());
    // 搜索后不自动关闭，让用户可以看到搜索内容
  }
}

// 搜索类型改变
function onSearchTypeChange() {
  emit('update:searchType', searchType.value);
}

// 获取占位符文本
function getPlaceholder(type) {
  switch (type) {
    case 'location':
      return '搜索产地，如：湖南、江西...';
    default:
      return '搜索矿物、产地...';
  }
}

function onGoToAdmin() {
  emit('go-to-admin');
}

function onToggleTheme() {
  emit('toggle-theme');
}

function onToggleMainView() {
  emit('toggle-main-view');
}

const hoverBtn = (e) => gsap.to(e.target, { scale: 1.05, duration: 0.2 });
const leaveBtn = (e) => gsap.to(e.target, { scale: 1, duration: 0.2 });

onMounted(() => {
  // 监听 ESC 键关闭搜索
  const handleKeyDown = (event) => {
    if (event.key === 'Escape' && searchExpanded.value) {
      onCloseSearch();
    }
  };
  document.addEventListener('keydown', handleKeyDown);

  // 清理函数
  onBeforeUnmount(() => {
    document.removeEventListener('keydown', handleKeyDown);
  });
});

defineExpose({
  actionsRef
});
</script>

<style scoped>
.top-actions {
  position: absolute;
  top: 20px;
  right: 20px;
  z-index: 20;
  display: flex;
  flex-direction: row;
  align-items: center;
  justify-content: flex-end;
  gap: 12px;
}

.action-group {
  display: flex;
  align-items: center;
  padding: 4px;
  border-radius: 12px;
}

:deep(.mac-glass) {
  background: var(--glass-bg);
  backdrop-filter: blur(25px) saturate(180%);
  -webkit-backdrop-filter: blur(25px) saturate(180%);
  border: var(--glass-border);
  box-shadow: var(--panel-shadow);
}

.mac-icon-btn {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  border: none;
  background: transparent;
  color: var(--text-primary);
  cursor: pointer;
  display: flex;
  justify-content: center;
  align-items: center;
  transition: background 0.2s;
}

.mac-icon-btn:hover {
  background: var(--sidebar-hover);
}

.admin-btn img {
  width: 18px;
  height: 18px;
  object-fit: contain;
}

.separator {
  width: 1px;
  height: 16px;
  background: var(--text-secondary);
  opacity: 0.2;
  margin: 0 2px;
}

.mac-pill-btn {
  padding: 8px 16px;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  color: var(--text-primary);
  border: var(--glass-border);
}

/* 搜索容器 */
.search-container {
  position: relative;
  display: flex;
  align-items: center;
  border-radius: 8px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  overflow: hidden;
}

.search-container:not(.expanded) {
  width: 32px;
  height: 32px;
}

.search-container.expanded {
  width: 280px;
  height: 32px;
  background: var(--sidebar-hover);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.search-trigger {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.search-expanded {
  display: flex;
  align-items: center;
  width: 100%;
  padding: 0 12px;
  gap: 8px;
}

.search-type-selector {
  background: transparent;
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: var(--text-primary);
  border-radius: 4px;
  padding: 4px 8px;
  font-size: 12px;
  min-width: 60px;
  cursor: pointer;
  outline: none;
}

.search-type-selector:focus {
  border-color: var(--accent-blue);
}

.search-type-selector:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.search-type-selector option {
  background: var(--bg-primary);
  color: var(--text-primary);
}

.search-icon {
  color: var(--text-secondary);
  flex-shrink: 0;
  opacity: 0.6;
}

.close-search-btn {
  margin-left: 8px; /* 给关闭按钮一些左边距 */
  color: var(--text-secondary);
  opacity: 0.8;
}

.close-search-btn:hover {
  color: var(--text-primary);
}

.search-input {
  flex: 1;
  background: transparent;
  border: none;
  outline: none;
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
  min-width: 0;
  padding: 0;
}

.search-input::placeholder {
  color: var(--text-secondary);
  opacity: 0.5;
  font-weight: 400;
}

/* 动画效果 */
.search-container {
  transform-origin: center;
  transition: all 0.4s cubic-bezier(0.25, 0.46, 0.45, 0.94);
}

.search-container.expanded .search-trigger {
  opacity: 0;
  transform: scale(0.8) rotate(180deg);
  pointer-events: none;
}

.search-container:not(.expanded) .search-expanded {
  opacity: 0;
  transform: translateX(-20px) scale(0.9);
  pointer-events: none;
}

.search-container.expanded .search-expanded {
  opacity: 1;
  transform: translateX(0) scale(1);
  pointer-events: auto;
}

.search-input {
  transition: all 0.3s ease;
}

.search-input:focus {
  transform: scale(1.02);
}

.search-input:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.search-loading {
  display: flex;
  align-items: center;
  margin-left: 8px;
}

.loading-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-top: 2px solid var(--accent-blue);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style>

