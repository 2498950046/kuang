<template>
  <button
    class="toggle"
    :class="{ 'is-3d': modelValue }"
    @click="$emit('update:modelValue', !modelValue)"
    :aria-pressed="modelValue"
  >
    <!-- 背景 -->
    <div class="toggle-bg"></div>

    <!-- 文字 -->
    <span class="toggle-text">
      {{ modelValue ? '切换至2D' : '切换至3D' }}
    </span>

    <!-- 滑块 -->
    <div class="knob"></div>
  </button>
</template>

<script setup>
defineProps({
  modelValue: {
    type: Boolean,
    default: false
  }
});
defineEmits(['update:modelValue']);
</script>

<style scoped>
.toggle {
  position: relative;
  width: 128px;
  height: 48px;
  border-radius: 9999px;
  cursor: pointer;
  font-size: 15px;
  font-weight: 400;
  text-align: left;
  padding: 3px 6px;
  border: none;
  background: transparent;
  outline: none;
}

.toggle-bg {
  position: absolute;
  inset: 0;
  border-radius: inherit;
  background: var(--bg-gradient);
  transition: background 0.4s ease;
}

.toggle {
  --bg-gradient: linear-gradient(to right, #22d3ee, #3b82f6, #8b5cf6);
}

.toggle.is-3d {
  --bg-gradient: linear-gradient(to right, #a78bfa, #c084fc, #e879f9);
}

.toggle-text {
  position: relative;
  z-index: 1;
  color: #fff;
  height: 100%;
  display: flex;
  align-items: center;
  pointer-events: none;
  transition: opacity 0.3s ease, transform 0.3s ease, margin-left 0.3s ease, margin-right 0.3s ease;
  opacity: 1;
  transform: translateX(0);
  margin-left: 40px;
  margin-right: 10px;
}

.toggle.is-3d .toggle-text {
  margin-left: 10px;
  margin-right: auto;
  transform: translateX(0);
}

.knob {
  position: absolute;
  top: 4px;
  left: 4px;
  width: 40px;
  height: 40px;
  background: #fff;
  border-radius: 9999px;
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
  transition: left 300ms cubic-bezier(0.22, 1, 0.36, 1);
}

.toggle.is-3d .knob {
  left: calc(100% - 44px);
}
</style>

