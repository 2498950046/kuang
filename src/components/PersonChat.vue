<template>
  <div class="person-chat-container">
    <!-- 顶部工具栏 -->
    <div class="chat-header">
      <div class="header-left">
        <button @click="$emit('close')" class="btn-icon" title="返回人物属性">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M19 12H5M12 19l-7-7 7-7" />
          </svg>
        </button>
      </div>
      <div class="chat-header-title">
            <h4>与 {{ currentPersonName }} 对话</h4>
        </div> 
      <div class="header-right">
        <button @click="showPersonList = !showPersonList" class="btn-icon" title="对话列表">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M3 12h18M3 6h18M3 18h18" />
          </svg>
        </button>
        <button @click="showDeleteConfirm = true" class="btn-icon" title="删除记录">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M3 6h18M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
          </svg>
        </button>
      </div>
    </div>

    <!-- 对话列表侧边栏 -->
    <div v-if="showPersonList" class="person-list-sidebar">
      <div class="sidebar-header">
        <h4>对话列表</h4>
        <button @click="showPersonList = false" class="btn-close">×</button>
      </div>
      <div class="person-list">
        <div
          v-for="(history, personName) in allChats"
          :key="personName"
          @click="switchPerson(personName)"
          class="person-item"
          :class="{ active: personName === currentPersonName }"
        >
          <img :src="getPersonAvatar(personName)" class="person-avatar-small" @error="handleAvatarError" />
          <div class="person-info">
            <div class="person-name">{{ personName }}</div>
            <div class="last-message">{{ getLastMessage(history) }}</div>
          </div>
        </div>
        <div v-if="Object.keys(allChats).length === 0" class="no-chats">
          暂无对话记录
        </div>
      </div>
      <button @click="confirmDeleteAll" class="btn-delete-all">清空所有对话</button>
    </div>

    <!-- 删除确认对话框 -->
    <div v-if="showDeleteConfirm" class="modal-overlay" @click="showDeleteConfirm = false">
      <div class="modal-content" @click.stop>
        <h3>删除确认</h3>
        <p>确定要删除与 {{ currentPersonName }} 的聊天记录吗？</p>
        <div class="modal-actions">
          <button @click="showDeleteConfirm = false" class="btn-cancel">取消</button>
          <button @click="deleteCurrentChat" class="btn-confirm">确定</button>
        </div>
      </div>
    </div>

    <!-- 聊天消息区 -->
    <div class="chat-messages" ref="messagesContainer">
      <div v-for="(msg, index) in currentChat" :key="index" class="message-wrapper" :class="msg.role">
        <img :src="msg.role === 'user' ? userAvatar : personAvatar" class="avatar" @error="handleAvatarError" />
        <div class="message-bubble">
          <div class="message-content" v-html="formatMessage(msg.content)"></div>
          <div class="message-time">{{ formatTime(msg.timestamp) }}</div>
        </div>
      </div>
      <div v-if="isLoading" class="message-wrapper assistant">
        <img :src="personAvatar" class="avatar" @error="handleAvatarError" />
        <div class="message-bubble loading">
          <div class="typing-indicator">
            <span></span><span></span><span></span>
          </div>
        </div>
      </div>
    </div>

    <!-- 输入区 -->
    <div class="chat-input-area">
      <textarea
        v-model="userInput"
        @keydown.enter.exact.prevent="sendMessage"
        placeholder="输入您的问题..."
        rows="3"
        :disabled="isLoading"
      ></textarea>
      <button @click="sendMessage" :disabled="isLoading || !userInput.trim()" class="btn-send">
        <svg viewBox="0 0 24 24" fill="currentColor">
          <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" />
        </svg>
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, nextTick, onMounted } from 'vue';
import MarkdownIt from 'markdown-it';

const md = new MarkdownIt();

const props = defineProps({
  personName: {
    type: String,
    required: true
  },
  personAvatar: {
    type: String,
    default: ''
  }
});

const emit = defineEmits(['close']);

