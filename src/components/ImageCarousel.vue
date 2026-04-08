<template>
  <div class="image-carousel">
    <div v-if="loading" class="no-image loading">
      <div class="loading-content">
        <div class="spinner-ring"></div>
        <p class="loading-text">图片加载中…</p>
      </div>
    </div>
    <div v-else-if="images.length === 0" class="no-image">
      <div class="placeholder-content">
        <p class="placeholder-title">矿物标本预览</p>
        <p class="placeholder-subtitle">暂无图片，或图片加载失败</p>
      </div>
    </div>
    <div v-else class="carousel-container">
      <!-- 图片展示区域 -->
      <div class="image-wrapper">
        <img 
          v-for="(img, index) in images" 
          :key="index"
          :src="img" 
          :alt="`${name} 图像 ${index + 1}`"
          class="carousel-image"
          :class="{ active: index === currentIndex }"
          @error="handleImageError"
        />
      </div>
      
      <!-- 左右切换按钮 -->
      <button 
        v-if="images.length > 1"
        class="nav-button prev" 
        @click="prevImage"
        aria-label="上一张"
      >
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="currentColor">
          <path d="M15 18l-6-6 6-6" />
        </svg>
      </button>
      <button 
        v-if="images.length > 1"
        class="nav-button next" 
        @click="nextImage"
        aria-label="下一张"
      >
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="24" height="24" fill="currentColor">
          <path d="M9 18l6-6-6-6" />
        </svg>
      </button>
      
      <!-- 底部指示器 -->
      <div v-if="images.length > 1" class="indicators">
        <button
          v-for="(img, index) in images"
          :key="index"
          class="indicator"
          :class="{ active: index === currentIndex }"
          @click="goToImage(index)"
          :aria-label="`跳转到第 ${index + 1} 张图片`"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue';

const props = defineProps({
  images: {
    type: Array,
    default: () => []
  },
  name: {
    type: String,
    default: ''
  },
  loading: {
    type: Boolean,
    default: false
  },
  autoplay: {
    type: Boolean,
    default: true
  },
  interval: {
    type: Number,
    default: 3000
  }
});

const currentIndex = ref(0);
let autoplayTimer = null;

// 上一张
function prevImage() {
  if (props.images.length === 0) return;
  currentIndex.value = (currentIndex.value - 1 + props.images.length) % props.images.length;
  resetAutoplay();
}

// 下一张
function nextImage() {
  if (props.images.length === 0) return;
  currentIndex.value = (currentIndex.value + 1) % props.images.length;
  resetAutoplay();
}

// 跳转到指定图片
function goToImage(index) {
  if (index >= 0 && index < props.images.length) {
    currentIndex.value = index;
    resetAutoplay();
  }
}

// 重置自动播放
function resetAutoplay() {
  if (autoplayTimer) {
    clearInterval(autoplayTimer);
    autoplayTimer = null;
  }
  if (props.autoplay && props.images.length > 1) {
    startAutoplay();
  }
}

// 开始自动播放
function startAutoplay() {
  if (props.autoplay && props.images.length > 1) {
    autoplayTimer = setInterval(() => {
      nextImage();
    }, props.interval);
  }
}

// 停止自动播放
function stopAutoplay() {
  if (autoplayTimer) {
    clearInterval(autoplayTimer);
    autoplayTimer = null;
  }
}

function handleImageError(e) {
  e.target.src = '/specimen-placeholder.svg';
}

// 监听图片数组变化
watch(() => props.images, (newImages) => {
  if (newImages && newImages.length > 0) {
    currentIndex.value = 0;
    resetAutoplay();
  }
}, { immediate: true });

onMounted(() => {
  if (props.autoplay && props.images.length > 1) {
    startAutoplay();
  }
});

onUnmounted(() => {
  stopAutoplay();
});
</script>

<style scoped>
.image-carousel {
  width: 100%;
  height: 100%;
  position: relative;
  background: #0f0f11;
  border-radius: 8px;
  overflow: hidden;
  display: block;
  min-height: 400px;
}

.no-image {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.05);
  border: 2px dashed rgba(255, 255, 255, 0.26);
  border-radius: 8px;
}

.no-image.loading {
  border-style: solid;
}

.loading-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  color: rgba(255, 255, 255, 0.9);
}

.spinner-ring {
  width: 32px;
  height: 32px;
  border-radius: 999px;
  border: 3px solid rgba(255, 255, 255, 0.25);
  border-top-color: rgba(255, 255, 255, 0.9);
  animation: carousel-spin 0.8s linear infinite;
}

.loading-text {
  font-size: 13px;
  letter-spacing: 0.04em;
}

@keyframes carousel-spin {
  to {
    transform: rotate(360deg);
  }
}

.placeholder-content {
  text-align: center;
  color: rgba(255, 255, 255, 0.85);
}

.placeholder-title {
  font-size: 20px;
  margin: 0 0 8px 0;
  color: rgba(255, 255, 255, 0.85);
}

.placeholder-subtitle {
  font-size: 12px;
  margin: 0;
  color: rgba(255, 255, 255, 0.6);
}

.carousel-container {
  width: 100%;
  height: 100%;
  position: relative;
  overflow: hidden;
}

.image-wrapper {
  width: 100%;
  height: 100%;
  position: relative;
  overflow: hidden;
}

.carousel-image {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  object-position: center;
  opacity: 0;
  transition: opacity 0.5s ease-in-out;
  display: block;
}

.carousel-image.active {
  opacity: 1;
  z-index: 1;
}

.nav-button {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background: rgba(0, 0, 0, 0.2);
  border: none;
  color: rgb(255, 255, 255);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10;
  transition: opacity 0.3s ease, background 0.3s ease;
  backdrop-filter: blur(8px);
  opacity: 0;
  pointer-events: none;
}

.carousel-container:hover .nav-button {
  opacity: 1;
  pointer-events: auto;
}

.nav-button:hover {
  background: rgba(255, 255, 255, 0.3);
}

.nav-button.prev {
  left: 0px;
}

.nav-button.next {
  right: 0px;
}

.nav-button svg {
  width: 24px;
  height: 24px;
}

.indicators {
  position: absolute;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  gap: 8px;
  z-index: 10;
  background: rgba(0, 0, 0, 0.6);
  padding: 8px 16px;
  border-radius: 20px;
  backdrop-filter: blur(8px);
  pointer-events: auto;
}

.indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  border: none;
  background: rgba(255, 255, 255, 0.4);
  cursor: pointer;
  transition: all 0.3s ease;
  padding: 0;
}

.indicator:hover {
  background: rgba(255, 255, 255, 0.6);
  transform: scale(1.2);
}

.indicator.active {
  background: rgba(255, 255, 255, 0.9);
  width: 24px;
  border-radius: 4px;
}
</style>

