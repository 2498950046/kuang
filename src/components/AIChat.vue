<template>
  <div class="mac-window-container" ref="containerRef">
    <div class="mac-layout" :class="{ 'sidebar-collapsed': isSidebarCollapsed }">
      <aside class="mac-sidebar" ref="sidebarRef">
        <div class="sidebar-header-area" v-if="!isSidebarCollapsed">
          <div class="sidebar-row">
            <button class="mac-icon-btn collapse-btn" @click="toggleSidebar" title="折叠侧栏">
              <img :src="isSidebarCollapsed ? currentUnfoldIcon : currentFoldIcon" class="icon-img" />
            </button>
            <button class="mac-new-chat-btn" @click="startNewConversation" @mouseenter="hoverBtn" @mouseleave="leaveBtn">
              <span class="plus-icon">＋</span> 新对话
            </button>
          </div>

          <ModeNavigation :currentMode="currentMode" @switch-mode="switchMode" />
        </div>
        <div class="collapsed-actions" v-else>
          <button class="mac-mini-btn ghost" @click="toggleSidebar" title="展开侧栏">
            <img :src="currentUnfoldIcon" class="icon-img" />
          </button>
          <div class="mini-stack">
            <button class="mac-mini-btn" :class="{ active: currentMode === 'nl2cypher' }" @click="switchMode('nl2cypher')" title="图谱查询">
              <Search :size="18" />
            </button>
            <button class="mac-mini-btn" :class="{ active: currentMode === 'rag' }" @click="switchMode('rag')" title="智能问答">
              <MessageCircle :size="18" />
            </button>
            <button class="mac-mini-btn" :class="{ active: currentMode === 'appreciation' }" @click="switchMode('appreciation')" title="智能鉴赏">
              <MessageCircle :size="18" />
            </button>
            <button class="mac-mini-btn" :class="{ active: currentMode === 'deep-learning' }" @click="switchMode('deep-learning')" title="算法模型可视化平台">
              <Search :size="18" />
            </button>
          </div>
        </div>

        <RecentHistory
          :historyItems="historyItems"
          :isSidebarCollapsed="isSidebarCollapsed"
          @clear-history="clearHistory"
          @open-conversation="openConversation"
        />

        <div class="sidebar-copyright" v-if="!isSidebarCollapsed">
          <div>Copyright © 2026</div>
          
        </div>
      </aside>

      <section class="mac-main">
        <header class="mac-header">
          <div class="header-title-group">
            <h2 class="title">{{ headerTitle }}</h2>
            <p class="subtitle">基于全量矿物数据图谱</p>
          </div>
        </header>

        <div v-if="currentMode === 'appreciation'" class="appreciation-viewport">
          <AppreciationPanel @query-mineral="handleQueryMineral" />
        </div>

        <div v-else-if="currentMode === 'deep-learning'" class="deep-learning-viewport">
          <iframe
            class="deep-learning-frame"
            :src="deepLearningUrl"
            title="算法模型可视化平台"
            frameborder="0"
          ></iframe>
        </div>

        <div v-else class="chat-viewport">
          <ChatMessages
            ref="chatMessagesRef"
            :currentMode="currentMode"
            :currentMessages="currentMessages"
            :streamingMessage="streamingMessage"
            :currentStreamingMessageId="currentStreamingMessageId"
            :showContext="showContext"
            :aiAvatar="aiAvatar"
            :setQuestion="setQuestion"
            :rerunGraph="rerunGraph"
            @show-reference="showReferencePreview"
          />

          <div class="input-area-wrapper">
            <div class="mac-input-bar">
              <input 
                v-model="inputMessage" 
                type="text"
                :placeholder="currentMode === 'nl2cypher' ? '输入查询描述 (例如: 石英的物理性质)...' : '输入您的问题...'" 
                @keypress.enter="sendMessage"
                :disabled="isLoading || isRecording" 
                class="glass-input" 
              />
              <button 
                class="voice-btn-mac" 
                :class="{ recording: isRecording }"
                @click="toggleRecording" 
                :disabled="isLoading"
                :title="isRecording ? '点击停止录音' : '点击开始语音输入'"
              >
                <svg v-if="!isRecording" width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12,2A3,3 0 0,1 15,5V11A3,3 0 0,1 12,14A3,3 0 0,1 9,11V5A3,3 0 0,1 12,2M19,11C19,14.53 16.39,17.44 13,17.93V21H11V17.93C7.61,17.44 5,14.53 5,11H7A5,5 0 0,0 12,16A5,5 0 0,0 17,11H19Z" />
                </svg>
                <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="currentColor" class="recording-icon">
                  <rect x="6" y="6" width="12" height="12" rx="2" />
                </svg>
              </button>
              <button class="send-btn-mac" @click="sendMessage" :disabled="!inputMessage.trim() || isLoading || isRecording">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M2,21L23,12L2,3V10L17,12L2,14V21Z" />
                </svg>
              </button>
            </div>
            <div class="input-footer-mac">
              <label class="mac-checkbox">
                <span class="status-text" v-if="isLoading">AI 正在思考中...</span>
              </label>
            </div>
          </div>
        </div>
      </section>
    </div>

    <div v-if="previewVisible" class="preview-overlay" @click.self="closePreview">
      <div class="preview-modal">
        <button class="preview-close-btn" @click="closePreview">×</button>
        <div class="preview-header">
          <h3 class="preview-title">{{ currentPreviewRef?.documentName || currentPreviewRef?.document_name }}</h3>
        </div>
        <div class="preview-content">
          <p class="preview-text">{{ currentPreviewRef?.content }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, nextTick, computed, onMounted } from 'vue';
