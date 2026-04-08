<template>
  <div class="gesture-guide">
    <!-- 底部状态栏 -->
<div class="status-bar" v-show="!hideStatusBar">
  <div class="status-content">
        <div v-if="stabilityCount > 1" class="stability-progress">
          <div 
            class="progress-bar" 
            :style="{ width: `${(stabilityCount / STABILITY_THRESHOLD) * 100}%` }" 
          />
        </div>
        
        <div class="status-info">
          <div class="status-icon" :class="{ active: gestureState.type !== 'NONE' }">
              <img src="@/assets/hand_finger.png" alt="手势控制" class="hand-finger-icon" style="width: 20px; height: 20px;" >
          </div>
          <div class="status-text">
            <div class="status-value">{{ gestureStatus }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 右侧指引面板 -->
    <div class="guide-panel">
      <div class="guide-header">
        <img src="@/assets/hand_finger.png" alt="手势控制" class="hand-finger-icon" style="width: 20px; height: 20px;" >
        <h3>手势操作指引</h3>
      </div>
      <div class="guide-content">
        <div v-for="(item, idx) in guideItems" :key="idx" class="guide-item">
          <div class="guide-item-header">
            <span class="guide-key-wrapper">
              <span class="guide-key">{{ item.key }}</span>
              <svg 
                v-if="item.hasVideo" 
                class="video-icon" 
                @click="openVideoModal"
                viewBox="0 0 1024 1024" 
                width="24" 
                height="24"
              >
                <path d="M849.5 962l-675 0c-66.284 0-112.5-46.216-112.5-112.5l0-675c0-66.284 46.216-112.5 112.5-112.5l675 0c66.284 0 112.5 46.216 112.5 112.5l0 675c0 66.284-46.216 112.5-112.5 112.5zM99.5 212l0 75 150 0-72.858-182.135c-46.619 13.532-77.142 53.522-77.142 107.135zM249.5 99.5l75.001 187.5 112.481 0-74.982-187.5-112.5 0zM436.982 99.5l75.018 187.5 112.5 0-75-187.5-112.519 0zM624.5 99.5l75 187.5 112.5 0-75-187.5-112.5 0zM924.5 212c0-66.284-46.216-112.5-112.5-112.5l75.001 187.5 37.499 0 0-75zM924.5 324.5l-824.999 0 0 487.5c0 66.284 46.216 112.5 112.5 112.5l600 0c66.284 0 112.5-46.216 112.5-112.5l0-487.5zM362 437l337.5 187.5-337.5 187.5 0-374.999z" fill="currentColor"/>
              </svg>
            </span>
            <span class="guide-label" :class="item.colorClass">{{ item.label }}</span>
          </div>
          <div class="guide-sub">{{ item.sub }}</div>
        </div>
      </div>
    </div>

    <!-- 切换确认提示 -->
    <transition name="bounce">
      <div v-if="confirmedGesture" class="confirm-toast">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="20 6 9 17 4 12" />
        </svg>
        {{ confirmedGesture }}
      </div>
    </transition>

    <!-- 视频弹窗 -->
    <transition name="fade">
      <div v-if="showVideoModal" class="video-modal-overlay" @click="closeVideoModal">
        <div class="video-modal" @click.stop>
          <button class="video-close-btn" @click="closeVideoModal">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
          <video 
            :src="gestureVideo" 
            controls 
            autoplay 
            class="gesture-video"
          />
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue';
import gestureVideo from '@/assets/gesture.mp4';

const props = defineProps({
  gestureState: {
    type: Object,
    required: true
  },
  hideStatusBar: {
    type: Boolean,
    default: false
  },
  stabilityCount: {
    type: Number,
    default: 0
  },
  confirmedGesture: {
    type: String,
    default: null
  }
});

const STABILITY_THRESHOLD = 12;
const showVideoModal = ref(false);

const guideItems = [
  { key: '握拳', label: '空间旋转', sub: '拳头上下左右移动即旋转图谱', colorClass: 'text-blue' },
  { key: '张开', label: '切换列表', sub: '保持手势1-6静止即可切换图谱，需手背面向摄像头，否则无法识别。细节可参考视频。', hasVideo: true },
  { key: '捏合', label: '深度缩放', sub: '食指与拇指靠近/远离从而缩小/放大图谱', colorClass: 'text-amber' }
];

const gestureStatus = computed(() => {
  const { type } = props.gestureState;
  if (type === 'NONE') return '寻找手部...';
  if (type === 'FIST') return '握拳旋转 (随手势位移)';
  if (type === 'ZOOM') return '视图缩放 (捏合/张开)';
  if (type.startsWith('SELECT_')) {
    const idx = parseInt(type.split('_')[1]);
    return `检测到手势 ${idx} (保持静止)`;
  }
  return '检测中...';
});

function openVideoModal() {
  showVideoModal.value = true;
}

function closeVideoModal() {
  showVideoModal.value = false;
}
</script>

<style scoped>
.gesture-guide {
  pointer-events: none;
  position: fixed;
  inset: 0;
  z-index: 10; /* 降低层级，避免遮挡底部控制面板 */
}

.status-bar {
  position: absolute;
  bottom: 100px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 5;
}

.status-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}

