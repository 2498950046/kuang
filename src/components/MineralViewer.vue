<template>
  <div class="viewer-wrapper">
    <!-- 3D 模型容器 -->
    <div class="model-container">
      <model-viewer
        v-if="src && isModelViewerReady"
        :src="src"
        :alt="alt"
        :auto-rotate="autoRotate"
        :camera-controls="cameraControls"
        :shadow-intensity="shadowIntensity"
        :exposure="exposure"
        :interaction-policy="cameraControls ? 'allow-when-focused' : 'none'"
        camera-orbit="0deg 75deg 4.5m"
        field-of-view="30deg"
        reveal="auto"
        ar
        ar-modes="webxr scene-viewer quick-look"
        environment-image="neutral"
        style="width: 100%; height: 100%; background-color: transparent;"
        @load="onModelLoad"
        @progress="onProgress"
        @error="onError"
      >
      </model-viewer>
      <div v-if="loading && src" class="loading">
      <div class="spinner"></div>
      <p>{{ Math.round(progress * 100) }}% 加载中...</p>
    </div>
      <div v-if="error" class="error-message">
        <p>模型加载失败</p>
        <p class="error-detail">{{ error }}</p>
      </div>
      <div v-if="!src" class="model-placeholder">
        <p>暂无 3D 模型</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue';

const props = defineProps({
  src: {
    type: String,
    default: ''
  },
  alt: {
    type: String,
    default: '3D 模型'
  },
  autoRotate: {
    type: Boolean,
    default: true
  },
  cameraControls: {
    type: Boolean,
    default: true
  },
  shadowIntensity: {
    type: Number,
    default: 1
  },
  exposure: {
    type: Number,
    default: 1
  }
});

const loading = ref(true);
const progress = ref(0);
const error = ref(null);
const isModelViewerReady = ref(false);

// 检查 model-viewer 是否可用
const checkModelViewer = () => {
  if (typeof customElements !== 'undefined') {
    customElements.whenDefined('model-viewer').then(() => {
      isModelViewerReady.value = true;
      console.log('model-viewer 已就绪');
    }).catch(() => {
      // 如果未定义，尝试等待
      setTimeout(() => {
        if (customElements.get('model-viewer')) {
          isModelViewerReady.value = true;
        } else {
          console.warn('model-viewer 未加载，尝试动态加载');
          // 动态加载 model-viewer
          const script = document.createElement('script');
          script.type = 'module';
          script.src = 'https://unpkg.com/@google/model-viewer/dist/model-viewer.min.js';
          script.onload = () => {
            isModelViewerReady.value = true;
            console.log('model-viewer 动态加载完成');
          };
          script.onerror = () => {
            error.value = '无法加载 model-viewer 库';
            console.error('model-viewer 加载失败');
          };
          document.head.appendChild(script);
        }
      }, 100);
    });
  }
};

onMounted(() => {
  checkModelViewer();
});

watch(() => props.src, (newSrc) => {
  if (newSrc) {
    loading.value = true;
    error.value = null;
    progress.value = 0;
    console.log('准备加载模型:', newSrc);
  }
}, { immediate: true });

const onModelLoad = () => {
  loading.value = false;
  progress.value = 1;
  error.value = null;
  console.log('3D 模型加载完成:', props.src);
};

const onProgress = (event) => {
  if (event.detail && event.detail.totalProgress !== undefined) {
    progress.value = event.detail.totalProgress;
    loading.value = progress.value < 1;
  }
};

const onError = (event) => {
  loading.value = false;
  const errorMsg = event.detail?.message || '未知错误';
  error.value = errorMsg;
  console.error('3D 模型加载失败:', event, '模型路径:', props.src);
};
</script>

<style scoped>
.viewer-wrapper {
  position: relative;
  width: 100%;
  height: 100%;
  min-height: 400px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.loading {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  color: white;
  text-align: center;
  z-index: 10;
}

.spinner {
  border: 4px solid rgba(255, 255, 255, 0.2);
  border-top: 4px solid #fff;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  margin: 0 auto 10px;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.model-container {
  width: 100%;
  height: 100%;
  min-height: 400px;
  position: relative;
  background: transparent;
}

/* 确保 model-viewer 正确显示 */
.model-container model-viewer {
  width: 100% !important;
  height: 100% !important;
  background-color: transparent !important;
}

.model-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  color: rgba(255, 255, 255, 0.7);
}

.model-placeholder p {
  margin: 8px 0;
}

.error-message {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: rgba(255, 0, 0, 0.1);
  border-radius: 8px;
  color: rgba(255, 255, 255, 0.9);
  padding: 20px;
}

.error-message p {
  margin: 8px 0;
}

.error-detail {
  font-size: 0.85em;
  color: rgba(255, 255, 255, 0.6);
}

.hint {
  font-size: 0.85em;
  color: rgba(255, 255, 255, 0.5);
}
</style>