import gsap from 'gsap';
import foldIcon from '@/assets/fold.png';
import unfoldIcon from '@/assets/unfold.png';
import aiAvatar from '@/assets/ai.png';
import { Search, MessageCircle } from 'lucide-vue-next';
import { nl2cypher, speechToText, graphQuery } from '@/api';
import AppreciationPanel from './AppreciationPanel.vue';
import ModeNavigation from './AIChat/ModeNavigation.vue';
import RecentHistory from './AIChat/RecentHistory.vue';
import ChatMessages from './AIChat/ChatMessages.vue';

const APP_HOST = '154.44.25.243';
const IS_LOCAL_TEST = ['localhost', '127.0.0.1'].includes(window.location.hostname);
const QA_API_BASE = IS_LOCAL_TEST ? `http://${APP_HOST}:8081` : '/qa-api';
const deepLearningUrl = 'http://154.44.25.243:18080/';

const currentFoldIcon = foldIcon;
const currentUnfoldIcon = unfoldIcon;

const props = defineProps({ visible: { type: Boolean, default: true } });
const emit = defineEmits(['graph-query-result']);

const currentMode = ref('nl2cypher');
const isSidebarCollapsed = ref(false);
const inputMessage = ref('');
const isLoading = ref(false);
const messagesStore = reactive({ nl2cypher: [], rag: [], appreciation: [], 'deep-learning': [] });
const conversationHistory = ref([]);
const currentConversationId = ref(null);
const chatMessagesRef = ref(null);
const showContext = ref(false);
const streamingMessage = ref('');
const currentStreamingMessageId = ref(null);
let messageIdCounter = 0;

// ====== 参考资料弹窗 ======
const previewVisible = ref(false);
const currentPreviewRef = ref(null);
const showReferencePreview = (refItem) => {
  currentPreviewRef.value = refItem;
  previewVisible.value = true;
};
const closePreview = () => {
  previewVisible.value = false;
  currentPreviewRef.value = null;
};
// ==========================

const isRecording = ref(false);
let mediaRecorder = null;
let audioChunks = [];

const currentMessages = computed(() => messagesStore[currentMode.value] || []);
const headerTitle = computed(() => {
  if (currentMode.value === 'nl2cypher') return '知识图谱查询';
  if (currentMode.value === 'appreciation') return '智能鉴赏';
  if (currentMode.value === 'deep-learning') return '算法模型可视化平台';
  return '智能助手问答';
});