.stability-progress {
  width: 256px;
  height: 6px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 999px;
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.progress-bar {
  height: 100%;
  background: #3b82f6;
  box-shadow: 0 0 15px #3b82f6;
  border-radius: 999px;
  transition: width 75ms ease;
}

.status-info {
  display: flex;
  align-items: center;
  gap: 8px;
  /* padding: 10px 20px; */
  /* background: var(--glass-bg); */
  /* backdrop-filter: blur(25px) saturate(180%);
  -webkit-backdrop-filter: blur(25px) saturate(180%); */
  /* border: var(--glass-border);
  box-shadow: var(--panel-shadow);
  border-radius: 16px; */
  min-width: 200px;
}

.status-icon {
  padding: 12px;
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.05);
  color: rgba(255, 255, 255, 0.2);
  transition: all 0.3s;
}

.status-icon.active {
  background: #3b82f6;
  color: white;
}

.status-text {
  display: flex;
  flex-direction: column;
}

.status-label {
  font-size: 9px;
  color: rgba(255, 255, 255, 0.3);
  font-weight: 900;
  text-transform: uppercase;
  letter-spacing: 0.1em;
  margin-bottom: 2px;
}

.status-value {
  font-size: 14px;
  font-weight: bold;
  color: white;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.guide-panel {
  position: absolute;
  top: 180px;
  right: 24px;
  padding: 24px;
  background: var(--glass-bg);
  backdrop-filter: blur(25px) saturate(180%);
  -webkit-backdrop-filter: blur(25px) saturate(180%);
  border: var(--glass-border);
  box-shadow: var(--panel-shadow);
  border-radius: 24px;
  width: 288px;
  z-index: 30;
}

.guide-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 24px;
}

.guide-header svg {
  color: #60a5fa;
}

.guide-header h4 {
  font-size: 10px;
  font-weight: 900;
  color: rgba(255, 255, 255, 0.8);
  text-transform: uppercase;
  letter-spacing: 0.1em;
  margin: 0;
}

.guide-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.guide-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.guide-item-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.guide-key-wrapper {
  display: flex;
  align-items: center;
  gap: 8px;
}

.guide-key {
  background: rgba(255, 255, 255, 0.1);
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 14px;
  color: white;
  font-family: monospace;
  font-weight: bold;
}

.guide-label {
  font-size: 14px;
  font-weight: bold;
  color: rgba(255, 255, 255, 0.7);
}

.guide-label.text-blue {
  color: #60a5fa;
}

.guide-label.text-amber {
  color: #fbbf24;
}

.guide-sub {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.3);
  line-height: 1.4;
}

.confirm-toast {
  position: absolute;
  top: 80px;
  left: 50%;
  transform: translateX(-50%);
  padding: 12px 24px;
  background: rgba(16, 185, 129, 0.2);
  border: 1px solid rgba(16, 185, 129, 0.5);
  border-radius: 999px;
  color: #10b981;
  font-weight: bold;
  font-size: 12px;
  display: flex;
  align-items: center;
  gap: 8px;
  backdrop-filter: blur(8px);
  z-index: 50;
}

.bounce-enter-active {
  animation: bounceIn 0.5s;
}

.bounce-leave-active {
  animation: bounceOut 0.3s;
}

@keyframes bounceIn {
  0% {
    transform: translateX(-50%) translateY(-20px);
    opacity: 0;
  }
  50% {
    transform: translateX(-50%) translateY(5px);
  }
  100% {
    transform: translateX(-50%) translateY(0);
    opacity: 1;
  }
}

@keyframes bounceOut {
  0% {
    transform: translateX(-50%) translateY(0);
    opacity: 1;
  }
  100% {
    transform: translateX(-50%) translateY(-20px);
    opacity: 0;
  }
}

/* 视频图标样式 */
.video-icon {
  display: block;
  cursor: pointer;
  color: rgba(255, 255, 255, 0.5);
  transition: color 0.2s ease, transform 0.2s ease;
  pointer-events: auto;
}

.video-icon:hover {
  color: #3b82f6;
  transform: scale(1.1);
}

/* 视频弹窗样式 */
.video-modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
  pointer-events: auto;
}

.video-modal {
  position: relative;
  max-width: 90vw;
  max-height: 90vh;
  background: #1a1a1a;
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 25px 50px rgba(0, 0, 0, 0.5);
}

.video-close-btn {
  position: absolute;
  top: 12px;
  right: 12px;
  width: 36px;
  height: 36px;
  border: none;
  background: rgba(0, 0, 0, 0.6);
  border-radius: 50%;
  color: white;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10;
  transition: background 0.2s ease, transform 0.2s ease;
}

.video-close-btn:hover {
  background: rgba(59, 130, 246, 0.8);
  transform: scale(1.1);
}

.gesture-video {
  display: block;
  max-width: 80vw;
  max-height: 80vh;
  width: auto;
  height: auto;
}

/* 淡入淡出动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
