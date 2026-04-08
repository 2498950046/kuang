<template>
  <div 
    class="mineral-card"
    :style="{ '--accent-color': color }"
    @mouseenter="isHovered = true"
    @mouseleave="isHovered = false"
    @click="$emit('click')"
  >
    <!-- Gradient overlay -->
    <div class="gradient-overlay" :class="{ active: isHovered }" />
    
    <!-- Image -->
    <div class="image-container">
      <!-- 占位符（加载中显示） -->
      <div v-if="!imageLoaded && !imageError" class="image-placeholder">
        <div class="placeholder-spinner"></div>
      </div>
      <!-- 实际图片（始终渲染，让浏览器开始加载） -->
      <img
        :src="currentImageUrl"
        :alt="name"
        class="mineral-image"
        :class="{ hovered: isHovered, 'image-error': imageError, 'image-loaded': imageLoaded }"
        loading="lazy"
        decoding="async"
        referrerpolicy="no-referrer"
        @error="handleImageError"
        @load="handleImageLoad"
      />
      <!-- 错误占位符（加载失败时显示） -->
      <div v-if="imageError" class="image-error-placeholder">
        <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
          <circle cx="8.5" cy="8.5" r="1.5"/>
          <polyline points="21 15 16 10 5 21"/>
        </svg>
      </div>
    </div>
    
    <!-- Content -->
    <div class="content">
      <div class="header">
        <svg class="sparkle-icon" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M9.937 15.5A2 2 0 0 0 8.5 14.063l-6.135-1.582a.5.5 0 0 1 0-.962L8.5 9.936A2 2 0 0 0 9.937 8.5l1.582-6.135a.5.5 0 0 1 .963 0L14.063 8.5A2 2 0 0 0 15.5 9.937l6.135 1.582a.5.5 0 0 1 0 .963L15.5 14.063a2 2 0 0 0-1.437 1.437l-1.582 6.135a.5.5 0 0 1-.963 0z"/>
        </svg>
        <span class="type-text">{{ type }}</span>
      </div>
      <h3 class="name-text">{{ name }}</h3>
    </div>
    
    <!-- Crystal sparkle effect -->
    <div class="sparkle-dot" :class="{ active: isHovered }" />
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch } from 'vue';

const props = defineProps({
  name: {
    type: String,
    required: true
  },
  type: {
    type: String,
    default: '宝玉石'
  },
  imageUrl: {
    type: String,
    default: '/specimen-placeholder.svg'
  },
  color: {
    type: String,
    default: '#6200EA'
  }
});

const emit = defineEmits(['click']);

const isHovered = ref(false);
const imageError = ref(false);
const imageLoaded = ref(false);
const currentImageUrl = ref(props.imageUrl);

watch(() => props.imageUrl, (newUrl) => {
  if (newUrl && newUrl !== '/specimen-placeholder.svg') {
    currentImageUrl.value = newUrl;
    imageError.value = false;
    imageLoaded.value = false;
  } else if (!newUrl) {
    currentImageUrl.value = '/specimen-placeholder.svg';
    imageError.value = false;
    imageLoaded.value = false;
  }
}, { immediate: true });

function handleImageLoad() {
  imageError.value = false;
  imageLoaded.value = true;
}

function handleImageError() {
  if (currentImageUrl.value === '/specimen-placeholder.svg') {
    return;
  }
  imageError.value = true;
  imageLoaded.value = false;
  currentImageUrl.value = '/specimen-placeholder.svg';
}

onMounted(() => {
  if (props.imageUrl) {
    currentImageUrl.value = props.imageUrl;
  } else {
    currentImageUrl.value = '/specimen-placeholder.svg';
  }
});
</script>

<style scoped>
.mineral-card {
  position: relative;
  overflow: hidden;
  border-radius: 0.75rem;
  background: linear-gradient(to bottom right, rgba(30, 41, 59, 0.8), rgba(15, 23, 42, 0.8));
  backdrop-filter: blur(12px);
  border: 1px solid rgba(51, 65, 85, 0.5);
  cursor: pointer;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
  animation: fadeInUp 0.5s ease forwards;
}

.mineral-card:hover {
  transform: scale(1.05) translateY(-5px);
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.gradient-overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, var(--accent-color), transparent);
  opacity: 0;
  transition: opacity 0.3s ease;
  z-index: 1;
}

.gradient-overlay.active {
  opacity: 0.2;
}

.image-container {
  aspect-ratio: 1;
  overflow: hidden;
  position: relative;
  background: linear-gradient(135deg, rgba(30, 41, 59, 0.5), rgba(15, 23, 42, 0.5));
}

.image-placeholder {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, rgba(30, 41, 59, 0.8), rgba(15, 23, 42, 0.8));
}

.placeholder-spinner {
  width: 32px;
  height: 32px;
  border: 3px solid rgba(255, 255, 255, 0.1);
  border-top-color: var(--accent-color, #6200EA);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.mineral-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: opacity 0.4s ease, transform 0.3s ease;
  opacity: 0;
  will-change: opacity;
}

.mineral-image.image-loaded {
  opacity: 1;
}

.mineral-image.image-error {
  opacity: 0.5;
}

.mineral-image.hovered {
  transform: scale(1.1);
}

.image-error-placeholder {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, rgba(30, 41, 59, 0.8), rgba(15, 23, 42, 0.8));
  color: rgba(148, 163, 184, 0.5);
}

.content {
  padding: 1rem;
  position: relative;
  z-index: 2;
}

.header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.5rem;
}

.sparkle-icon {
  width: 1rem;
  height: 1rem;
  color: var(--accent-color);
}

.type-text {
  font-size: 0.75rem;
  line-height: 1rem;
  color: rgb(148, 163, 184);
}

.name-text {
  color: white;
  margin: 0;
  font-size: 1.1rem;
  font-weight: 600;
}

.sparkle-dot {
  position: absolute;
  top: 0.5rem;
  right: 0.5rem;
  width: 0.5rem;
  height: 0.5rem;
  border-radius: 50%;
  background-color: var(--accent-color);
  opacity: 0;
  transition: opacity 0.3s ease;
  animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
  z-index: 3;
}

.sparkle-dot.active {
  opacity: 1;
}

@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}
</style>