const historyItems = computed(() => {
  const normalizeTime = (t) => (t instanceof Date ? t : new Date(t));
  return (conversationHistory.value || [])
    .map((item) => {
      const ts = normalizeTime(item.updatedAt || item.createdAt || item.timestamp || Date.now());
      const firstQuestion = item.content || item.title || (item.messages?.find(m => m.type === 'user')?.content || '');
      const title = firstQuestion && firstQuestion.length > 12 ? `${firstQuestion.slice(0, 12)}…` : firstQuestion || '未命名会话';
      return { ...item, timestamp: ts, title };
    })
    .sort((a, b) => b.timestamp - a.timestamp)
    .slice(0, 30);
});

const generateMessageId = () => `msg_${Date.now()}_${++messageIdCounter}`;

const loadStoredMessages = () => {
  try {
    const storedHistory = localStorage.getItem('ai-chat-conversations');
    if (storedHistory) {
      const parsedHistory = JSON.parse(storedHistory);
      conversationHistory.value = Array.isArray(parsedHistory) ? parsedHistory : [];
    }

    if (conversationHistory.value && conversationHistory.value.length > 0 && !currentConversationId.value) {
      const latest = conversationHistory.value.slice().sort((a, b) => new Date(b.updatedAt) - new Date(a.updatedAt))[0];
      if (latest) {
        currentConversationId.value = latest.id;
        currentMode.value = latest.mode || 'nl2cypher';
        messagesStore[currentMode.value] = [...(latest.messages || [])];
      }
    }
  } catch (e) {}
};

const saveMessagesToStorage = () => {
  try {
    localStorage.setItem('ai-chat-messages', JSON.stringify(messagesStore));
    localStorage.setItem('ai-chat-conversations', JSON.stringify(conversationHistory.value || []));
  } catch (e) {}
};

const addConversationHistory = (mode, content) => {
  if (!content) return;
  const now = new Date();
  const memoryId = now.getTime(); // 嵌入真实时间戳给 SpringBoot
  const id = `conv_${memoryId}_${Math.random().toString(36).slice(2, 6)}`;
  const entry = { id, mode, content, title: content, messages: [...(messagesStore[mode] || [])], createdAt: now, updatedAt: now };
  currentConversationId.value = id;
  conversationHistory.value = [entry, ...(conversationHistory.value || [])];
  if (conversationHistory.value.length > 100) {
    conversationHistory.value = conversationHistory.value.slice(0, 100);
  }
  saveMessagesToStorage();
};

const updateCurrentConversationMessages = () => {
  if (!currentConversationId.value) return;
  const idx = (conversationHistory.value || []).findIndex((c) => c.id === currentConversationId.value);
  if (idx === -1) return;
  const conv = conversationHistory.value[idx];
  const mode = conv.mode || currentMode.value;
  conversationHistory.value[idx] = { ...conv, messages: [...(messagesStore[mode] || [])], updatedAt: new Date() };
  saveMessagesToStorage();
};

const openConversation = async (id) => {
  const conv = (conversationHistory.value || []).find((c) => c.id === id);
  if (!conv) return;
  currentConversationId.value = conv.id;
  currentMode.value = conv.mode || 'nl2cypher';
  messagesStore[currentMode.value] = [...(conv.messages || [])];
  nextTick(() => scrollToBottom());

  // 同步后端拉取参考资料
  if (currentMode.value === 'rag') {
    const match = id.match(/conv_(\d+)_/);
    if (match) {
      const memoryId = parseInt(match[1]);
      try {
        const res = await fetch(`${QA_API_BASE}/ai/history/${memoryId}`, { credentials: 'include' });
        if (res.ok) {
          const data = await res.json();
          if (data && data.length > 0) {
            const newMessages = [];
            data.forEach((item, index) => {
              if (item.question) {
                newMessages.push({ id: `msg_u_${index}`, type: 'user', content: item.question, mode: 'rag' });
              }
              if (item.answer) {
                let refsArray = [];
                if (item.reference_materials) {
                  try { refsArray = JSON.parse(item.reference_materials); } catch(e){}
                }
                newMessages.push({ 
                  id: `msg_a_${index}`, type: 'assistant', content: item.answer, references: refsArray, mode: 'rag', success: true 
                });
              }
            });
            messagesStore.rag = newMessages;
            updateCurrentConversationMessages();
            nextTick(() => scrollToBottom());
          }
        }
      } catch(e) {}
    }
  }
};

