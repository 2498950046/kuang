<template>
  <div
    class="mineral-detail-panel"
    ref="panelRef"
    @click.stop
  >
    <div class="detail-header">
      <h3 :style="{ color: mineralTitleColor }">
        {{ mineralDetail?.name || '矿物详情' }}
      </h3>
      <button class="mac-close-btn" @click="onClose" title="关闭">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="18" y1="6" x2="6" y2="18"></line>
          <line x1="6" y1="6" x2="18" y2="18"></line>
        </svg>
      </button>
    </div>
    <div class="detail-scroll-area">
      <div class="detail-body">
        <div class="detail-left">
          <div class="specimen-viewer" ref="fullscreenTargetRef">
            <template v-if="isGemstoneGraph && activeSpecimen && activeSpecimen.bigImages.length > 0">
              <GemstoneImageCarousel 
                :images="activeSpecimen.bigImages"
                width="100%"
                height="300px" 
                :autoplay="true"
                :interval="3000"
              />
            </template>
            <template v-else-if="activeSpecimen">
              <div
                class="specimen-image-card"
                @mousedown.prevent="onImagePointerDown"
                @mousemove.prevent="onImagePointerMove"
                @mouseup.prevent="onImagePointerUp"
                @mouseleave="onImagePointerUp"
                @touchstart.passive="onImagePointerDown"
                @touchmove.prevent="onImagePointerMove"
                @touchend="onImagePointerUp"
              >
                <div class="specimen-image-wrap" ref="specimenImageWrapRef">
                  <!-- 加载中骨架屏：在任意加载阶段都显示，直到图片真正加载完成 -->
                  <div v-if="isImageLoading" class="specimen-loading-spinner">
                    <div class="spinner-ring"></div>
                    <div class="spinner-text">图片加载中…</div>
                  </div>
                  <!-- 加载失败提示：避免出现空白，给用户明确反馈 -->
                  <div v-else-if="imageError" class="specimen-loading-spinner">
                    <div class="spinner-ring error"></div>
                    <div class="spinner-text">图片加载失败</div>
                  </div>
                  <!-- 实际图片始终占位渲染，叠在骨架/错误层下面 -->
                  <img
                    ref="specimenImageRef"
                    :src="currentSpecimenImage"
                    alt="标本图片"
                    @load="handleImageLoaded"
                    @error="handleImageError"
                    :class="{ 'is-loading': isImageLoading || imageError }"
                  />
                </div>
              </div>
              <div class="specimen-controls-row" v-if="activeSpecimen">
                <div class="specimen-controls-left">
                  <button
                    class="specimen-zoom"
                    @click.stop="onToggleSpecimenFullscreen"
                    title="全屏查看"
                  >
                    ⛶
                  </button>
                  <button
                    v-if="specimenState.samples.length > 1"
                    class="specimen-nav"
                    @click.stop="onPrevSample"
                    title="上一个样本"
                  >‹</button>
                  <button
                    v-if="specimenState.samples.length > 1"
                    class="specimen-nav"
                    @click.stop="onNextSample"
                    title="下一个样本"
                  >›</button>
                </div>
                <div class="specimen-hint">按住左右拖动切换角度</div>
              </div>
            </template>
            <!-- 当还没有 activeSpecimen（例如详情面板刚打开、数据/图片尚未就绪）时，直接显示骨架屏，避免出现空白区域 -->
            <div v-else class="specimen-image-card">
              <div class="specimen-image-wrap">
                <div class="specimen-loading-spinner">
                  <div class="spinner-ring"></div>
                  <div class="spinner-text">图片加载中…</div>
                </div>
              </div>
            </div>
          </div>
          <div class="detail-right mac-card" v-if="activeSpecimen && (activeSpecimen.description && activeSpecimen.description.trim())">
            <h4>特有描述</h4>
            <div class="description-text">{{ activeSpecimen.description }}</div>
          </div>
          <div class="mac-card basic-info" v-if="mineralBasicInfo">
            <h4>基本信息</h4>
            <div class="info-grid">
              <span class="label">名称：</span><span>{{ filterSource(mineralBasicInfo.name) || '-' }}</span>
              <span class="label">颜色：</span><span>{{ filterSource(mineralBasicInfo.color) || '-' }}</span>
              <span class="label">产地：</span><span>{{ filterSource(mineralBasicInfo.location) || '-' }}</span>
              <span class="label">发现年份：</span><span>{{ filterSource(mineralBasicInfo.discoveryYear) || '-' }}</span>
              <template v-if="mineralBasicInfo.categories && mineralBasicInfo.categories.length > 0">
                <span class="label">分类：</span>
                <div class="badges">
                  <span v-for="c in mineralBasicInfo.categories" :key="c" class="badge">{{ filterSource(c) }}</span>
                </div>
              </template>
            </div>
          </div>
        </div>
        <div class="detail-right mac-card">
          <h4>基本描述</h4>
          <div class="description-kv">
            <div
              v-for="(row, idx) in mineralDescriptionKVs"
              :key="idx"
              class="description-row"
              :class="{ 'description-row-full': !row.label }"
            >
              <span
                v-if="row.label"
                class="description-label"
              >
                {{ row.label }}：
              </span>
              <span class="description-value">
                {{ row.value }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, onBeforeUnmount } from 'vue';
