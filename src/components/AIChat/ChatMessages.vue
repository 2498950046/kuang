<template>
  <div class="messages-container" ref="messagesContainer">
    <transition @enter="onWelcomeEnter" :css="false">
      <div v-if="currentMessages && currentMessages.length === 0" class="mac-welcome-card">
        <div class="welcome-icon">{{ currentMode === 'nl2cypher' ? '🔍' : '💬' }}</div>
        <h3>{{ currentMode === 'nl2cypher' ? '图谱查询模式' : '智能问答模式' }}</h3>
        <p>{{ currentMode === 'nl2cypher' ? '自然语言转图谱查询，结果可视化展示。' : '基于知识库的深度问答与推理。' }}</p>

        <div class="suggestion-grid">
          <div
            v-for="(q, idx) in exampleQuestions"
            :key="idx"
            class="suggestion-chip"
            @click="setQuestion(q)"
          >
            {{ q }}
          </div>
        </div>
      </div>
    </transition>

    <div
      v-for="(message, index) in currentMessages"
      :key="message.id || index"
      class="message-row"
      :class="message.type"
    >
      <div class="avatar" :class="{ 'avatar-with-image': message.type === 'assistant' }">
        <img v-if="message.type === 'assistant'" :src="aiAvatar" alt="AI" class="avatar-image" />
        <span v-else>{{ message.type === 'user' ? 'U' : 'AI' }}</span>
      </div>

      <div class="bubble-wrapper">
        <div class="bubble-meta">
          <span class="time">{{ formatTime(message.timestamp) }}</span>
        </div>

        <div
          :class="['mac-bubble', message.type, { 'error-bubble': !message.success && message.type === 'assistant' }]"
        >
          <div v-if="message.type === 'user'">{{ message.content }}</div>

          <div v-else-if="message.mode === 'nl2cypher'" class="ai-content">
            <div v-if="message.success">
              <div class="code-block-mac">
                <div class="code-header">Cypher Query</div>
                <code>{{ message.cypher }}</code>
              </div>
              <div
                class="success-tag"
                @click="rerunGraph(message)"
                title="点击重新在图谱中展示结果"
              >
                ✅ 已找到 {{ message.data?.nodes?.length || 0 }} 节点 / {{ message.data?.links?.length || 0 }} 关系
              </div>
            </div>
            <div v-else class="error-content">
              <p>❌ {{ message.error }}</p>
            </div>
          </div>

          <div v-else-if="message.mode === 'rag'" class="ai-content">
            
            <div 
              :class="['markdown-body', { 'streaming-text': message.id === currentStreamingMessageId }]"
              v-html="formatAnswer(message.content || '')"
            ></div>

            <div v-if="message.references && message.references.length > 0" class="references-section">
              <div class="references-title">参考资料</div>
              <ul class="references-list">
                <li 
                  v-for="(ref, refIdx) in message.references" 
                  :key="refIdx" 
                  class="reference-item"
                  @click="$emit('show-reference', ref)"
                >
                  <span class="reference-icon">📄</span>
                  <span class="reference-name">{{ ref.documentName || ref.document_name }}</span>
                </li>
              </ul>
            </div>

            <div v-if="message.context && showContext" class="mac-disclosure">
              <details>
                <summary>📚 参考资料来源</summary>
                <div class="disclosure-content" v-html="formatContext(message.context)"></div>
              </details>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, ref, toRefs, watch } from 'vue';
import gsap from 'gsap';
import MarkdownIt from 'markdown-it';

const md = new MarkdownIt();

const props = defineProps({
  currentMode: { type: String, required: true },
  currentMessages: { type: Array, required: true },
  streamingMessage: { type: String, default: '' },
  currentStreamingMessageId: { type: [String, Number, null], default: null },
  showContext: { type: Boolean, required: true },
  aiAvatar: { type: String, required: true },
  setQuestion: { type: Function, required: true },
  rerunGraph: { type: Function, required: true },
});

// 🌟 修复点 3：声明向父组件抛出事件，用于打开参考资料弹窗
const emit = defineEmits(['show-reference']);

const {
  currentMode,
  currentMessages,
  streamingMessage,
  currentStreamingMessageId,
  showContext,
  aiAvatar,
  setQuestion,
  rerunGraph,
} = toRefs(props);

