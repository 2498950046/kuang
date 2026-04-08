<!-- src/components/MainHeader.vue -->
<template>
  <header class="main-header">
    <div class="title">矿石信息图谱</div>
    <div class="tabs view-selector">
        <button 
          :class="['view-btn', { active: currentView === 'graph' }]"
          @click="$emit('update:currentView', 'graph')"
        >
          <!-- <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2Z" />
          </svg> -->
          <Share2 class="stat-icon" :size="16" stroke-width="1.5" />
          图谱视图
        </button>
        <!-- 新增：AI聊天视图按钮 -->
        <button 
          :class="['view-btn', { active: currentView === 'ai' }]"
          @click="$emit('update:currentView', 'ai')"
        >
          <!-- <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12,2A2,2 0 0,1 14,4C14,4.74 13.6,5.39 13,5.73V7A1,1 0 0,0 14,8H18A1,1 0 0,0 19,7V5.73C18.4,5.39 18,4.74 18,4A2,2 0 0,1 20,2A2,2 0 0,1 22,4C22,5.11 21.1,6 20,6H19V7A3,3 0 0,1 16,10H15.5A1.5,1.5 0 0,0 14,11.5V16.5A1.5,1.5 0 0,0 15.5,18H16A1,1 0 0,0 17,19V20H20A2,2 0 0,1 22,22A2,2 0 0,1 20,24A2,2 0 0,1 18,22C18,21.26 18.4,20.61 19,20.27V19A3,3 0 0,1 16,16H15.5A3.5,3.5 0 0,1 12,12.5A3.5,3.5 0 0,1 8.5,16H8A3,3 0 0,1 5,19V20.27C5.6,20.61 6,21.26 6,22A2,2 0 0,1 4,24A2,2 0 0,1 2,22A2,2 0 0,1 4,20H5V19A1,1 0 0,0 6,18H8.5A1.5,1.5 0 0,0 10,16.5V11.5A1.5,1.5 0 0,0 8.5,10H8A3,3 0 0,1 5,7V6H4A2,2 0 0,1 2,4A2,2 0 0,1 4,2A2,2 0 0,1 6,4C6,4.74 5.6,5.39 5,5.73V7A1,1 0 0,0 6,8H8.5A1.5,1.5 0 0,0 10,6.5V4.5A1.5,1.5 0 0,0 8.5,3H8A1,1 0 0,0 7,2V1H4A2,2 0 0,1 2,3A2,2 0 0,1 4,5A2,2 0 0,1 6,3C6,2.26 5.6,1.61 5,1.27V2A3,3 0 0,1 8,5H8.5A3.5,3.5 0 0,1 12,8.5A3.5,3.5 0 0,1 15.5,5H16A3,3 0 0,1 19,2V1.27C18.4,1.61 18,2.26 18,3A2,2 0 0,1 20,5A2,2 0 0,1 22,3A2,2 0 0,1 20,1H19V2A1,1 0 0,0 18,3H15.5A1.5,1.5 0 0,0 14,4.5V6.5A1.5,1.5 0 0,0 15.5,8H18A1,1 0 0,0 19,7V5.73C19.6,5.39 20,4.74 20,4A2,2 0 0,1 22,2Z" />
          </svg> -->
          <MessageCircleQuestion :size="18" />
          智能问答
        </button>
      </div>

    <!-- MATCH (n:Event {category: "战役事件"}) RETURN n -->
    <!--  -->

    <div class="header-controls">
      <!-- 发出事件，通知父组件切换主题 -->
      <div class="theme-toggle" @click="emit('toggle-theme')">
        <Sun v-if="theme === 'dark'" :size="20" />
        <Moon v-else :size="20" />
      </div>
    </div>
  </header>
</template>

<script setup>
import { MessageCircleQuestion, Box, Share2, Sun, Moon } from 'lucide-vue-next';

// 定义 props，接收来自父组件的数据
defineProps({
  // 使用 modelValue 配合 v-model:currentView 实现双向绑定
  modelValue: {
    type: String,
    required: true,
  },
  theme: {
    type: String,
    required: true,
  },
});

// 定义 emits，声明该组件可以触发的事件
const emit = defineEmits(['update:modelValue', 'toggle-theme', 'set-force-label-show', 'run-query']);

</script>

<style scoped>
/* 样式与原 App.vue 中 main-header 相关部分一致 */
.main-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 5px 25px 5px 5px;
  border-bottom: 1px solid var(--border-color);
  background-color: var(--bg-primary);
}

/* .main-header .title {
  font-size: 1.6rem; 
  font-weight: 700; 
  letter-spacing: 1px; 
  background: linear-gradient(90deg, var(--accent-color), var(--text-primary));
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
  text-shadow: 0 0 15px rgba(var(--accent-color-rgb), 0.3);
  transition: all 0.3s ease;
} */

.main-header .title {
  width: 300px;
  font-size: 1.6rem;
  font-weight: 700;
  letter-spacing: 1px;

  /* 矿物主题：淡金色渐变 */
  background: linear-gradient(120deg, #f5e6d3, #e8c9a0, #d4a574);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;

  /* 淡金色辉光效果 */
  text-shadow: 0 0 15px rgba(232, 201, 160, 0.3);

  transition: all 0.3s ease;
}

.main-header .tabs {
  display: flex;
  gap: 8px;
  padding: 4px;
  border-radius: 8px;
}

.main-header .tab {
  padding: 6px 16px;
  cursor: pointer;
  border-radius: 6px;
  background: rgba(25, 18, 12, 0.5);
  backdrop-filter: blur(8px);
  color: var(--text-muted);
  border: 1.5px solid rgba(255, 207, 113, 0.3);
  transition: all 0.3s ease-in-out;
}

.main-header .tab.active {
  background: linear-gradient(120deg, var(--accent-primary), var(--accent-secondary));
  color: var(--text-primary);
  font-weight: 600;
  border-color: var(--accent-primary);
  box-shadow: 0 0 15px rgba(212, 165, 116, 0.3);
}

.main-header .header-controls {
  display: flex;
  align-items: center;
  gap: 16px;
}

.main-header .control-btn {
  background: none;
  border: 1px solid var(--border-color);
  color: var(--text-muted);
  padding: 6px;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: color 0.2s, border-color 0.2s;
}

.main-header .control-btn:hover {
  color: var(--text-primary);
  border-color: var(--text-primary);
}

.main-header .theme-toggle {
  cursor: pointer;
  color: var(--text-primary);
  display: flex;
  align-items: center;
}


.view-selector {
  display: flex;
  gap: 4px;
  background: var(--bg-tertiary);
  backdrop-filter: blur(8px);
  border-radius: 8px;
  padding: 4px;
  border: 1.5px solid var(--border-color);
  box-shadow: 0 0 0 1px rgba(212, 165, 116, 0.15);
}

.view-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border: none;
  background: transparent;
  color: var(--text-secondary);
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 14px;
  font-weight: 500;
}

.view-btn:hover {
  background-color: var(--bg-hover);
  color: var(--text-primary);
}

.view-btn.active {
  background: linear-gradient(120deg, var(--accent-primary), var(--accent-secondary));
  color: var(--text-primary);
  box-shadow: 0 0 10px rgba(212, 165, 116, 0.3);
}

.view-btn svg {
  flex-shrink: 0;
}

</style>