import GemstoneImageCarousel from './GemstoneImageCarousel.vue';

const props = defineProps({
  mineralTitleColor: { type: String, default: '#ffffff' },
  mineralDetail: { type: Object, default: null },
  activeSpecimen: { type: Object, default: null },
  specimenState: { type: Object, required: true },
  currentSpecimenImage: { type: String, default: '' },
  specimenDescription: { type: String, default: '' },
  mineralBasicInfo: { type: Object, default: null },
  mineralDescriptionKVs: { type: Array, default: () => [] },
  mineralDetailImage: { type: String, default: '' },
  onClose: { type: Function, required: true },
  onToggleSpecimenFullscreen: { type: Function, required: true },
  onPrevSample: { type: Function, required: true },
  onNextSample: { type: Function, required: true },
  onImagePointerDown: { type: Function, required: true },
  onImagePointerMove: { type: Function, required: true },
  onImagePointerUp: { type: Function, required: true },
  isGemstoneGraph: { type: Boolean, default: false },
});

const panelRef = ref(null);
const specimenImageWrapRef = ref(null);
const fullscreenTargetRef = ref(null);
const specimenImageRef = ref(null);
// 初始进入任意标本时显示一次加载中；一旦首张图片加载成功，本标本生命周期内不再显示加载中
const isImageLoading = ref(true);
const imageError = ref(false);
let preloadImg = null;

function requestSpecimenFullscreen() {
  if (!document.fullscreenElement) {
    fullscreenTargetRef.value?.requestFullscreen?.();
  } else {
    document.exitFullscreen?.();
  }
}

/** 过滤「来自Deepseek」类内容，并将「不详」视为空（由模板用 - 展示） */
function filterSource(str) {
  if (str == null || typeof str !== 'string') return str ?? '';
  const s = str
    .replace(/[（(]\s*来自\s*Deepseek\s*[）)]/gi, '')
    .replace(/\s*来自\s*Deepseek\s*/gi, '')
    .replace(/\n\s*来自\s*Deepseek\s*/gi, '')
    .trim();
  return s === '不详' ? '' : s;
}

const onClose = () => props.onClose?.();
const onToggleSpecimenFullscreen = () => requestSpecimenFullscreen();
const onPrevSample = () => props.onPrevSample?.();
const onNextSample = () => props.onNextSample?.();
const onImagePointerDown = (e) => props.onImagePointerDown?.(e);
const onImagePointerMove = (e) => props.onImagePointerMove?.(e);
const onImagePointerUp = (e) => props.onImagePointerUp?.(e);

const handleImageLoaded = () => {
  isImageLoading.value = false;
  imageError.value = false;
};

const handleImageError = () => {
  isImageLoading.value = false;
  imageError.value = true;
};