// 状态管理
const currentPersonName = ref(props.personName);
const allChats = ref({});
const userInput = ref('');
const isLoading = ref(false);
const showPersonList = ref(false);
const showDeleteConfirm = ref(false);
const messagesContainer = ref(null);

// 默认头像
const userAvatar = new URL('../assets/person/default.jpg', import.meta.url).href;
const defaultPersonAvatar = new URL('../assets/person/default.jpg', import.meta.url).href;
const personAvatar = computed(() => {
  // 根据当前人物名称动态获取头像
  return getPersonAvatar(currentPersonName.value);
});

// 本地存储键
const STORAGE_KEY = 'person_chat_history';

// 当前聊天记录
const currentChat = computed(() => {
  return allChats.value[currentPersonName.value] || [];
});

// 初始化：从 localStorage 加载聊天记录
onMounted(() => {
  loadChatsFromStorage();
  if (!allChats.value[currentPersonName.value]) {
    allChats.value[currentPersonName.value] = [];
  }
});

// 监听 personName 变化
watch(() => props.personName, (newName) => {
  if (newName && newName !== currentPersonName.value) {
    currentPersonName.value = newName;
    if (!allChats.value[newName]) {
      allChats.value[newName] = [];
    }
  }
});

// 保存聊天记录到 localStorage
function saveChatsToStorage() {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(allChats.value));
  } catch (e) {
    console.error('保存聊天记录失败:', e);
  }
}

// 从 localStorage 加载聊天记录
function loadChatsFromStorage() {
  try {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      allChats.value = JSON.parse(stored);
    }
  } catch (e) {
    console.error('加载聊天记录失败:', e);
    allChats.value = {};
  }
}

