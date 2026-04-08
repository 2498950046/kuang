<template>
  <div class="top-banner" ref="bannerRef">
    <span class="banner-text">{{ title }}</span>
  </div>
</template>

<script setup>
import { ref } from 'vue';

defineProps({
  title: { type: String, default: '' }
});

const bannerRef = ref(null);

defineExpose({
  bannerRef
});
</script>

<style scoped>
.top-banner {
  position: absolute;
  top: -28px;
  left: 50%;
  transform: translateX(-50%);
  padding: 14px 60px;
  border-radius: 0 0 18px 18px;
  background: url('@/assets/title.png') center center / cover no-repeat;
  background-size: 70% 100%;
  box-shadow: none;
  border: none;
  color: #ffffff;
  letter-spacing: 4px;
  font-weight: 800;
  font-size: 2rem;
  z-index: 22;
  min-height: 100px;
  min-width: 520px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.banner-text {
  text-shadow: 0 0 10px rgba(0, 195, 255, 0.5);
  padding: 6px 48px 10px;
}
</style>