// 每次切换到新的样品时，才重新显示一次“图片加载中”；
// 使用独立的 Image 对象预加载首张图片，不依赖 imgEl.complete / naturalWidth。
watch(
  () => props.activeSpecimen,
  (newVal, oldVal) => {
    if (newVal && newVal !== oldVal) {
      // 切换到全新的标本：先进入加载中
      isImageLoading.value = true;
      imageError.value = false;

      // 清理上一个预加载器
      if (preloadImg) {
        preloadImg.onload = null;
        preloadImg.onerror = null;
        preloadImg = null;
      }

      const firstUrl =
        props.currentSpecimenImage ||
        newVal?.bigImages?.[0] ||
        newVal?.smallImages?.[0] ||
        '';

      if (firstUrl) {
        preloadImg = new Image();
        preloadImg.onload = () => {
          handleImageLoaded();
        };
        preloadImg.onerror = () => {
          handleImageError();
        };
        preloadImg.src = firstUrl;
      } else {
        // 没有任何可用图片 URL，直接视为失败，避免一直转圈
        handleImageError();
      }
    }
  }
);

onBeforeUnmount(() => {
  if (preloadImg) {
    preloadImg.onload = null;
    preloadImg.onerror = null;
    preloadImg = null;
  }
});

</script>

<style scoped>
.mineral-detail-panel {
  position: fixed;
  top: 0;
  right: 0;
  bottom: 0;
  width: 800x;
  max-width: 55vw;
  height: 100vh;
  /* 更柔和的玻璃拟态背景，让右侧面板与整体更融合 */
  background: radial-gradient(circle at top left, #23293a 0%, #131725 35%, #050711 100%);
  backdrop-filter: blur(32px) saturate(180%);
  border-left: 1px solid rgba(255, 255, 255, 0.04);
  box-shadow: -20px 0 40px rgba(0, 0, 0, 0.55);
  display: flex;
  flex-direction: column;
  z-index: 20;
  overflow: hidden;
}

.detail-header {
  padding: 20px 24px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.04);
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: linear-gradient(90deg, rgba(36, 42, 57, 0.98), rgba(36, 42, 57, 0.78));
  flex-shrink: 0;
}

.detail-header h3 {
  margin: 0;
  font-size: 20px;
  font-weight: 700;
  color: var(--text-primary);
}

.mac-close-btn {
  background: transparent;
  border: none;
  font-size: 16px;
  color: var(--text-secondary);
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  opacity: 0.6;
}

.mac-close-btn:hover {
  opacity: 1;
  background: rgba(0, 0, 0, 0.05);
  color: var(--text-primary);
}

.detail-scroll-area {
  flex: 1;
  overflow-y: auto;
  padding: 24px 28px 28px 28px;
  scrollbar-width: thin;
  scrollbar-color: var(--border-color) transparent;
}

.detail-scroll-area::-webkit-scrollbar {
  width: 6px;
}

.detail-scroll-area::-webkit-scrollbar-thumb {
  background: var(--border-color);
  border-radius: 3px;
}

.detail-scroll-area::-webkit-scrollbar-track {
  background: transparent;
}

.detail-body {
  display: grid;
  /* 左侧略窄，右侧更宽一些，突出文字描述区域 */
  grid-template-columns: 1.1fr 1.6fr;
  gap: 24px;
  align-items: start;
}

.detail-left {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.specimen-viewer {
  display: flex;
  flex-direction: column;
  gap: 0;
  height: 220px; /* 进一步修改为 280px，尝试解决重叠问题 */
  width: 100%; /* 宽度占满父容器 */
}

/* 全屏展示时：黑底、图片居中 */
.specimen-viewer:fullscreen,
.specimen-viewer:-webkit-full-screen {
  height: 100vh;
  width: 100vw;
  background: #000;
  justify-content: center;
  align-items: center;
  padding: 0;
}
.specimen-viewer:fullscreen .specimen-image-wrap,
.specimen-viewer:-webkit-full-screen .specimen-image-wrap {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  max-width: 100%;
  max-height: 100%;
}
.specimen-viewer:fullscreen .specimen-image-wrap img,
.specimen-viewer:-webkit-full-screen .specimen-image-wrap img {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
}

.detail-right {
  display: flex;
  flex-direction: column;
}

.detail-right h4 {
  margin: 0 0 16px 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--text-primary);
  display: flex;
  align-items: center;
  gap: 8px;
}

.detail-right h4::before {
  content: '';
  width: 4px;
  height: 16px;
  background: var(--accent-primary);
  border-radius: 2px;
}