// 发送消息
async function sendMessage() {
  if (!userInput.value.trim() || isLoading.value) return;

  const message = userInput.value.trim();
  userInput.value = '';

  // 添加用户消息
  const userMsg = {
    role: 'user',
    content: message,
    timestamp: new Date().toISOString()
  };

  if (!allChats.value[currentPersonName.value]) {
    allChats.value[currentPersonName.value] = [];
  }
  allChats.value[currentPersonName.value].push(userMsg);
  saveChatsToStorage();

  // 滚动到底部
  await nextTick();
  scrollToBottom();

  // 调用后端 API
  isLoading.value = true;
  
  // 不要提前创建消息，等收到第一个chunk再创建
  let assistantMsg = null;
  
  try {
    const apiUrl = import.meta.env.VITE_API_URL;
    const response = await fetch(`${apiUrl}/ai/person_chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        person_name: currentPersonName.value,
        chat_history: allChats.value[currentPersonName.value], // 现在可以包含所有历史消息
        user_message: message
      })
    });

    if (!response.ok) {
      throw new Error(`HTTP错误: ${response.status}`);
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    
    // console.log('📡 开始接收流式数据...');
    let chunkCount = 0;

    while (true) {
      const { done, value } = await reader.read();
      if (done) {
        // console.log('✅ 流式数据接收完成，共', chunkCount, '个数据块');
        break;
      }

      buffer += decoder.decode(value, { stream: true });
      
      // SSE 格式：event: xxx\ndata: {...}\n\n
      // 按 \n\n 分割完整的事件
      const events = buffer.split('\n\n');
      
      // 保留最后一个不完整的事件
      buffer = events.pop() || '';

      for (const event of events) {
        if (!event.trim()) continue;
        
        const lines = event.split('\n');
        let eventType = 'message';
        let eventData = '';
        
        for (const line of lines) {
          if (line.startsWith('event: ')) {
            eventType = line.slice(7).trim();
          } else if (line.startsWith('data: ')) {
            eventData = line.slice(6);
          }
        }
        
        if (eventData) {
          try {
            const data = JSON.parse(eventData);
            
            if (data.type === 'answer_chunk' && data.content) {
              chunkCount++;
              
              // 第一次收到数据时创建助手消息
              if (!assistantMsg) {
                assistantMsg = {
                  role: 'assistant',
                  content: '',
                  timestamp: new Date().toISOString()
                };
                allChats.value[currentPersonName.value].push(assistantMsg);
                // console.log('🎯 创建助手消息框');
                  // 收到第一个chunk时立即隐藏加载动画
                  isLoading.value = false;
              }
              
              // 累加到助手消息中
              assistantMsg.content += data.content;
              
              // 强制触发响应式更新 - 重新赋值整个对象和数组
              const currentPerson = currentPersonName.value;
              allChats.value = {
                ...allChats.value,
                [currentPerson]: [...allChats.value[currentPerson]]
              };
              
              if (chunkCount === 1) {
                // console.log('🎯 收到第一个数据块:', data.content);
                // console.log('📝 当前消息内容长度:', assistantMsg.content.length);
                // console.log('📊 聊天记录数量:', allChats.value[currentPerson].length);
              }
              
              await nextTick();
              scrollToBottom();
            } else if (data.type === 'complete') {
              // 完成信号
              if (data.full_answer && assistantMsg) {
                assistantMsg.content = data.full_answer;
                const currentPerson = currentPersonName.value;
                allChats.value = {
                  ...allChats.value,
                  [currentPerson]: [...allChats.value[currentPerson]]
                };
              }
              if (assistantMsg) {
                // console.log('✅ 消息接收完成，最终长度:', assistantMsg.content.length, '字符');
              }
            } else if (data.type === 'error') {
              throw new Error(data.error);
            } else if (data.type === 'step') {
              // 显示进度信息
            //   console.log('📋 进度:', data.message);
            }
          } catch (e) {
            console.error('❌ 解析响应失败:', e, '原始数据:', eventData);
          }
        }
      }
    }

    // 检查是否收到有效回复
    if (!assistantMsg || !assistantMsg.content.trim()) {
      if (assistantMsg) {
        // 移除空消息
        allChats.value[currentPersonName.value].pop();
      }
      throw new Error('未收到有效回复');
    }
    
    // 最终保存
    saveChatsToStorage();

  } catch (error) {
    console.error('❌ 发送消息失败:', error);
    // 移除失败的助手消息
    if (assistantMsg) {
      const lastMsg = allChats.value[currentPersonName.value]?.[allChats.value[currentPersonName.value].length - 1];
      if (lastMsg && lastMsg.role === 'assistant' && lastMsg === assistantMsg) {
        allChats.value[currentPersonName.value].pop();
      }
    }
    alert(`发送消息失败: ${error.message}`);
  } finally {
    isLoading.value = false;
    saveChatsToStorage();
    await nextTick();
    scrollToBottom();
  }
}

// 切换到其他人物
function switchPerson(personName) {
  currentPersonName.value = personName;
  showPersonList.value = false;
  nextTick(() => scrollToBottom());
}

// 删除当前聊天
function deleteCurrentChat() {
  delete allChats.value[currentPersonName.value];
  saveChatsToStorage();
  showDeleteConfirm.value = false;
  emit('close');
}

// 确认删除所有聊天
function confirmDeleteAll() {
  if (confirm('确定要删除所有对话记录吗？此操作不可恢复！')) {
    allChats.value = {};
    saveChatsToStorage();
    showPersonList.value = false;
    emit('close');
  }
}

// 获取人物头像
function getPersonAvatar(personName) {
  // 尝试从图片模块中获取该人物的第一张照片
  const imageModules = import.meta.glob('../assets/person/images/**/*', { eager: true, as: 'url' });
  const images = Object.keys(imageModules)
    .filter(path => path.includes(`/images/${personName}/`))
    .sort()
    .map(path => imageModules[path]);
  
  return images.length > 0 ? images[0] : defaultPersonAvatar;
}

// 头像加载失败处理
function handleAvatarError(event) {
  event.target.src = defaultPersonAvatar;
}

// 获取最后一条消息
function getLastMessage(history) {
  if (!history || history.length === 0) return '暂无消息';
  const lastMsg = history[history.length - 1];
  const content = lastMsg.content.substring(0, 30);
  return content.length < lastMsg.content.length ? content + '...' : content;
}

// 格式化消息（支持 Markdown）
function formatMessage(content) {
  try {
    return md.render(content);
  } catch (e) {
    return content.replace(/\n/g, '<br>');
  }
}

// 格式化时间
function formatTime(timestamp) {
  const date = new Date(timestamp);
  const now = new Date();
  const diff = now - date;
  
  if (diff < 60000) return '刚刚';
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`;
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`;
  
  return date.toLocaleString('zh-CN', {
    month: 'numeric',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
}

// 滚动到底部
function scrollToBottom() {
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight;
  }
}
</script>

<style scoped>
.person-chat-container {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: var(--bg-secondary);
  border-radius: 8px;
  overflow: hidden;
  position: relative;
}

/* 顶部工具栏 */
.chat-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 5px 15px;
  background: var(--bg-primary);
  border-bottom: 1px solid var(--border-color);
}

.header-left, .header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.chat-header h3 {
  margin: 0;
  font-size: 1.1em;
  color: var(--text-primary);
}

.btn-icon {
  background: transparent;
  border: none;
  cursor: pointer;
  padding: 6px;
  border-radius: 4px;
  color: var(--text-secondary);
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.btn-icon svg {
  width: 20px;
  height: 20px;
}

.btn-icon:hover {
  background: var(--bg-hover);
  color: var(--accent-color);
}

/* 对话列表侧边栏 */
.person-list-sidebar {
  position: absolute;
  top: 0;
  right: 0;
  width: 280px;
  height: 100%;
  background: var(--bg-primary);
  border-left: 1px solid var(--border-color);
  z-index: 10;
  display: flex;
  flex-direction: column;
  box-shadow: -2px 0 8px rgba(0, 0, 0, 0.1);
}

.sidebar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-color);
}

.sidebar-header h4 {
  margin: 10px 0 0 0;
  font-size: 1em;
  color: var(--text-primary);
}

.chat-header-title h4 {
  margin: 10px 0 0 0;
  font-size: 1em;
  color: var(--text-secondary);
}

.chat-header-title{
    flex: 1;
    text-align: center;
    /* white-space: nowrap; */
    /* overflow: hidden; */
    text-overflow: ellipsis;
}

.btn-close {
  background: transparent;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: var(--text-secondary);
  padding: 0;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.btn-close:hover {
  color: var(--text-primary);
}

.person-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.person-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  margin-bottom: 4px;
}

.person-item:hover {
  background: var(--bg-hover);
}

.person-item.active {
  background: var(--accent-color);
  color: white;
}

.person-avatar-small {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  object-fit: cover;
}

.person-info {
  flex: 1;
  min-width: 0;
}

.person-name {
  font-weight: 600;
  font-size: 0.95em;
  margin-bottom: 4px;
}

.last-message {
  font-size: 0.85em;
  color: var(--text-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.person-item.active .last-message {
  color: rgba(255, 255, 255, 0.8);
}

.no-chats {
  text-align: center;
  padding: 40px 20px;
  color: var(--text-muted);
  font-size: 0.9em;
}

.btn-delete-all {
  margin: 16px;
  padding: 10px;
  background: #ff4444;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.9em;
  transition: all 0.2s;
}

.btn-delete-all:hover {
  background: #cc0000;
}

/* 模态对话框 */
.modal-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 20;
}

.modal-content {
  background: var(--bg-primary);
  padding: 24px;
  border-radius: 8px;
  max-width: 400px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.modal-content h3 {
  margin: 0 0 12px 0;
  color: var(--text-primary);
}

.modal-content p {
  margin: 0 0 20px 0;
  color: var(--text-secondary);
}

.modal-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}

.btn-cancel, .btn-confirm {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9em;
  transition: all 0.2s;
}

.btn-cancel {
  background: var(--bg-secondary);
  color: var(--text-primary);
}

.btn-cancel:hover {
  background: var(--bg-hover);
}

.btn-confirm {
  background: #ff4444;
  color: white;
}

.btn-confirm:hover {
  background: #cc0000;
}

/* 聊天消息区 */
.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.message-wrapper {
  display: flex;
  gap: 12px;
  max-width: 85%;
}

.message-wrapper.user {
  align-self: flex-end;
  flex-direction: row-reverse;
}

.message-wrapper.assistant {
  align-self: flex-start;
}

.avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  object-fit: cover;
  flex-shrink: 0;
}

.message-bubble {
  background: var(--bg-primary);
  padding: 10px 14px;
  border-radius: 12px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

.message-wrapper.user .message-bubble {
  background: var(--accent-color);
  color: white;
}

.message-content {
  font-size: 0.95em;
  line-height: 1.5;
  word-wrap: break-word;
}

.message-wrapper.user .message-content {
  color: white;
}

.message-time {
  font-size: 0.75em;
  color: var(--text-muted);
  margin-top: 6px;
  text-align: right;
}

.message-wrapper.user .message-time {
  color: rgba(255, 255, 255, 0.7);
}

/* 加载动画 */
.message-bubble.loading {
  padding: 14px 20px;
}

.typing-indicator {
  display: flex;
  gap: 4px;
}

.typing-indicator span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--accent-color);
  animation: typing 1.4s infinite;
}

.typing-indicator span:nth-child(2) {
  animation-delay: 0.2s;
}

.typing-indicator span:nth-child(3) {
  animation-delay: 0.4s;
}

@keyframes typing {
  0%, 60%, 100% {
    transform: translateY(0);
  }
  30% {
    transform: translateY(-10px);
  }
}

/* 输入区 */
.chat-input-area {
  display: flex;
  gap: 12px;
  padding: 16px;
  background: var(--bg-primary);
  border-top: 1px solid var(--border-color);
}

.chat-input-area textarea {
  flex: 1;
  padding: 10px 14px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  background: var(--bg-secondary);
  color: var(--text-primary);
  font-size: 0.95em;
  resize: none;
  font-family: inherit;
}

.chat-input-area textarea:focus {
  outline: none;
  border-color: var(--accent-color);
}

.chat-input-area textarea:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-send {
  padding: 10px 16px;
  background: var(--accent-color);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 50px;
  margin: 0px;
}

.btn-send:hover:not(:disabled) {
  background: var(--accent-hover);
  transform: translateY(-1px);
}

.btn-send:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-send svg {
  width: 20px;
  height: 20px;
}

/* Markdown 样式 */
.message-content :deep(p) {
  margin: 0 0 8px 0;
}

.message-content :deep(p:last-child) {
  margin-bottom: 0;
}

.message-content :deep(ul), .message-content :deep(ol) {
  margin: 8px 0;
  padding-left: 20px;
}

.message-content :deep(code) {
  background: rgba(0, 0, 0, 0.1);
  padding: 2px 6px;
  border-radius: 3px;
  font-family: monospace;
  font-size: 0.9em;
}

.message-wrapper.user .message-content :deep(code) {
  background: rgba(255, 255, 255, 0.2);
}

.message-content :deep(pre) {
  background: rgba(0, 0, 0, 0.1);
  padding: 10px;
  border-radius: 6px;
  overflow-x: auto;
  margin: 8px 0;
}

.message-content :deep(pre code) {
  background: none;
  padding: 0;
}

/* 滚动条样式 */
.chat-messages::-webkit-scrollbar,
.person-list::-webkit-scrollbar {
  width: 6px;
}

.chat-messages::-webkit-scrollbar-track,
.person-list::-webkit-scrollbar-track {
  background: transparent;
}

.chat-messages::-webkit-scrollbar-thumb,
.person-list::-webkit-scrollbar-thumb {
  background: var(--border-color);
  border-radius: 3px;
}

.chat-messages::-webkit-scrollbar-thumb:hover,
.person-list::-webkit-scrollbar-thumb:hover {
  background: var(--text-muted);
}
</style>