const setQuestion = (q) => { inputMessage.value = q; };
const switchMode = (mode) => { currentMode.value = mode; };
const toggleSidebar = () => { isSidebarCollapsed.value = !isSidebarCollapsed.value; };

const handleQueryMineral = ({ mode, question }) => {
  switchMode(mode);
  setQuestion(question);
  nextTick(() => {
    const input = document.querySelector('.glass-input');
    if (input) input.focus();
  });
};

const clearHistory = () => {
  if (confirm('确定清空当前模式历史？')) {
    messagesStore[currentMode.value] = [];
    conversationHistory.value = (conversationHistory.value || []).filter((h) => h.mode !== currentMode.value);
    if (conversationHistory.value.length === 0) currentConversationId.value = null;
    saveMessagesToStorage();
  }
};

const startNewConversation = () => {
  messagesStore[currentMode.value] = [];
  currentConversationId.value = null;
  saveMessagesToStorage();
  streamingMessage.value = '';
  currentStreamingMessageId.value = null;
};

const scrollToBottom = () => { chatMessagesRef.value?.scrollToBottom?.(); };

const sendMessage = async () => {
  if (!inputMessage.value.trim() || isLoading.value) return;
  const question = inputMessage.value;
  inputMessage.value = '';

  const isFirstMessageOfConversation = !currentConversationId.value || messagesStore[currentMode.value].length === 0;

  const userMsg = { id: generateMessageId(), type: 'user', content: question, timestamp: new Date(), mode: currentMode.value };
  messagesStore[currentMode.value].push(userMsg);
  
  if (isFirstMessageOfConversation) addConversationHistory(currentMode.value, question);
  else updateCurrentConversationMessages();

  isLoading.value = true;
  await nextTick();
  scrollToBottom();

  try {
    if (currentMode.value === 'nl2cypher') await handleNL2Cypher(question);
    else await handleRAGStream(question);
  } catch (e) {
    messagesStore[currentMode.value].push({
      id: generateMessageId(), type: 'assistant', content: '服务异常', success: false, error: e.message, timestamp: new Date(), mode: currentMode.value,
    });
  } finally {
    isLoading.value = false;
    await nextTick();
    scrollToBottom();
  }
};