.description-kv {
  display: flex;
  flex-direction: column;
  gap: 8px;
  font-size: 14px;
  line-height: 1.6;
}

.description-row {
  display: flex;
  align-items: flex-start;
  /* 确保字段名和内容之间始终有空隙 */
  column-gap: 12px;
}

.description-row-full .description-value {
  margin-left: 0;
}

.description-label {
  /* 定宽，保证所有冒号右侧内容从同一列开始 */
  width: 120px;
  min-width: 120px;
  max-width: 120px;
  flex: 0 0 120px;
  padding-right: 8px;
  font-weight: 600;
  font-size: 15px;
  color: var(--text-primary);
}

.description-value {
  flex: 1;
  color: var(--text-secondary);
  white-space: pre-wrap;
  word-break: break-word;
}

.specimen-image-card {
  width: 100%;
  display: flex;
  flex-direction: column;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  position: relative;
  background: var(--bg-secondary);
  padding: 0;
}

.specimen-image-card img {
  width: 100%;
  height: 100%;
  object-fit: contain;
  transition: transform 0.5s;
}

.specimen-image-card:hover img {
  transform: scale(1.05);
}

.specimen-nav,
.specimen-zoom {
  background: rgba(255, 255, 255, 0.08);
  border: none;
  border-radius: 10px;
  padding: 10px 14px;
  color: inherit;
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 18px;
}

.specimen-zoom {
  color: #fff;
}

.specimen-nav:hover,
.specimen-zoom:hover {
  background: rgba(255, 255, 255, 0.15);
}

.specimen-image-wrap {
  position: relative;
  border-radius: 0;
  overflow: hidden;
  background: rgba(0, 0, 0, 0.2);
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  flex: 1;
  width: 100%;
}

.specimen-image-wrap img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.specimen-image-wrap img.is-loading {
  opacity: 0.2;
  transition: opacity 0.2s ease-out;
}

.specimen-loading-spinner {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  background: radial-gradient(circle at center, rgba(0, 0, 0, 0.45), rgba(0, 0, 0, 0.75));
  color: rgba(255, 255, 255, 0.9);
  z-index: 2;
}

.spinner-ring {
  width: 32px;
  height: 32px;
  border-radius: 999px;
  border: 3px solid rgba(255, 255, 255, 0.25);
  border-top-color: rgba(255, 255, 255, 0.9);
  animation: specimen-spin 0.8s linear infinite;
}

.spinner-text {
  font-size: 13px;
  letter-spacing: 0.04em;
}

@keyframes specimen-spin {
  to {
    transform: rotate(360deg);
  }
}

.specimen-controls-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.specimen-controls-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.specimen-hint {
  flex: 1;
  text-align: right;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.75);
  white-space: nowrap;
}

.mac-card {
  background: rgb(36,42,57);
  border-radius: 12px;
  padding: 20px;
  border: 1px solid rgba(125,125,125,0.08);
}

.basic-info h4 {
  margin: 0 0 12px 0;
  opacity: 0.9;
  font-size: 1.2rem;
  font-weight: 600;
  color: var(--text-primary);
  display: flex;
  align-items: center;
  gap: 6px;
}

.basic-info h4::before {
  content: 'ⓘ';
  font-size: 14px;
  opacity: 0.7;
}

.basic-info .info-grid {
  display: grid;
  grid-template-columns: 80px 1fr;
  gap: 8px 4px;
  row-gap: 8px;
}

.basic-info .label {
  color: rgba(255, 255, 255, 1);
}

.basic-info .info-grid > span:not(.label) {
  color: rgba(255, 255, 255, 0.7);
}

.basic-info .badges {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 0;
  align-items: center;
}

.basic-info .badge {
  background: rgba(255, 255, 255, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 4px;
  padding: 2px 8px;
  font-size: 0.85em;
  color: white;
  cursor: pointer;
}

.basic-info .badge:hover {
  background: rgba(255, 255, 255, 0.3);
}

.description-text {
  line-height: 1.8;
  font-size: 14px;
  color: var(--text-primary);
  white-space: pre-line;
  word-break: break-word;
}
</style>



