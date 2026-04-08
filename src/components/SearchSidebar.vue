<template>
  <transition name="search-slide">
    <div v-if="visible" class="search-sidebar">
      <div class="search-container">
        <div class="search-input-wrapper">
          <Search class="search-icon" :size="18" />
          <input
            ref="searchInputRef"
            v-model="keyword"
            class="search-input"
            placeholder="搜索矿物、产地..."
            @keyup.enter="onSearch"
            @keyup.esc="onClose"
          />
        </div>
        <button class="search-submit-btn" @click="onSearch" title="搜索">
          <Search :size="18" />
        </button>
      </div>
    </div>
  </transition>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue';
import { Search } from 'lucide-vue-next';

const props = defineProps({
  visible: { type: Boolean, default: false },
  keyword: { type: String, default: '' }
});

const emit = defineEmits(['update:keyword', 'search', 'close']);

const searchInputRef = ref(null);
const keyword = ref(props.keyword);

watch(() => props.keyword, (newVal) => {
  keyword.value = newVal;
});

watch(() => props.visible, (newVal) => {
  if (newVal) {
    nextTick(() => {
      searchInputRef.value?.focus();
    });
  }
});

watch(keyword, (newVal) => {
  emit('update:keyword', newVal);
});

function onSearch() {
  emit('search', keyword.value);
}

function onClose() {
  emit('close');
}

defineExpose({
  searchInputRef
});
</script>

<style scoped>
.search-sidebar {
  position: fixed;
  top: 20px;
  left: 880px;
  z-index: 1000;
  max-width: 366px;
  width: calc(100vw - 40px);
}

.search-container {
  display: flex;
  align-items: center;
  gap: 0;
  background: var(--glass-bg);
  backdrop-filter: blur(25px) saturate(180%);
  -webkit-backdrop-filter: blur(25px) saturate(180%);
  border: var(--glass-border);
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3),
              0 0 0 1px rgba(255, 255, 255, 0.05) inset;
  overflow: hidden;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.dark-theme .search-container {
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5),
              0 0 0 1px rgba(255, 255, 255, 0.08) inset;
}

.search-input-wrapper {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 18px;
  background: transparent;
}

.search-icon {
  color: var(--text-secondary);
  flex-shrink: 0;
  opacity: 0.6;
}

.search-input {
  flex: 1;
  background: transparent;
  border: none;
  outline: none;
  font-size: 15px;
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

.search-submit-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  border: none;
  background: var(--accent-blue);
  color: white;
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  flex-shrink: 0;
  border-radius: 0 12px 12px 0;
}

.search-submit-btn:hover {
  background: #0080ff;
  transform: scale(1.05);
}

.search-submit-btn:active {
  transform: scale(0.98);
}

/* 搜索框滑入/滑出动画 */
.search-slide-enter-active {
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.search-slide-leave-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.search-slide-enter-from {
  transform: translateX(-100%);
  opacity: 0;
}

.search-slide-leave-to {
  transform: translateX(-100%);
  opacity: 0;
}

.search-slide-enter-to,
.search-slide-leave-from {
  transform: translateX(0);
  opacity: 1;
}
</style>

