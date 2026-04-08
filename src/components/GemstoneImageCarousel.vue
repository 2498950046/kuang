<template>
  <div class="image-carousel-container">
    <div class="carousel-container">
      <div class="image-wrapper">
        <img 
          v-for="(image, index) in images" 
          :key="index"
          :src="image"
          :alt="`Image ${index + 1}`"
          class="carousel-image"
          :class="{ active: activeIndex === index }"
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
          :class="{ active: index === activeIndex }"
          @click="goToImage(index)"
          :aria-label="`跳转到第 ${index + 1} 张图片`"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue';

const props = defineProps({
  images: {
    type: Array,
    required: true,
    default: () => [],
  },
  width: {
    type: String,
    default: '100%',
  },
  height: {
    type: String,
    default: '100%',
  },
  autoplay: {
    type: Boolean,
    default: true,
  },
  interval: {
    type: Number,
    default: 3000, // 默认3秒切换
  },
});

const activeIndex = ref(0);
let autoplayTimer = null;

const nextImage = () => {
  activeIndex.value = (activeIndex.value + 1) % props.images.length;
};

const prevImage = () => {
  activeIndex.value = (activeIndex.value - 1 + props.images.length) % props.images.length;
};

const goToImage = (index) => {
  activeIndex.value = index;
};

const startAutoplay = () => {
  if (props.autoplay && props.images.length > 1) {
    clearInterval(autoplayTimer);
    autoplayTimer = setInterval(nextImage, props.interval);
  }
};

const stopAutoplay = () => {
  clearInterval(autoplayTimer);
  autoplayTimer = null;
};

watch(() => props.images.length, () => {
  activeIndex.value = 0;
  stopAutoplay();
  startAutoplay();
});

onMounted(() => {
  startAutoplay();
});

onBeforeUnmount(() => {
  stopAutoplay();
});
</script>

<style scoped>
.image-carousel-container {
  width: 100%;
  height: 100%;
  position: relative;
  background: #0f0f11;
  border-radius: 8px;
  overflow: hidden;
  display: block;
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
  object-fit: cover; /* 修改为 cover，确保图片填充整个容器 */
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
  bottom: 0px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  gap: 8px;
  z-index: 10;
  background: rgba(0, 0, 0, 0.6);
  padding: 4px 10px;
  border-radius: 20px;
  backdrop-filter: blur(8px);
  pointer-events: auto;
}

.indicator {
  width: 4px;
  height: 4px;
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