const messagesContainer = ref(null);

const exampleQuestions = computed(() => {
  if (currentMode.value === 'nl2cypher') {
    return [
      '石英有哪些重要的物理和化学性质？',
      '黄铁矿和方铅矿有什么关系？',
      '含有铁元素的矿物有哪些？',
    ];
  }
  return [
    '石英和长石有哪些共同特征？',
    '请查询有多少种宝石类矿物？',
    '孔雀石的形成条件和用途是什么？',
  ];
});

// --- UI 动画与滚动 ---
const scrollToBottom = () => {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight + 100;
  }
};

defineExpose({ scrollToBottom });

const onWelcomeEnter = (el, done) => {
  gsap.from(el, { opacity: 0, y: 20, duration: 0.6, ease: 'back.out(1.7)', onComplete: done });
};

watch(
  () => currentMessages.value?.length || 0,
  async (newVal, oldVal) => {
    await nextTick();
    scrollToBottom();
    if (newVal > oldVal) {
      const bubbles = messagesContainer.value?.querySelectorAll('.message-row') || [];
      const lastBubble = bubbles[bubbles.length - 1];
      if (lastBubble) {
        gsap.from(lastBubble, { opacity: 0, y: 20, scale: 0.95, duration: 0.4, ease: 'power2.out' });
      }
    }
  },
);

// --- 文本格式化 ---
const formatTime = (timestamp) =>
  new Date(timestamp).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });

const formatAnswer = (answer) => {
  if (!answer) return '';
  try {
    return md.render(answer);
  } catch (e) {
    return answer;
  }
};

const formatContext = (context) => {
  if (!context) return '';
  return `<pre>${JSON.stringify(context, null, 2)}</pre>`;
};
</script>

<style scoped>
.messages-container {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  padding-bottom: 140px; /* 与输入区高度匹配，防止内容被输入框遮挡 */
  position: relative;
  z-index: 1;
  /* 使用 mask 确保内容在输入框位置被完全隐藏，渐隐区高度与输入框高度保持一致 */
  mask-image: linear-gradient(to bottom, black calc(100% - 120px), transparent calc(100% - 120px));
  -webkit-mask-image: linear-gradient(to bottom, black calc(100% - 120px), transparent calc(100% - 120px));
}

/* Welcome Card */
.mac-welcome-card {
  margin: 40px auto;
  max-width: 500px;
  text-align: center;
  background: rgba(15, 23, 42, 0.6); /* 玻璃态背景 */
  backdrop-filter: blur(12px);
  padding: 30px;
  border-radius: 20px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
}
.welcome-icon {
  font-size: 40px;
  margin-bottom: 16px;
}
.mac-welcome-card h3 {
  margin: 0 0 10px 0;
  color: var(--chat-text);
}
.mac-welcome-card p {
  color: var(--chat-text-sub);
  font-size: 14px;
  margin-bottom: 24px;
}

.suggestion-grid {
  display: grid;
  gap: 10px;
}
.suggestion-chip {
  background: var(--chip-bg);
  padding: 10px 16px;
  border-radius: 12px;
  font-size: 13px;
  cursor: pointer;
  border: 1px solid var(--chat-border);
  transition: all 0.2s;
  color: var(--chat-text);
}
.suggestion-chip:hover {
  border-color: #3b82f6; /* blue-500 */
  background: rgba(37, 99, 235, 0.1); /* blue-600/10 */
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.2);
  color: #60a5fa; /* blue-400 */
}

/* Bubbles */
.message-row {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
}
.message-row.user {
  flex-direction: row-reverse;
}

.avatar {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: rgba(30, 41, 59, 0.6); /* slate-800 with glass effect */
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  font-weight: 700;
  color: #cbd5e1; /* slate-300 */
  flex-shrink: 0;
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15);
  backdrop-filter: blur(8px);
  overflow: hidden;
  position: relative;
}

.avatar-with-image {
  background: transparent;
  padding: 2px;
}

.avatar-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  border-radius: 50%;
}

.message-row.user .avatar {
  color: #ffffff;
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.3);
}

.bubble-wrapper {
  max-width: 70%;
  display: flex;
  flex-direction: column;
}
.message-row.user .bubble-wrapper {
  align-items: flex-end;
}

