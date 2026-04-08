<template>
  <div class="sidebar-scroll-area" v-if="!isSidebarCollapsed">
    <div class="section-title">
      <span>最近历史</span>
      <button class="text-btn" @click="emit('clear-history')">清空</button>
    </div>

    <div class="history-list">
      <transition-group name="list" tag="div">
        <div
          v-for="item in historyItems"
          :key="item.id"
          class="mac-history-item"
          @click="emit('open-conversation', item.id)"
        >
          <span class="item-icon">
            <Search v-if="item.mode === 'nl2cypher'" :size="14" stroke-width="2.2" />
            <MessageCircle v-else :size="14" stroke-width="2.2" />
          </span>
          <span class="item-text">{{ item.title }}</span>
        </div>
      </transition-group>

      <div v-if="!historyItems.length" class="empty-state">暂无记录</div>
    </div>
  </div>
</template>

<script setup>
import { Search, MessageCircle } from 'lucide-vue-next';

const { historyItems, isSidebarCollapsed } = defineProps({
  historyItems: { type: Array, required: true },
  isSidebarCollapsed: { type: Boolean, required: true },
});

const emit = defineEmits(['clear-history', 'open-conversation']);
</script>

<style scoped>
:global(.mac-layout.sidebar-collapsed .sidebar-scroll-area) {
  display: none;
}

.sidebar-scroll-area {
  flex: 1;
  overflow-y: auto;
}

.section-title {
  display: flex;
  justify-content: space-between;
  font-size: 11px;
  color: var(--chat-text-sub);
  margin-bottom: 8px;
  padding: 0 4px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.text-btn {
  background: none;
  border: none;
  font-size: 11px;
  color: #60a5fa; /* blue-400 */
  cursor: pointer;
  transition: color 0.2s;
}

.text-btn:hover {
  color: #3b82f6; /* blue-500 */
}

.mac-history-item {
  padding: 8px 10px;
  border-radius: 6px;
  font-size: 13px;
  color: var(--chat-text);
  cursor: pointer;
  display: flex;
  gap: 8px;
  align-items: center;
  transition: background 0.2s, border-color 0.2s;
  margin-bottom: 2px;
  border: 1px solid transparent;
}

.mac-history-item:hover {
  background: rgba(30, 41, 59, 0.5); /* slate-800 with opacity */
  border-color: rgba(59, 130, 246, 0.2); /* blue-500/20 */
}

.item-text {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>

