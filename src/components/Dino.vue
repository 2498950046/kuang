<template>
  <div 
    class="dino-wrapper" 
    @mousedown="startDrag"
    @click="handleClick"
    :style="{ left: position.x + 'px', top: position.y + 'px' }"
  >
    <!-- 第一个视频：打盹状态；用 v-if 代替 v-show 避免卸载时 setDisplay 报错 -->
    <video 
      v-if="activeVideo === 'sleep'"
      ref="sleepVideo" 
      src="/src/assets/webfront.webm" 
      muted 
      playsinline
      loop
    ></video>

    <!-- 第二个视频：清醒/响应状态 -->
    <video 
      v-if="activeVideo === 'awake'"
      ref="awakeVideo" 
      src="/src/assets/weball.webm" 
      muted 
      playsinline
      preload="auto"
    ></video>

  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onBeforeUnmount } from "vue";

const emit = defineEmits(['navigate-to-ai']);

const activeVideo = ref("sleep");
const sleepVideo = ref(null);
const awakeVideo = ref(null);

// 用于存储 timeupdate 事件的处理器
let awakeTimeUpdateHandler = null;

// --- 核心视频控制逻辑 ---

// 鼠标移入 -> 播放awake视频从2s到5s
const handleMouseEnter = () => {
  activeVideo.value = "awake";
  const video = awakeVideo.value;
  if (!video) return;

  if (video.currentTime >= 5 && video.paused) return;

  if (awakeTimeUpdateHandler) {
    video.removeEventListener('timeupdate', awakeTimeUpdateHandler);
    awakeTimeUpdateHandler = null;
  }
  
  video.currentTime = 2;
  video.play();

  awakeTimeUpdateHandler = () => {
    if (video.currentTime >= 5) {
      video.pause();
      video.removeEventListener('timeupdate', awakeTimeUpdateHandler);
      awakeTimeUpdateHandler = null;
    }
  };
  video.addEventListener('timeupdate', awakeTimeUpdateHandler);
};

// 点击 -> 触发导航到智能问答页面
const handleClick = () => {
  // 【核心改动】通过计算移动距离来判断是拖拽还是点击
  if (dragging) return;
  if (Math.abs(mouseDownPosition.x - mouseUpPosition.x) > 5 || Math.abs(mouseDownPosition.y - mouseUpPosition.y) > 5) {
    return; // 移动距离超过阈值，认为是拖拽，不执行点击逻辑
  }
  
  // 触发导航事件，让父组件切换到智能问答页面（移除状态检查，任何状态下都可以点击）
  emit('navigate-to-ai');
  
  // 清理 awake 视频的事件监听器（如果存在）
  if (activeVideo.value === 'awake') {
    const video = awakeVideo.value;
    if (video && awakeTimeUpdateHandler) {
      video.removeEventListener('timeupdate', awakeTimeUpdateHandler);
      awakeTimeUpdateHandler = null;
    }
  }
  
  // 重置视频状态
  activeVideo.value = "sleep";
  const awakeVid = awakeVideo.value;
  if (awakeVid) {
    awakeVid.pause();
    awakeVid.currentTime = 2;
  }
};

// 鼠标移出 -> 切换回睡眠视频
const handleMouseLeave = () => {
  activeVideo.value = "sleep";
  const video = awakeVideo.value;
  if (!video) return;

  video.pause();
  video.currentTime = 2;

  if (awakeTimeUpdateHandler) {
    video.removeEventListener('timeupdate', awakeTimeUpdateHandler);
    awakeTimeUpdateHandler = null;
  }
};


// --- 拖拽逻辑 ---
const position = reactive({ x: window.innerWidth - 220, y: window.innerHeight - 250 });
let dragging = false;
let offsetX = 0;
let offsetY = 0;

// 【新增】用于记录鼠标按下和松开时的位置
const mouseDownPosition = reactive({ x: 0, y: 0 });
const mouseUpPosition = reactive({ x: 0, y: 0 });

const startDrag = (e) => {
  dragging = true;
  offsetX = e.clientX - position.x;
  offsetY = e.clientY - position.y;

  // 【核心改动】记录鼠标按下时的位置
  mouseDownPosition.x = e.clientX;
  mouseDownPosition.y = e.clientY;

  document.addEventListener("mousemove", onDrag);
  document.addEventListener("mouseup", stopDrag);
};

const onDrag = (e) => {
  if (!dragging) return;
  // 限制拖拽范围，保持在视口内
  const maxX = window.innerWidth - 200;
  const maxY = window.innerHeight - 200;
  const minX = 0;
  const minY = 0;
  
  position.x = Math.max(minX, Math.min(maxX, e.clientX - offsetX));
  position.y = Math.max(minY, Math.min(maxY, e.clientY - offsetY));
};

const stopDrag = (e) => {
  dragging = false;
  
  // 【核心改动】记录鼠标松开时的位置
  mouseUpPosition.x = e.clientX;
  mouseUpPosition.y = e.clientY;

  document.removeEventListener("mousemove", onDrag);
  document.removeEventListener("mouseup", stopDrag);
};

// --- 生命周期 ---
let resizeHandler = null;

onMounted(() => {
  const sleepVid = sleepVideo.value;
  if (sleepVid) {
    sleepVid.play();
  }

  const awakeVid = awakeVideo.value;
  if (awakeVid) {
    awakeVid.pause();
    awakeVid.currentTime = 2;
  }

  // 初始化位置到右下角
  position.x = window.innerWidth - 220;
  position.y = window.innerHeight - 250;

  // 监听窗口大小变化，保持右下角位置
  resizeHandler = () => {
    const rightEdge = window.innerWidth - 200;
    const bottomEdge = window.innerHeight - 200;
    
    // 如果当前位置超出视口，调整到右下角
    if (position.x > rightEdge || position.x < 0) {
      position.x = Math.max(0, Math.min(rightEdge, window.innerWidth - 220));
    }
    if (position.y > bottomEdge || position.y < 0) {
      position.y = Math.max(0, Math.min(bottomEdge, window.innerHeight - 250));
    }
  };

  window.addEventListener('resize', resizeHandler);
});

onBeforeUnmount(() => {
  if (resizeHandler) {
    window.removeEventListener('resize', resizeHandler);
  }
});
</script>

<style scoped>
.dino-wrapper {
  position: fixed;
  width: 200px;
  height: auto;
  cursor: grab;
  user-select: none;
  /* 低于底部 Dock(z-index:30)，避免覆盖按钮 */
  z-index: 25;
  display: flex;
  flex-direction: column;
  align-items: center;
}
.dino-wrapper:active {
  cursor: grabbing;
}
video {
  width: 100%;
  height: auto;
  display: block;
  pointer-events: auto;
}
</style>