.bubble-meta {
  margin-bottom: 4px;
  font-size: 11px;
  color: var(--chat-text-sub);
  margin-left: 4px;
}

.mac-bubble {
  padding: 12px 16px;
  border-radius: 18px;
  font-size: 14px;
  line-height: 1.5;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.05);
  position: relative;
}

.message-row.user .mac-bubble {
  background: linear-gradient(135deg, #2563eb, #1d4ed8); /* blue-600 to blue-700 */
  color: #ffffff;
  border-bottom-right-radius: 4px;
  box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
}

.message-row.user .avatar {
  color: #ffffff;
}

.message-row.assistant .mac-bubble {
  background: rgba(15, 23, 42, 0.6); /* 玻璃态背景 */
  backdrop-filter: blur(8px);
  color: #f1f5f9; /* slate-100 */
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-bottom-left-radius: 4px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

/* Code & Content Styles */
.code-block-mac {
  background: rgba(15, 23, 42, 0.8); /* 更深的玻璃态背景 */
  backdrop-filter: blur(8px);
  color: #cbd5e1; /* slate-300 */
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  margin: 8px 0;
  overflow: hidden;
  font-size: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
}
.code-header {
  background: rgba(30, 41, 59, 0.6);
  padding: 4px 8px;
  font-size: 10px;
  color: #94a3b8; /* slate-400 */
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}
code {
  display: block;
  padding: 8px;
  overflow-x: auto;
  font-family: monospace;
}

.success-tag {
  display: inline-block;
  background: rgba(52, 199, 89, 0.1);
  color: #34c759;
  padding: 4px 8px;
  border-radius: 6px;
  font-size: 12px;
  margin-top: 8px;
  cursor: pointer;
}

.error-bubble {
  border-left: 3px solid #ff3b30 !important;
  background: rgba(255, 59, 48, 0.05) !important;
}

/* AI Content Styles - 确保内容可见且背景透明 */
.ai-content {
  color: var(--chat-text);
  background: transparent;
}

.markdown-body {
  background: transparent;
  color: var(--chat-text);
}

/* Markdown 内容样式 - 确保所有元素背景透明 */
.markdown-body :deep(p) {
  margin: 8px 0;
  color: var(--chat-text);
  background: transparent;
}

.markdown-body :deep(ul),
.markdown-body :deep(ol) {
  margin: 8px 0;
  padding-left: 24px;
  color: var(--chat-text);
  background: transparent;
}

.markdown-body :deep(li) {
  margin: 4px 0;
  color: var(--chat-text);
  background: transparent;
}

.markdown-body :deep(h1),
.markdown-body :deep(h2),
.markdown-body :deep(h3),
.markdown-body :deep(h4),
.markdown-body :deep(h5),
.markdown-body :deep(h6) {
  margin: 12px 0 8px 0;
  color: var(--chat-text);
  background: transparent;
  font-weight: 600;
}

.markdown-body :deep(strong),
.markdown-body :deep(b) {
  font-weight: 600;
  background: transparent;
}

.markdown-body :deep(em),
.markdown-body :deep(i) {
  color: var(--chat-text);
  background: transparent;
}

.markdown-body :deep(code) {
  background: rgba(0, 0, 0, 0.1);
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Monaco', 'Menlo', monospace;
  font-size: 13px;
  color: var(--chat-text);
}

:global(.dark-theme) .markdown-body :deep(code) {
  background: rgba(255, 255, 255, 0.1);
}

.markdown-body :deep(pre) {
  background: #282c34;
  color: #abb2bf;
  padding: 12px;
  border-radius: 8px;
  overflow-x: auto;
  margin: 8px 0;
}

.markdown-body :deep(pre code) {
  background: transparent;
  padding: 0;
  color: #abb2bf;
}

.markdown-body :deep(blockquote) {
  border-left: 3px solid var(--mac-blue);
  padding-left: 12px;
  margin: 8px 0;
  color: var(--chat-text-sub);
  background: transparent;
}

.markdown-body :deep(a) {
  color: var(--mac-blue);
  text-decoration: none;
  background: transparent;
}

.markdown-body :deep(a:hover) {
  text-decoration: underline;
}

/* 🌟 修复点 4：参考资料专属样式 */
.references-section {
  margin-top: 12px;
  padding: 12px;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e9ecef;
}

:global(.dark-theme) .references-section {
  background: rgba(255,255,255,0.05);
  border-color: rgba(255,255,255,0.1);
}

.references-title {
  font-size: 13px;
  font-weight: 600;
  color: #6c757d;
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  gap: 6px;
}

:global(.dark-theme) .references-title { color: #94a3b8; }

.references-title::before { content: '📚'; }

.references-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.reference-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  background: white;
  border: 1px solid #dee2e6;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 13px;
  color: #495057;
}

:global(.dark-theme) .reference-item {
  background: rgba(30, 41, 59, 0.6);
  border-color: rgba(255, 255, 255, 0.1);
  color: #cbd5e1;
}

.reference-item:hover {
  background: #e9ecef;
  border-color: #adb5bd;
  transform: translateX(2px);
}

:global(.dark-theme) .reference-item:hover {
  background: rgba(255, 255, 255, 0.1);
}

.reference-icon { font-size: 16px; }
.reference-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 简单的流式光标 */
.streaming-text::after {
  content: '';
  display: inline-block;
  width: 6px;
  height: 14px;
  background: var(--mac-blue);
  margin-left: 2px;
  animation: blink 1s infinite;
}
@keyframes blink {
  50% { opacity: 0; }
}

/* 表格等原有样式... */
.markdown-body :deep(table) {
  width: 100%; border-collapse: collapse; margin: 16px 0; background: rgba(255, 255, 255, 0.95); border: 1px solid var(--chat-border); border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1); table-layout: fixed;
}
.markdown-body :deep(th) { white-space: nowrap; word-break: keep-all; overflow: hidden; text-overflow: ellipsis; }
.markdown-body :deep(th:nth-child(1)), .markdown-body :deep(td:nth-child(1)) { width: 12%; min-width: 120px; }
.markdown-body :deep(th:nth-child(2)), .markdown-body :deep(td:nth-child(2)) { width: 13%; min-width: 130px; }
.markdown-body :deep(th:nth-child(3)), .markdown-body :deep(td:nth-child(3)) { width: 10%; min-width: 100px; }
.markdown-body :deep(th:nth-child(4)), .markdown-body :deep(td:nth-child(4)) { width: 32.5%; min-width: 200px; }
.markdown-body :deep(th:nth-child(5)), .markdown-body :deep(td:nth-child(5)) { width: 32.5%; min-width: 200px; }
.markdown-body :deep(th:nth-child(n+6)), .markdown-body :deep(td:nth-child(n+6)) { width: auto; min-width: 150px; }
.markdown-body :deep(th), .markdown-body :deep(td) { border: 1px solid var(--chat-border); padding: 12px; background: rgba(255, 255, 255, 0.95); color: #1c1d21; text-align: left; vertical-align: top; }
.markdown-body :deep(th) { background: rgba(0, 122, 255, 0.15); color: #1c1d21; font-weight: 600; border-bottom: 2px solid var(--chat-border); }
.markdown-body :deep(td) { overflow-wrap: break-word; word-wrap: break-word; white-space: normal; }
:global(.dark-theme) .markdown-body :deep(table) { background: #161922 !important; border-color: rgba(255, 255, 255, 0.2) !important; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3); }
:global(.dark-theme) .markdown-body :deep(th) { background: #1f2329 !important; color: #cbd5e1 !important; border-color: rgba(255, 255, 255, 0.2) !important; }
:global(.dark-theme) .markdown-body :deep(td) { background: #161922 !important; color: #cbd5e1 !important; border-color: rgba(255, 255, 255, 0.15) !important; }
.markdown-body :deep(td:first-child) { color: #1c1d21 !important; background: rgba(255, 255, 255, 0.98) !important; font-weight: 600; }
:global(.dark-theme) .markdown-body :deep(td:first-child) { color: #cbd5e1 !important; background: #161922 !important; font-weight: 600; }
:global(.dark-theme) .markdown-body :deep(td:first-child), :global(.dark-theme) .markdown-body :deep(td) { color: #cbd5e1 !important; }
.markdown-body :deep(tr:hover td) { background: rgba(0, 122, 255, 0.05); }
:global(.dark-theme) .markdown-body :deep(tr:hover td) { background: #1f2329 !important; }
.markdown-body :deep(hr) { border: none; border-top: 1px solid var(--chat-border); margin: 16px 0; background: transparent; }
</style>