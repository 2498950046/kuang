<template>
  <div class="mode-navigation">
    <div class="nav-title">功能导航</div>
    <div class="mac-segmented-control">
      <button
        class="segment-item"
        :class="{ active: currentMode === 'nl2cypher' }"
        @click="emit('switch-mode', 'nl2cypher')"
      >
        <Search class="seg-icon" :size="18" />
        <span class="segment-text">图谱查询</span>
        <div v-if="currentMode === 'nl2cypher'" class="active-dot"></div>
      </button>

      <button
        class="segment-item"
        :class="{ active: currentMode === 'rag' }"
        @click="emit('switch-mode', 'rag')"
      >
        <MessageCircle class="seg-icon" :size="18" />
        <span class="segment-text">智能问答</span>
        <div v-if="currentMode === 'rag'" class="active-dot"></div>
      </button>

      <button
        class="segment-item"
        :class="{ active: currentMode === 'appreciation' }"
        @click="emit('switch-mode', 'appreciation')"
      >
        <Mic class="seg-icon" :size="18" />
        <span class="segment-text">智能鉴赏</span>
        <div v-if="currentMode === 'appreciation'" class="active-dot"></div>
      </button>

      <button
        class="segment-item"
        :class="{ active: currentMode === 'deep-learning' }"
        @click="emit('switch-mode', 'deep-learning')"
      >
        <Cpu class="seg-icon" :size="18" />
        <span class="segment-text">&#28145;&#24230;&#23398;&#20064;&#24179;&#21488;</span>
        <div v-if="currentMode === 'deep-learning'" class="active-dot"></div>
      </button>
    </div>
  </div>
</template>

<script setup>
import { Search, MessageCircle, Mic, Cpu } from 'lucide-vue-next';

const { currentMode } = defineProps({
  currentMode: { type: String, required: true },
});

const emit = defineEmits(['switch-mode']);
</script>

<style scoped>
/* 功能导航区域 */
.mode-navigation {
  margin-bottom: 16px;
}

.nav-title {
  font-size: 10px;
  font-weight: 700;
  color: var(--chat-text-sub, #94a3b8);
  text-transform: uppercase;
  letter-spacing: 0.2em;
  margin-bottom: 16px;
  padding-left: 8px;
}

/* 分段控制器（纵向排列，蓝色背景高亮） */
.mac-segmented-control {
  position: relative;
  display: flex;
  flex-direction: column;
  background: transparent;
  border-radius: 8px;
  padding: 0;
  width: 100%;
  gap: 8px;
}

.segment-item {
  position: relative;
  z-index: 2;
  border: none;
  background: transparent;
  font-size: 15px;
  font-weight: 500;
  color: var(--chat-text-sub, #94a3b8);
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 16px;
  border-radius: 12px;
  width: 100%;
  text-align: left;
}

.segment-item:hover {
  background: rgba(30, 41, 59, 0.5); /* slate-800 with opacity */
  color: #cbd5e1; /* slate-300 */
}

.segment-item.active {
  background: rgba(37, 99, 235, 0.2); /* blue-600/20 */
  color: #60a5fa; /* blue-400 */
  font-weight: 500;
  border: 1px solid rgba(59, 130, 246, 0.2); /* blue-500/20 */
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2);
}

.segment-item.active .seg-icon {
  color: #60a5fa; /* blue-400 */
}

.segment-item.active .segment-text {
  color: #60a5fa; /* blue-400 */
}

.seg-icon {
  width: 18px;
  height: 18px;
  flex-shrink: 0;
  color: inherit;
  transition: color 0.2s;
}

.segment-text {
  flex: 1;
  color: inherit;
  transition: color 0.2s;
}

/* 选中状态指示点 */
.active-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #ffffff;
  box-shadow: 0 0 8px rgba(255, 255, 255, 0.8);
  flex-shrink: 0;
  margin-left: auto;
}
</style>

