<template>
  <div class="gesture-overlay">
    <video ref="videoRef" class="hidden" playsinline muted autoplay :width="480" :height="360" />
    <canvas ref="canvasRef" class="canvas" :width="480" :height="360" />
    
    <div v-if="isLoading" class="loading-overlay">
      <div class="spinner"></div>
      <span class="loading-text">快速启动...</span>
    </div>

    <div class="status-bar">
      <div class="status-indicator">
        <div :class="['status-dot', { active: !isLoading }]"></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount } from 'vue';
import { detectGesture } from '../services/gestureRecognition';

const props = defineProps({
  onGesture: {
    type: Function,
    required: true
  }
});

const videoRef = ref(null);
const canvasRef = ref(null);
const isLoading = ref(true);
const isMounted = ref(true);
const requestRef = ref(null);
let hands = null;
let cameraStream = null;

onMounted(async () => {
  isMounted.value = true;
  
  const initEngine = async () => {
    // 动态加载MediaPipe Hands和drawing_utils
    const loadScript = (src) => {
      return new Promise((resolve, reject) => {
        const existing = document.querySelector(`script[src="${src}"]`);
        if (existing) {
          // 如果已存在，等待一下确保已加载完成
          setTimeout(resolve, 50);
          return;
        }
        const script = document.createElement('script');
        script.src = src;
        script.crossOrigin = 'anonymous';
        script.onload = () => {
          // 给一点时间让库初始化
          setTimeout(resolve, 100);
        };
        script.onerror = reject;
        document.head.appendChild(script);
      });
    };

    try {
      // 检查是否已经在HTML中加载了MediaPipe库
      const hasHands = !!window.Hands;
      const hasDrawConnectors = typeof window.drawConnectors === 'function';
      const hasDrawLandmarks = typeof window.drawLandmarks === 'function';
      const hasHandConnections = !!window.HAND_CONNECTIONS;
      
      // 如果HTML中已加载，直接使用
      if (hasHands && hasDrawConnectors && hasDrawLandmarks && hasHandConnections) {
        setupHands();
        return;
      }
      
      // 否则动态加载
      if (!hasDrawConnectors) {
        await loadScript('https://cdn.jsdelivr.net/npm/@mediapipe/drawing_utils/drawing_utils.js');
      }
      
      if (!hasHands) {
        await loadScript('https://cdn.jsdelivr.net/npm/@mediapipe/hands/hands.js');
      }
      
      // 额外等待确保所有库都初始化完成
      await new Promise(resolve => setTimeout(resolve, 200));
      
      // 再次检查
      const finalHasHands = !!window.Hands;
      const finalHasDrawConnectors = typeof window.drawConnectors === 'function';
      const finalHasDrawLandmarks = typeof window.drawLandmarks === 'function';
      const finalHasHandConnections = !!window.HAND_CONNECTIONS;
      
      if (finalHasHands) {
        // 即使drawing_utils未加载，也继续（只是不绘制骨架）
        if (!finalHasDrawConnectors || !finalHasDrawLandmarks || !finalHasHandConnections) {
          console.warn('MediaPipe drawing_utils not fully loaded, hand skeleton will not be drawn', {
            drawConnectors: finalHasDrawConnectors,
            drawLandmarks: finalHasDrawLandmarks,
            HAND_CONNECTIONS: finalHasHandConnections
          });
        }
        setupHands();
      } else {
        console.error('Failed to load MediaPipe Hands');
        isLoading.value = false;
      }
    } catch (err) {
      console.error('Error loading MediaPipe scripts:', err);
      isLoading.value = false;
    }
  };

  const setupHands = async () => {
    // 从window对象获取Hands类
    const Hands = window.Hands;
    
    if (!Hands) {
      console.error('MediaPipe Hands not available');
      isLoading.value = false;
      return;
    }

    // 检查drawing_utils是否已加载（不强制要求，如果没有就只显示视频不绘制骨架）
    if (!window.drawConnectors || !window.drawLandmarks || !window.HAND_CONNECTIONS) {
      console.warn('MediaPipe drawing_utils not loaded, hand skeleton will not be drawn');
    }

    hands = new Hands({
      locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/hands/${file}`,
    });

    hands.setOptions({
      maxNumHands: 1,
      modelComplexity: 0,
      minDetectionConfidence: 0.5,
      minTrackingConfidence: 0.5,
    });

    hands.onResults((results) => {
      if (!isMounted.value) return;
      if (isLoading.value) isLoading.value = false;
      
      const canvas = canvasRef.value;
      if (!canvas) return;
      
      const ctx = canvas.getContext('2d');
      if (!ctx) return;

      ctx.save();
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.translate(canvas.width, 0);
      ctx.scale(-1, 1);
      ctx.drawImage(results.image, 0, 0, canvas.width, canvas.height);
      
      if (results.multiHandLandmarks && results.multiHandLandmarks.length > 0) {
        const landmarks = results.multiHandLandmarks[0];
        const gesture = detectGesture(landmarks);
        props.onGesture(gesture);

        // 从window对象获取drawing函数（每次回调都重新获取，确保可用）
        const drawConnectors = window.drawConnectors;
        const drawLandmarks = window.drawLandmarks;
        const HAND_CONNECTIONS = window.HAND_CONNECTIONS;

        // 绘制手部骨架（确保函数可用）
        if (typeof drawConnectors === 'function' && typeof drawLandmarks === 'function' && HAND_CONNECTIONS) {
          try {
            const isFist = gesture.type === 'FIST';
            drawConnectors(ctx, landmarks, HAND_CONNECTIONS, { 
              color: isFist ? '#3b82f6' : '#ffffff', 
              lineWidth: 4 
            });
            drawLandmarks(ctx, landmarks, { 
              color: '#ffffff', 
              lineWidth: 1, 
              radius: 2 
            });
            
            // 如果是握拳，在手掌中心绘制高亮圆
            if (isFist) {
              ctx.beginPath();
              ctx.arc(landmarks[9].x * canvas.width, landmarks[9].y * canvas.height, 15, 0, 2 * Math.PI);
              ctx.fillStyle = 'rgba(59, 130, 246, 0.4)';
              ctx.fill();
            }
          } catch (err) {
            // 静默处理drawConnectors相关错误，避免控制台刷屏
            // 只在第一次错误时记录，后续不再记录
            if (err.message && !err.message.includes('drawConnectors') && !err.message.includes('not a function')) {
              console.warn('Error drawing landmarks:', err);
            }
          }
        }
      } else {
        props.onGesture({ type: 'NONE', x: 0, y: 0, distance: 0, fingerCount: 0 });
      }
      ctx.restore();
    });

    try {
      cameraStream = await navigator.mediaDevices.getUserMedia({
        video: { width: 480, height: 360, frameRate: 30 }
      });

      if (videoRef.value) {
        videoRef.value.srcObject = cameraStream;
        // 主动触发一次 play（可能被省电策略拒绝：吞掉异常即可继续识别）
        videoRef.value.play?.().catch(() => {});
        videoRef.value.onloadedmetadata = () => {
          // play 可能会因为省电/策略被拒绝，忽略该异常，但仍会继续走 hands.send 循环
          videoRef.value?.play?.().catch(() => {});
        };

        const processFrame = async () => {
          if (!isMounted.value || !videoRef.value || !hands) return;
          // 部分浏览器在隐藏/省电策略下 readyState 可能不会立刻到 >=2
          // 先放宽到 >=1 以便尽快启动 MediaPipe 推理。
          if (videoRef.value.readyState >= 1) {
            try {
              await hands.send({ image: videoRef.value });
            } catch (e) {
              // 静默处理处理错误，避免控制台刷屏
              // 只在非drawConnectors相关错误时记录
              if (e.message && !e.message.includes('drawConnectors') && !e.message.includes('not a function')) {
                console.warn('Hands processing error:', e);
              }
            }
          }
          requestRef.value = requestAnimationFrame(processFrame);
        };
        requestRef.value = requestAnimationFrame(processFrame);
      }
    } catch (err) {
      console.error('Camera access error:', err);
      isLoading.value = false;
    }
  };

  initEngine();
});

onBeforeUnmount(() => {
  isMounted.value = false;
  if (requestRef.value) cancelAnimationFrame(requestRef.value);
  if (cameraStream) {
    cameraStream.getTracks().forEach(track => track.stop());
  }
  if (hands) hands.close();
});
</script>

<style scoped>
.gesture-overlay {
  position: fixed;
  top: 0px;
  right: 24px;
  width: 288px;
  height: 160px;
  z-index: 50;
  border-radius: 16px;
  overflow: hidden;
  background: rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(12px);
  border: 2px solid rgba(59, 130, 246, 0.3);
  box-shadow: 0 0 30px rgba(0, 0, 0, 0.5);
}

.canvas {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.hidden {
  position: absolute;
  left: -100000px;
  top: 0;
  width: 1px;
  height: 1px;
  opacity: 0;
  pointer-events: none;
}

.loading-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: rgba(15, 23, 42, 0.9);
  backdrop-filter: blur(8px);
}

.spinner {
  width: 32px;
  height: 32px;
  border: 2px solid #3b82f6;
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.loading-text {
  margin-top: 16px;
  font-size: 9px;
  color: #60a5fa;
  font-weight: 900;
  text-transform: uppercase;
  letter-spacing: 0.2em;
}

.status-bar {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  padding: 8px;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  pointer-events: none;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 6px;
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #f59e0b;
  animation: pulse 2s ease-in-out infinite;
}

.status-dot.active {
  background: #10b981;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

</style>
