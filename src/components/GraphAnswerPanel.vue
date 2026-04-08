<template>
  <div v-if="answer" class="graph-answer-panel mac-glass" ref="answerRef">
    <div class="answer-header">
      <h4 class="answer-title">查询结果说明</h4>
      <button class="answer-close-btn" @click="onClose" title="关闭">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="18" y1="6" x2="6" y2="18"></line>
          <line x1="6" y1="6" x2="18" y2="18"></line>
        </svg>
      </button>
    </div>
    <div class="answer-content">
      {{ answer }}
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';

const props = defineProps({
  answer: { type: String, default: '' }
});

const emit = defineEmits(['close']);

const answerRef = ref(null);

function onClose() {
  emit('close');
}

defineExpose({
  answerRef
});
</script>

<style scoped>
.graph-answer-panel {
  position: absolute;
  top: 80px;
  right: 20px;
  width: 400px;
  max-width: calc(100% - 40px);
  max-height: 300px;
  border-radius: 12px;
  padding: 0;
  overflow: hidden;
  z-index: 20;
  backdrop-filter: blur(20px) saturate(180%);
  background: var(--panel-bg, rgba(30, 41, 59, 0.8));
  border: 1px solid var(--chat-border, rgba(148, 163, 184, 0.2));
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
}

.answer-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid var(--chat-border, rgba(148, 163, 184, 0.2));
  background: rgba(59, 130, 246, 0.1);
}

.answer-title {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--chat-text, #ffffff);
}

.answer-close-btn {
  background: transparent;
  border: none;
  cursor: pointer;
  padding: 4px;
  color: var(--chat-text-sub, #aeb7c8);
  transition: color 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.answer-close-btn:hover {
  color: var(--chat-text, #ffffff);
}

.answer-content {
  padding: 20px;
  color: var(--chat-text, #e2e8f0);
  font-size: 14px;
  line-height: 1.6;
  max-height: 240px;
  overflow-y: auto;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.answer-content::-webkit-scrollbar {
  width: 6px;
}

.answer-content::-webkit-scrollbar-thumb {
  background: rgba(148, 163, 184, 0.3);
  border-radius: 3px;
}

.answer-content::-webkit-scrollbar-track {
  background: transparent;
}
</style>

