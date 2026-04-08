<template>
  <span class="text-type">
    <span class="placeholder-text" aria-hidden="true">
      {{ fullText }}<span v-if="showCursor">{{ cursorCharacter }}</span>
    </span>
    <span class="content-wrapper">
      <span class="typed-text">{{ displayedText }}</span>
      <span v-if="showCursor" class="cursor" :class="{ blink: isTyping }">{{ cursorCharacter }}</span>
    </span>
  </span>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'

interface Props {
  text: string[]
  typingSpeed?: number
  pauseDuration?: number
  showCursor?: boolean
  cursorCharacter?: string
  deleteSpeed?: number
}

const props = withDefaults(defineProps<Props>(), {
  typingSpeed: 100,
  pauseDuration: 2000,
  showCursor: true,
  cursorCharacter: '|',
  deleteSpeed: 50
})

const displayedText = ref('')
const currentTextIndex = ref(0)
const isTyping = ref(true)
const isDeleting = ref(false)
let timeoutId: ReturnType<typeof setTimeout> | null = null

// 获取当前完整文字，用于占位符
const fullText = computed(() => {
  return props.text[currentTextIndex.value] || props.text[0] || ''
})

function typeText() {
  const currentText = props.text[currentTextIndex.value]
  
  if (!isDeleting.value && displayedText.value.length < currentText.length) {
    // Typing
    displayedText.value = currentText.substring(0, displayedText.value.length + 1)
    timeoutId = setTimeout(typeText, props.typingSpeed)
  } else if (!isDeleting.value && displayedText.value.length === currentText.length) {
    // Finished typing, pause before deleting
    isDeleting.value = true
    timeoutId = setTimeout(typeText, props.pauseDuration)
  } else if (isDeleting.value && displayedText.value.length > 0) {
    // Deleting
    displayedText.value = displayedText.value.substring(0, displayedText.value.length - 1)
    timeoutId = setTimeout(typeText, props.deleteSpeed)
  } else if (isDeleting.value && displayedText.value.length === 0) {
    // Finished deleting, move to next text
    isDeleting.value = false
    currentTextIndex.value = (currentTextIndex.value + 1) % props.text.length
    timeoutId = setTimeout(typeText, props.typingSpeed)
  }
}

onMounted(() => {
  typeText()
})

onBeforeUnmount(() => {
  if (timeoutId) {
    clearTimeout(timeoutId)
  }
})
</script>

<style scoped>
.text-type {
  display: inline-block;
  position: relative;
}

.placeholder-text {
  opacity: 0;
  display: inline-block;
  white-space: nowrap;
  pointer-events: none;
  user-select: none;
  line-height: inherit;
  font-size: inherit;
  font-weight: inherit;
  letter-spacing: inherit;
  background: linear-gradient(120deg, #fff3df, #ffcf71, #ff9d00);
  background-clip: text;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.content-wrapper {
  display: inline-block;
  position: absolute;
  left: 0;
  top: 0;
  white-space: nowrap;
  line-height: inherit;
  font-size: inherit;
  font-weight: inherit;
  letter-spacing: inherit;
}

.typed-text {
  display: inline-block;
  background: linear-gradient(120deg, #fff3df, #ffcf71, #ff9d00);
  background-clip: text;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  color: transparent;
}

.cursor {
  display: inline-block;
  margin-left: 2px;
  background: linear-gradient(120deg, #fff3df, #ffcf71, #ff9d00);
  background-clip: text;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  animation: blink 1s infinite;
}

.cursor.blink {
  animation: blink 1s infinite;
}

@keyframes blink {
  0%, 50% {
    opacity: 1;
  }
  51%, 100% {
    opacity: 0;
  }
}
</style>