// ==========================================
// 🚀 核心修复：还原你工作正常的原生追加逻辑，抛弃 splice！
// ==========================================
const handleRAGStream = async (q) => {
  const msgId = generateMessageId();
  
  const aiMessageIndex = messagesStore.rag.length;
  messagesStore.rag.push({
    id: msgId, type: 'assistant', mode: 'rag', content: '', timestamp: new Date(), success: true, references: []
  });
  
  currentStreamingMessageId.value = msgId;

  let memoryId = Date.now(); 
  if (currentConversationId.value) {
    const match = currentConversationId.value.match(/conv_(\d+)_/);
    if (match) memoryId = parseInt(match[1]); 
  }

  try {
    const chatIdResponse = await fetch(`${QA_API_BASE}/ai/chat_id`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        memoryId: memoryId
      }),
      credentials: 'include'
    });

    if (!chatIdResponse.ok) {
      throw new Error(`获取chat_id失败：${chatIdResponse.status}`);
    }

    await chatIdResponse.text();

    const response = await fetch(`${QA_API_BASE}/ai/chat_two_step`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/x-stream'
      },
      body: JSON.stringify({ memoryId: memoryId, message: q }),
      credentials: 'include'
    });

    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
    if (!response.body) throw new Error('浏览器未获取到可读流');

    const reader = response.body.getReader();
    const decoder = new TextDecoder('utf-8');

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      const chunk = decoder.decode(value, { stream: true });
      if (chunk) {
        messagesStore.rag[aiMessageIndex].content += chunk;
        streamingMessage.value = messagesStore.rag[aiMessageIndex].content;
        scrollToBottom();
      }
    }

    currentStreamingMessageId.value = null;
    streamingMessage.value = '';
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    const historyRes = await fetch(`${QA_API_BASE}/ai/history/${memoryId}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json'
      },
      credentials: 'include'
    });
    
    if (historyRes.ok) {
      const historyData = await historyRes.json();
      if (historyData.length > 0) {
        const lastItem = historyData[historyData.length - 1];
        if (lastItem.reference_materials) {
          try {
            const refs = JSON.parse(lastItem.reference_materials);
            messagesStore.rag[aiMessageIndex].references = refs;
          } catch(e){}
        }
      }
    }
    
    updateCurrentConversationMessages();
    saveMessagesToStorage();

  } catch (error) {
    console.error('RAG 流式请求失败:', error);
    messagesStore.rag[aiMessageIndex].content += `\n\n服务异常: ${error.message}`;
    messagesStore.rag[aiMessageIndex].success = false;

    currentStreamingMessageId.value = null;
    streamingMessage.value = '';
    updateCurrentConversationMessages();
    saveMessagesToStorage();
    scrollToBottom();
  }
};

const handleNL2Cypher = async (q) => {
  const msgId = generateMessageId();
  try {
    const res = await nl2cypher(q);
    const success = res?.success === true;
    const cypher = res?.cypher || '';
    const answer = res?.short_answer || res?.answer || res?.explanation || res?.description || res?.content || res?.message || res?.result?.short_answer || '';
    
    let graphData = null;
    if (res?.result) {
      graphData = res.result.data ? res.result.data : res.result;
    }

    messagesStore.nl2cypher.push({
      id: msgId, type: 'assistant', mode: 'nl2cypher', success, cypher, data: graphData, answer, timestamp: new Date(),
      error: res?.error || (success ? null : '查询失败'),
      content: res?.error || (success ? '查询成功' : '查询失败'),
    });
    updateCurrentConversationMessages();

    if (success && graphData) {
      emit('graph-query-result', { type: 'graph', data: graphData, answer: answer });
    }
  } catch (e) {
    messagesStore.nl2cypher.push({
      id: msgId, type: 'assistant', mode: 'nl2cypher', success: false, error: e?.message || '请求失败',
      content: `服务异常: ${e?.message || '未知错误'}`, timestamp: new Date(),
    });
    updateCurrentConversationMessages();
  } finally {
    saveMessagesToStorage();
  }
};

const rerunGraph = async (message) => {
  if (!message?.cypher) return;
  try {
    const res = await graphQuery(message.cypher);
    const graphData = res?.data || res?.result || res;
    emit('graph-query-result', { type: 'graph', data: graphData, answer: message.answer || '' });
  } catch (e) {
    alert(`重新查询失败: ${e?.message || '未知错误'}`);
  }
};

const toggleRecording = async () => {
  if (isRecording.value) { stopRecording(); } else { await startRecording(); }
};

const startRecording = async () => {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    mediaRecorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
    audioChunks = [];

    mediaRecorder.ondataavailable = (event) => {
      if (event.data.size > 0) audioChunks.push(event.data);
    };

    mediaRecorder.onstop = async () => {
      const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
      stream.getTracks().forEach(track => track.stop());
      isLoading.value = true;
      try {
        const result = await speechToText(audioBlob);
        if (result.success && result.text) inputMessage.value = result.text;
      } catch (error) {
        alert('语音识别失败: ' + error.message);
      } finally {
        isLoading.value = false;
      }
    };

    mediaRecorder.start();
    isRecording.value = true;
  } catch (error) {
    alert('无法访问麦克风，请检查权限设置');
  }
};

const stopRecording = () => {
  if (mediaRecorder && mediaRecorder.state !== 'inactive') mediaRecorder.stop();
  isRecording.value = false;
};

const hoverBtn = (e) => gsap.to(e.target, { scale: 1.02, duration: 0.2 });
const leaveBtn = (e) => gsap.to(e.target, { scale: 1, duration: 0.2 });

const containerRef = ref(null);
onMounted(() => {
  loadStoredMessages();
  gsap.from('.mac-sidebar', { x: -50, opacity: 0, duration: 0.8, ease: 'power3.out' });
  gsap.from('.mac-header', { y: -20, opacity: 0, duration: 0.8, delay: 0.2, ease: 'power3.out' });
  gsap.from('.input-area-wrapper', { y: 50, opacity: 0, duration: 0.8, delay: 0.4, ease: 'power3.out' });
});
</script>

<style scoped>
/* 原有的基础样式不动 */
:root {
  --font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Helvetica Neue", sans-serif;
  --mac-blue: #3b82f6; 
  --mac-blue-400: #60a5fa; 
  --mac-blue-600: #2563eb; 
  --mac-gray: #94a3b8; 
  --bubble-user: linear-gradient(135deg, #2563eb, #1d4ed8);
  --bubble-ai: rgba(15, 23, 42, 0.6);
  --chat-surface: rgba(247, 248, 252, 0.9);
  --chat-border: rgba(0, 0, 0, 0.12);
  --chat-text: #1c1d21;
  --chat-text-sub: #6b7280;
  --panel-bg: rgba(255, 255, 255, 0.28);
  --chip-bg: rgba(255, 255, 255, 0.34);
  --input-bg: rgba(255, 255, 255, 0.24);
  --mini-btn-bg: rgba(255, 255, 255, 0.9);
  --mac-shadow: 0 14px 44px rgba(0, 0, 0, 0.14);
}

:global(.dark-theme) {
  --chat-surface: rgba(15, 23, 42, 0.6); 
  --chat-border: rgba(255, 255, 255, 0.1); 
  --chat-text: #cbd5e1; 
  --chat-text-sub: #94a3b8; 
  --panel-bg: rgba(15, 23, 42, 0.6); 
  --chip-bg: rgba(30, 41, 59, 0.4); 
  --input-bg: rgba(15, 23, 42, 0.7);
  --mini-btn-bg: rgba(30, 41, 59, 0.5);
  --mac-shadow: 0 12px 40px rgba(0, 0, 0, 0.45);
}

.mac-window-container { width: 100%; height: 100%; box-sizing: border-box; font-family: var(--font-family); color: var(--chat-text); }
.mac-layout {
  display: flex; height: 100%; width: 100%; background: #020617; 
  background-image: radial-gradient(at 0% 0%, rgba(30, 58, 138, 0.15) 0, transparent 50%), radial-gradient(at 100% 100%, rgba(15, 118, 110, 0.1) 0, transparent 50%);
  backdrop-filter: blur(12px); border-radius: 16px; box-shadow: var(--mac-shadow); border: 1px solid var(--chat-border); overflow: hidden;
}
.mac-sidebar {
  width: 280px; background: rgba(15, 23, 42, 0.6); backdrop-filter: blur(12px); border-right: 1px solid rgba(255, 255, 255, 0.1);
  display: flex; flex-direction: column; transition: all 0.4s cubic-bezier(0.25, 0.8, 0.25, 1); padding: 16px; flex-shrink: 0; box-shadow: inset -1px 0 0 rgba(0,0,0,0.04);
}
.sidebar-header-area { display: flex; flex-direction: column; gap: 16px; margin-bottom: 20px; }
.sidebar-row { display: flex; gap: 10px; align-items: center; }
.collapsed-actions { display: flex; flex-direction: column; gap: 8px; align-items: center; padding: 6px 0; }
.mini-stack { display: flex; flex-direction: column; gap: 6px; }
.mac-mini-btn {
  width: 36px; height: 36px; border-radius: 12px; border: 1px solid var(--chat-border); background: var(--mini-btn-bg);
  color: var(--chat-text); cursor: pointer; font-size: 15px; transition: all 0.2s; display: inline-flex; align-items: center; justify-content: center;
}
.mac-mini-btn.active { background: rgba(37, 99, 235, 0.2); color: #60a5fa; border-color: rgba(59, 130, 246, 0.2); box-shadow: 0 2px 6px rgba(37, 99, 235, 0.2); }
:global(.dark-theme) .mac-mini-btn.active { background: rgba(37, 99, 235, 0.2); color: #60a5fa; border-color: rgba(59, 130, 246, 0.2); }
.mac-mini-btn:hover { transform: translateY(-1px); }
.mac-layout.sidebar-collapsed .mac-sidebar { width: 72px; padding: 12px 10px; }
.mac-layout.sidebar-collapsed .sidebar-scroll-area, .mac-layout.sidebar-collapsed .sidebar-header-area { display: none; }
.mac-icon-btn { background: transparent; border: none; cursor: pointer; opacity: 0.6; transition: opacity 0.2s; padding: 4px; }
.mac-icon-btn:hover { opacity: 1; }
.icon-img { width: 22px; height: 22px; }
.mac-new-chat-btn {
  width: 100%; padding: 8px; border-radius: 8px; border: 1px solid var(--chat-border); background: var(--chip-bg);
  color: var(--mac-blue-400); font-weight: 600; font-size: 15px; cursor: pointer; display: flex; align-items: center; justify-content: center; gap: 6px; transition: all 0.2s; box-shadow: 0 2px 6px rgba(0, 0, 0, 0.12);
}
:global(.dark-theme) .mac-new-chat-btn { background: rgba(30, 41, 59, 0.4); color: #60a5fa; box-shadow: none; border: 1px solid rgba(255, 255, 255, 0.1); }
.mac-new-chat-btn:hover { background: #3b82f6; color: #ffffff; box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3); transform: translateY(-1px); }
:global(.dark-theme) .mac-new-chat-btn:hover { background: rgba(59, 130, 246, 0.2); color: #60a5fa; border-color: rgba(59, 130, 246, 0.3); box-shadow: 0 2px 8px rgba(59, 130, 246, 0.2); transform: translateY(-1px); }
.sidebar-copyright { margin-top: auto; padding: 16px 8px 0px; text-align: center; font-size: 12px; color: var(--chat-text-sub); line-height: 1.6; }
.sidebar-copyright div { margin: 0; }
.mac-main { flex: 1; display: flex; flex-direction: column; position: relative; }
.mac-header { height: 60px; display: flex; align-items: center; padding: 0 20px; }
.header-title-group { display: flex; flex-direction: column; }
.title { font-size: 20px; font-weight: 700; margin: 0; color: var(--chat-text); }
.subtitle { font-size: 11px; color: var(--chat-text-sub); margin: 2px 0 0 0; }
.chat-viewport, .appreciation-viewport { flex: 1; display: flex; flex-direction: column; overflow: hidden; position: relative; }
.input-area-wrapper { position: absolute; bottom: 0; left: 0; right: 0; padding: 20px; background: var(--chat-surface) !important; z-index: 100; backdrop-filter: blur(20px); opacity: 1 !important; min-height: 80px; }
:global(.dark-theme) .input-area-wrapper { background: rgba(15, 23, 42, 0.8) !important; backdrop-filter: blur(12px); box-shadow: 0 -8px 30px rgba(0, 0, 0, 0.6); border-top: 1px solid rgba(255, 255, 255, 0.1); }
.mac-input-bar { display: flex; align-items: center; background: rgba(15, 23, 42, 0.6); backdrop-filter: blur(12px); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 24px; padding: 6px 6px 6px 16px; box-shadow: 0 6px 14px rgba(0,0,0,0.2); transition: all 0.2s; }
.mac-input-bar:focus-within { border-color: #3160ac; }
.glass-input { flex: 1; border: none; background: transparent; outline: none; font-size: 14px; color: var(--chat-text); }
.send-btn-mac { width: 32px; height: 32px; border-radius: 50%; border: none; background: #3b82f6; color: white; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: all 0.2s; box-shadow: 0 2px 8px rgba(59, 130, 246, 0.3); }
.send-btn-mac:disabled { background: rgba(148, 163, 184, 0.3); cursor: not-allowed; box-shadow: none; }
.send-btn-mac:not(:disabled):hover { transform: scale(1.1); background: #2563eb; box-shadow: 0 4px 12px rgba(37, 99, 235, 0.4); }
.voice-btn-mac { width: 32px; height: 32px; border-radius: 50%; border: none; background: rgba(100, 116, 139, 0.2); color: var(--chat-text-sub); cursor: pointer; display: flex; align-items: center; justify-content: center; transition: all 0.2s; margin-right: 8px; }
.voice-btn-mac:hover:not(:disabled) { background: rgba(100, 116, 139, 0.3); color: var(--chat-text-main); transform: scale(1.05); }
.voice-btn-mac:disabled { opacity: 0.5; cursor: not-allowed; }
.voice-btn-mac.recording { background: #ef4444; color: white; animation: pulse-recording 1s ease-in-out infinite; box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7); }
.voice-btn-mac.recording:hover { background: #dc2626; }
.voice-btn-mac .recording-icon { animation: pulse-icon 0.5s ease-in-out infinite; }
@keyframes pulse-recording { 0% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7); } 70% { box-shadow: 0 0 0 8px rgba(239, 68, 68, 0); } 100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); } }
@keyframes pulse-icon { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
.input-footer-mac { display: flex; justify-content: space-between; margin-top: 8px; padding: 0 10px; font-size: 11px; color: var(--chat-text-sub); }
.mac-checkbox { display: flex; align-items: center; gap: 4px; cursor: pointer; }
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-thumb { background: rgba(0,0,0,0.1); border-radius: 3px; }
::-webkit-scrollbar-track { background: transparent; }

/* 完美移植的【参考资料弹窗】CSS 样式 */
.preview-overlay {
  position: fixed; inset: 0; background: rgba(0, 0, 0, 0.5); display: flex; align-items: center; justify-content: center; z-index: 9999; animation: fadeIn 0.2s ease;
}
.preview-modal {
  background: white; border-radius: 12px; width: 90%; max-width: 800px; max-height: 80vh; display: flex; flex-direction: column; box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3); animation: slideUp 0.3s ease; position: relative;
}
:global(.dark-theme) .preview-modal { background: #1e293b; color: #cbd5e1; }

.preview-close-btn {
  position: absolute; top: 12px; right: 12px; background: transparent; border: none; font-size: 24px; font-weight: bold; color: #666; cursor: pointer; width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center; transition: all 0.2s; z-index: 10;
}
.preview-close-btn:hover { background: #f5f5f5; color: #333; }
:global(.dark-theme) .preview-close-btn { color: #94a3b8; }
:global(.dark-theme) .preview-close-btn:hover { background: rgba(255,255,255,0.1); color: white; }

.preview-header { padding: 20px 24px 16px; border-bottom: 1px solid #e9ecef; }
:global(.dark-theme) .preview-header { border-bottom: 1px solid rgba(255,255,255,0.1); }
.preview-title { font-size: 18px; font-weight: 600; color: #212529; margin: 0; padding-right: 32px; word-break: break-word; }
:global(.dark-theme) .preview-title { color: white; }
.preview-content { padding: 24px; overflow-y: auto; max-height: calc(80vh - 100px); line-height: 1.8; }
.preview-text { font-size: 15px; color: #212529; margin: 0; white-space: pre-wrap; word-break: break-word; line-height: 1.8; }
:global(.dark-theme) .preview-text { color: #cbd5e1; }

@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
@keyframes slideUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
.deep-learning-viewport {
  flex: 1;
  min-height: 0;
  padding: 0 24px 24px;
}
.deep-learning-frame {
  width: 100%;
  height: 100%;
  min-height: calc(100vh - 220px);
  border: 1px solid var(--chat-border);
  border-radius: 18px;
  background: #0f172a;
}
</style>
