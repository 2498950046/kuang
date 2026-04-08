<template>
  <div class="sidebar-section">
    <div class="section-header" style="display: flex; justify-content: space-between; align-items: center;">
    </div>

    <div>
      <!-- 聊天模式 -->
      <div v-if="showChat && selectedItem" class="chat-view">
        <PersonChat 
          :personName="selectedItem.data.name" 
          :personAvatar="personImages.length > 0 ? personImages[0] : ''"
          @close="showChat = false" 
        />
      </div>

      <!-- 属性显示模式 -->
      <div v-else-if="selectedItem" class="property-display">
        <div v-if="selectedItem.dataType === 'node'" class="node-properties">
          <h5>
            {{ selectedItem.data.name }}
            <span 
              class="category-tag"
              :style="getCategoryTagStyle(selectedItem.data.category)"
            >
              {{ entityCategoryLabels[selectedItem.data.category] || selectedItem.data.category }}
            </span>
            <!-- 与人物对话按钮 -->
            <button 
              v-if="entityCategoryLabels[selectedItem.data.category] === '前辈' || selectedItem.data.category === '前辈' || selectedItem.data.category === 'Person' || 
              selectedItem.data.properties.person_category && (
                (typeof selectedItem.data.properties.person_category === 'string' && selectedItem.data.properties.person_category.includes('新四军五师前辈')) ||
                (Array.isArray(selectedItem.data.properties.person_category) && selectedItem.data.properties.person_category.includes('新四军五师前辈'))
              )"
              @click="showChat = true"
              class="chat-button"
              title="与人物对话"
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
              </svg>
              对话
            </button>
          </h5>

          <div class="media-container"
            v-if="(entityCategoryLabels[selectedItem.data.category] === '前辈' || selectedItem.data.category === '前辈' || selectedItem.data.category === 'Person') && (personImages.length > 0 || personVideos.length > 0)">

            <div class="media-item image-item" v-if="personImages.length > 0">
              <button @click="prevImage" :disabled="personImages.length <= 1" class="media-nav-btn prev-btn">
                &lt;</button>
              <img :src="personImages[currentImageIndex]"
                style="width:100px; height:100%; margin:3px; vertical-align:middle; object-fit: cover;"
                @error="handleImageError" />
              <button @click="nextImage" :disabled="personImages.length <= 1" class="media-nav-btn next-btn">
                &gt;</button>
              <div v-if="personImages.length > 1" class="media-counter">{{ currentImageIndex + 1 }} / {{
                personImages.length
                }}</div>
            </div>

            <div class="media-item video-item" v-if="personVideos.length > 0">
              <button @click="prevVideo" :disabled="personVideos.length <= 1" class="media-nav-btn prev-btn">
                &lt;</button>
              <video ref="videoPlayer" :src="personVideos[currentVideoIndex]" controls
                style="max-width: 290px; max-height: 250px; margin: 3px;vertical-align:middle;"></video>
              <button @click="nextVideo" :disabled="personVideos.length <= 1" class="media-nav-btn next-btn">
                &gt;</button>
              <div v-if="personVideos.length > 1" class="media-counter">{{ currentVideoIndex + 1 }} / {{
                personVideos.length
                }}</div>
            </div>

            <div class="video-button-container">
              <button v-for="(videoUrl, index) in personVideos" :key="index"
                :class="{ 'video-switch-btn': true, 'active-video-btn': index === currentVideoIndex }"
                @click="switchToVideo(index)" :title="getVideoTitle(videoUrl)">
                {{ getVideoTitle(videoUrl) }}
              </button>
            </div>
          </div>

          <div class="properties-list" v-if="sortedProperties.length > 0">
            <div class="property-item" v-for="prop in sortedProperties" :key="prop.key"
              :class="{ 'is-supplementary': isSupplementary(prop.key) }">

              <template v-if="prop.key !== 'source_info'">
                <span class="property-key">{{ propertyLabels[prop.key] || prop.key }}:</span>
                <span class="property-value" v-html="formatProperty(prop.key, prop.value)"></span>
              </template>

              <div v-else>
                <span class="property-key">{{ propertyLabels[prop.key] || prop.key }}:</span>

                <template v-if="formattedData = formatSourceInfo(prop.value)">
                  <el-tree :data="formattedData.value" :props="{ children: 'children', label: 'label' }"
                    style="max-width: 270px;" :default-expand-all="false" v-if="formattedData.isTree" />

                  <span v-else class="property-value" style="white-space: pre-wrap;" v-html="formattedData.value">
                  </span>
                </template>
              </div>
            </div>
          </div>
          <div v-else class="no-properties">该节点没有额外属性</div>
        </div>

        <div v-else class="edge-properties">
          <div class="relationship-type-badge">
            <div class="badge-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M12 2L2 7l10 5 10-5-10-5z" />
                <path d="M2 17l10 5 10-5" />
                <path d="M2 12l10 5 10-5" />
              </svg>
            </div>
          </div>
          <div class="path-container">
            <div class="entity-card source-card">
              <div class="entity-name" :title="getNodeName(selectedItem.data.source)">
                {{ getNodeName(selectedItem.data.source) }}
              </div>
            </div>

            <div class="connection-visual">
              <div class="connection-line">
                <div class="line-segment"></div>
                <div class="arrow-head">
                  <svg viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12 2L22 12L12 22V16H2V8H12V2Z" />
                  </svg>
                </div>
                <div class="line-segment"></div>
              </div>
            </div>

            <div class="entity-card target-card">
              <div class="entity-name" :title="getNodeName(selectedItem.data.target)">
                {{ getNodeName(selectedItem.data.target) }}
              </div>
            </div>
          </div>

          <div class="properties-list" v-if="sortedProperties.length > 0">
            <div class="property-item" v-for="prop in sortedProperties" :key="prop.key"
              :class="{ 'is-supplementary': isSupplementary(prop.key) }">

              <template v-if="prop.key !== 'source_info'">
                <span class="property-key">{{ propertyLabels[prop.key] || prop.key }}:</span>
                <span class="property-value" v-html="formatProperty(prop.key, prop.value)"></span>
              </template>

              <div v-else>
                <span class="property-key">{{ propertyLabels[prop.key] || prop.key }}:</span>

                <template v-if="formattedData = formatSourceInfo(prop.value)">
                  <el-tree :data="formattedData.value" :props="{ children: 'children', label: 'label' }"
                    style="max-width: 270px;" :default-expand-all="false" v-if="formattedData.isTree" />
                  <span v-else class="property-value" style="white-space: pre-wrap;" v-html="formattedData.value">
                  </span>
                </template>
              </div>
            </div>
          </div>
          <div v-else class="no-properties">该关系没有额外属性</div>
        </div>

      </div>
      <!-- <div v-else class="no-hover">
        <p>鼠标点击节点或关系查看属性</p>
      </div> -->
    </div>

  </div>
</template>

<script setup>
import { computed, ref, watch } from 'vue';
import { formatProperty, getPropertyOrder, formatSourceInfo } from '../utils/formatters.js';
import PersonChat from './PersonChat.vue';

// --- 资源管理状态 ---
const personImages = ref([]);
const personVideos = ref([]);
const currentImageIndex = ref(0);
const currentVideoIndex = ref(0);
const videoPlayer = ref(null); // 用于获取 <video> DOM 元素

// 聊天状态
const showChat = ref(false);

const props = defineProps({
  selectedItem: Object,
  layoutConfig: Object,
  nodes: { type: Array, required: true },
  entityCategoryLabels: Object,
  edgeTypeLabels: Object,
  propertyLabels: Object,
  nodeColorMap: { type: Object, default: () => ({}) },
});

const emit = defineEmits(['update:layoutConfig']);

// --- 资源加载和切换逻辑 ---

// 使用 Vite 的 import.meta.glob 来动态导入资源
const imageModules = import.meta.glob('../assets/person/images/**/*', { eager: true, as: 'url' });
const videoModules = import.meta.glob('../assets/person/videos/**/*', { eager: true, as: 'url' });


/**
 * 从视频路径中提取出文件名中 '_' 后面的部分作为标题。
 * ⭐ 已修复中文乱码问题：通过 decodeURIComponent() 解码 URL 编码后的文件名。
 */
const getVideoTitle = (videoPath) => {
  // 1. 从路径中提取文件名 (e.g., "1_视频标题.mp4" 已经是 URL 编码格式)
  const pathSegments = videoPath.split('/');
  let filenameWithExt = pathSegments[pathSegments.length - 1];

  // ⭐ 核心修复：对文件名进行 URL 解码，将 %E4%B8%AD%E6%96%87 转换为 '中文' ⭐
  try {
    filenameWithExt = decodeURIComponent(filenameWithExt);
  } catch (e) {
    // 保持原始文件名，防止因不规范的URL编码导致程序崩溃
    console.warn("无法解码视频文件名中的中文，可能文件名包含非标准字符:", e);
  }
  // ⭐ 核心修复结束 ⭐

  // 2. 移除文件扩展名 (e.g., "1_视频标题")
  const filename = filenameWithExt.split('.').slice(0, -1).join('.');

  // 3. 查找第一个下划线 '_'
  const underscoreIndex = filename.indexOf('_');

  if (underscoreIndex !== -1 && underscoreIndex < filename.length - 1) {
    // 4. 提取下划线后面的部分作为标题
    return filename.substring(underscoreIndex + 1);
  }

  // 4.1. 如果格式不匹配，返回完整文件名（不含扩展名）作为备用
  return filename;
};


/**
 * 切换到指定视频的函数。
 * @param {number} index - 目标视频的索引。
 */
const switchToVideo = (index) => {
  if (index >= 0 && index < personVideos.value.length) {
    // 切换到不同视频时，暂停当前视频
    if (videoPlayer.value && currentVideoIndex.value !== index) {
      videoPlayer.value.pause();
    }
    currentVideoIndex.value = index;
  }
};


function loadPersonAssets(name) {
  const nameEncoded = name;

  // 1. 查找图片资源
  const images = Object.keys(imageModules)
    .filter(path => path.includes(`/images/${nameEncoded}/`))
    .sort()
    .map(path => imageModules[path]);

  personImages.value = images;
  currentImageIndex.value = 0;

  // 2. 查找视频资源
  const videos = Object.keys(videoModules)
    .filter(path => path.includes(`/videos/${nameEncoded}/`))
    // .sort()
    .sort((a, b) => {
      // 提取数字前缀进行比较
      const numA = parseInt(a.match(/(\d+)_/)?.[1] || 0);
      const numB = parseInt(b.match(/(\d+)_/)?.[1] || 0);
      return numA - numB;
    })
    .map(path => videoModules[path]);

  personVideos.value = videos;
  currentVideoIndex.value = 0;
}

// 切换图片
const nextImage = () => {
  if (personImages.value.length > 1) {
    currentImageIndex.value = (currentImageIndex.value + 1) % personImages.value.length;
  }
};

const prevImage = () => {
  if (personImages.value.length > 1) {
    currentImageIndex.value = (currentImageIndex.value - 1 + personImages.value.length) % personImages.value.length;
  }
};

// 切换视频 (调用 switchToVideo)
const nextVideo = () => {
  if (personVideos.value.length > 1) {
    const nextIndex = (currentVideoIndex.value + 1) % personVideos.value.length;
    switchToVideo(nextIndex);
  }
};

const prevVideo = () => {
  if (personVideos.value.length > 1) {
    const prevIndex = (currentVideoIndex.value - 1 + personVideos.value.length) % personVideos.value.length;
    switchToVideo(prevIndex);
  }
};


// 错误处理：图片加载失败时使用 default.jpg
const handleImageError = (event) => {
  // 设置默认图片路径
  const defaultUrl = new URL('../assets/person/default.jpg', import.meta.url).href;
  if (event.target.src !== defaultUrl) {
    event.target.src = defaultUrl;
  }
}

// 监听选中项变化
watch(() => props.selectedItem, (newItem) => {
  // 重置资源列表和索引
  personImages.value = [];
  personVideos.value = [];
  currentImageIndex.value = 0;
  currentVideoIndex.value = 0;
  showChat.value = false; // 关闭聊天

  // 确保选中项是人物节点
  const isPerson = newItem && newItem.dataType === 'node' &&
    (props.entityCategoryLabels[newItem.data.category] === '前辈' || newItem.data.category === '前辈' || newItem.data.category === 'Person');

  if (isPerson) {
    loadPersonAssets(newItem.data.name);
  }
}, { immediate: true });


// --- 基础图谱工具函数 (不变) ---

function getNodeName(nodeId) {
  const node = props.nodes.find(n => n.id === nodeId);
  return node ? node.name : '未知节点';
}

// 获取分类标签的样式（根据节点类别设置颜色）
function getCategoryTagStyle(category) {
  if (!category || !props.nodeColorMap) return {};
  
  // 获取节点类别的颜色
  const color = props.nodeColorMap[category] || props.nodeColorMap[props.entityCategoryLabels?.[category]];
  
  if (color) {
    return {
      background: color,
      borderColor: color,
    };
  }
  
  return {};
}

function isSupplementary(key) {
  const supplementaryKeys = ['source_info', 'source_text', 'created_at', 'updated_at'];
  return supplementaryKeys.includes(key);
}

const sortedProperties = computed(() => {
  if (!props.selectedItem || !props.selectedItem.data.properties) return [];
  
  // 判断是否是分类节点
  const isCategoryNode = props.selectedItem.dataType === 'node' && 
    (props.selectedItem.data.category === 'Category' || 
     props.selectedItem.data.category === '分类' ||
     props.entityCategoryLabels[props.selectedItem.data.category] === '分类');
  
  // 基础过滤列表
  const baseFilterKeys = ['id', 'ID', 'name', 'Name', 'person_id', 'event_id', 'type', 'battle_id', 'elementId', 'merge_metadata', 'migration_time', 'migrated_from', 'category', 'created_at', 'updated_at'];
  
  // 如果是分类节点，额外过滤掉 system
  const filterKeys = isCategoryNode 
    ? [...baseFilterKeys, 'system', 'System']
    : baseFilterKeys;
  
  return Object.entries(props.selectedItem.data.properties)
    .filter(([key]) => !filterKeys.includes(key))
    .map(([key, value]) => ({ key, value }))
    .sort((a, b) => getPropertyOrder(a.key) - getPropertyOrder(b.key))
    .filter(prop => prop.value);
});

</script>

<style scoped>
/* --- 基础样式保持不变 --- */
.sidebar-section {
  padding: 0 16px;
}

.section-header h4 {
  margin: 0;
  color: var(--text-primary);
}

.property-display {
  padding: 20px;
  background: rgb(36, 42, 57);
  backdrop-filter: blur(16px) saturate(180%);
  border: 1px solid rgba(125, 125, 125, 0.08);
  border-radius: 12px;
  margin-top: 10px;
  max-height: 600px;
  overflow-y: auto;
  box-shadow: 0 0 0 1px rgba(125, 125, 125, 0.08);
}

.node-properties h5,
.edge-properties h5 {
  margin: 0 0 12px 0;
  font-size: 1.1em;
  color: var(--text-primary);
  text-align: center;
  padding-bottom: 10px;
  border-bottom: 1px solid var(--border-color);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  flex-wrap: wrap;
}

.chat-button {
  background: linear-gradient(120deg, var(--accent-primary), var(--accent-secondary));
  color: var(--text-primary);
  border: 2px solid var(--accent-secondary);
  padding: 2px;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 4px;
  transition: all 0.3s ease;
  width: 21%;
  margin: 0;
  box-shadow: 0 2px 8px rgba(212, 165, 116, 0.25);
}

.chat-button svg {
  width: 16px;
  height: 16px;
}

.chat-button:hover {
  background: #e8c9a0;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(212, 165, 116, 0.35);
}

.chat-view {
  height: 600px;
  margin-top: 10px;
}

.category-tag {
  display: inline-block;
  padding: 2px 6px;
  background: #3a84c9; /* 默认颜色，会被动态样式覆盖 */
  border: 1px solid transparent;
  color: var(--text-primary);
  border-radius: 4px;
  font-size: 0.8em;
  margin-left: 8px;
  vertical-align: middle;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.25);
  transition: all 0.2s ease;
}

.no-hover,
.no-properties {
  padding: 20px 0;
  color: var(--text-muted);
  text-align: center;
  font-size: 0.9em;
}

/* --- [修改] 多媒体容器样式 --- */
.media-container {
  display: flex;
  justify-content: center;
  align-items: center;
  /* 确保图片和视频垂直居中对齐 */
  gap: 15px;
  /* 增加图片和视频之间的间距 */
  margin: 10px 0 20px 0;
  padding-bottom: 15px;
  border-bottom: 1px solid var(--border-color);
  flex-wrap: wrap;
  /* 允许按钮组换行到下一行 */
}

.media-item {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.media-item img,
.media-item video {
  display: block;
  border-radius: 4px;
}

.media-nav-btn {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  background: rgba(0, 0, 0, 0.5);
  color: white;
  border: none;
  padding: 5px 8px;
  cursor: pointer;
  border-radius: 50%;
  /* 圆形按钮 */
  font-weight: bold;
  font-size: 1.2em;
  line-height: 1;
  width: 30px;
  height: 30px;
  display: flex;
  justify-content: center;
  align-items: center;
  opacity: 0.8;
  transition: all 0.2s;
  z-index: 10;
}

.media-nav-btn:hover:not(:disabled) {
  opacity: 1;
  background: var(--accent-color);
}

.media-nav-btn:disabled {
  cursor: not-allowed;
  opacity: 0;
}

.prev-btn {
  left: 0px;
  top: 98%;
  height: 15px;
  width: 20px;
  font-size: 14px;

}

.next-btn {
  right: 0px;
  top: 98%;
  height: 15px;
  width: 20px;
  font-size: 14px;
}

.media-counter {
  position: absolute;
  top: 98%;
  /* right: 3px; */
  /* 放在图片/视频内部底部居中 */
  left: 50%;
  transform: translateX(-50%);
  background: rgba(0, 0, 0, 0.6);
  color: white;
  font-size: 11px;
  height: 15px;
  padding: 1px 5px;
  border-radius: 4px;
  min-width: 30px;
  text-align: center;
}

/* --- [新增] 视频切换按钮容器和按钮样式 --- */
.video-button-container {
  /* 确保按钮容器独占一行，位于视频播放器下方 */
  flex-basis: 100%;
  display: flex;
  flex-wrap: wrap;
  /* justify-content: center; */
  justify-content: space-evenly;
  gap: 3px;
  /* 按钮之间的间距 */
  width: 100%;
  margin-top: 0px;
  /* 与视频播放器保持一定距离 */
  max-width: 300px;
  /* 限制宽度以适应侧边栏 */
}

.video-switch-btn {
  /* 基础按钮样式 */
  background-color: var(--bg-primary);
  color: var(--text-secondary);
  border: 1px solid var(--border-color);
  padding: 1px 1px;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 11px;
  max-width: 90px;
  /* 限制按钮最大宽度 */
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  /* 确保标题在一行显示 */
  flex-grow: 1;
  /* 允许按钮增长填充空间 */
  min-width: 70px;
  margin-top: 3px;
}

.video-switch-btn:hover {
  background-color: var(--bg-hover);
  border-color: var(--accent-color);
  color: var(--text-primary);
}

.active-video-btn {
  /* 当前选中视频按钮的突出样式 */
  background-color: var(--accent-color);
  color: white;
  border-color: var(--accent-color);
  font-weight: bold;
  pointer-events: none;
  /* 当前选中按钮禁用点击 */
}

/* --- 视频切换按钮样式 End --- */


/* --- [核心改造] 高级关系路径可视化样式 (保持不变) --- */

/* 关系类型标签 (无修改) */
.relationship-type-badge {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
  padding: 8px 12px;
  background: linear-gradient(120deg, var(--accent-primary), var(--accent-secondary));
  color: var(--text-primary);
  border-radius: 20px;
  font-size: 0.9em;
  font-weight: 500;
  width: fit-content;
  margin-left: auto;
  margin-right: auto;
  box-shadow: 0 4px 12px rgba(212, 165, 116, 0.25);
}

.badge-icon {
  width: 16px;
  height: 16px;
}

.badge-icon svg {
  width: 100%;
  height: 100%;
}

/* 路径容器 (无修改) */
.path-container {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  margin: 20px 0;
  position: relative;
}

/* 实体卡片 (圆形样式) */
.entity-card {
  flex: none;
  width: 100px;
  height: 100px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 8px;
  background: var(--card-bg);
  backdrop-filter: blur(8px);
  border: 2px solid var(--border-color);
  border-radius: 50%;
  transition: all 0.3s ease;
  position: relative;
  box-sizing: border-box;
  box-shadow: 0 0 0 1px rgba(212, 165, 116, 0.15);
}

.entity-card:hover {
  border-color: var(--accent-primary);
  box-shadow: 0 4px 12px rgba(212, 165, 116, 0.25), 0 0 20px rgba(212, 165, 116, 0.2);
  transform: translateY(-2px);
}

.source-card {
  border-left: 4px solid #4CAF50;
}

.target-card {
  border-right: 4px solid #FF9800;
}

.entity-name {
  font-weight: 600;
  color: var(--text-primary);
  font-size: 0.95em;
  line-height: 1.3;
  word-break: break-word;
  overflow-wrap: break-word;
  max-height: 5.2em;
  overflow: hidden;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  text-align: center;
}

/* 连接线可视化 (无修改) */
.connection-visual {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
  position: relative;
}

.connection-line {
  display: flex;
  align-items: center;
  gap: 4px;
  width: 60px;
}

.line-segment {
  height: 3px;
  background: linear-gradient(90deg, var(--accent-primary) 0%, var(--accent-secondary) 100%);
  border-radius: 2px;
  flex: 1;
}

.arrow-head {
  width: 20px;
  height: 20px;
  color: var(--accent-secondary);
  animation: pulse 2s infinite;
}

.arrow-head svg {
  width: 100%;
  height: 100%;
}

@keyframes pulse {

  0%,
  100% {
    opacity: 1;
    transform: scale(1);
  }

  50% {
    opacity: 0.7;
    transform: scale(1.1);
  }
}

/* 其余样式保持不变 */
.properties-list {
  margin-top: 16px;
}

.property-item {
  display: flex;
  padding: 5px 4px;
  transition: background-color 0.2s;
}

.property-key {
  font-weight: 500;
  color: rgba(255, 255, 255, 1);
  min-width: 50px;
  flex-shrink: 0;
  margin-right: 12px;
  font-size: 0.9em;
}

.property-value {
  color: rgba(255, 255, 255, 0.7);
  flex: 1;
  font-size: 0.9em;
  white-space: pre-line;
  word-break: break-word;
}

.property-item.is-supplementary {
  background-color: var(--bg-primary);
}

.property-item.is-supplementary .property-key,
.property-item.is-supplementary .property-value {
  color: var(--text-muted);
  font-size: 0.85em;
}

/* 响应式设计 (无修改) */
@media (max-width: 768px) {
  .path-container {
    flex-direction: column;
    gap: 12px;
  }

  .connection-visual {
    transform: rotate(90deg);
  }
}

/* 使用 :deep() 深度选择器来穿透作用域，修改子组件的样式 */
:deep(.el-tree-node__label) {
  /* 允许文本换行 */
  white-space: normal !important;

  /* 确保文本在容器内自动断行 */
  word-break: break-all;
  font-size: 12px;
  color: var(--text-muted);
}

:deep(.el-tree-node__content) {
  /* 确保父容器的高度能自适应换行后的文本 */
  height: auto;
  min-height: 26px;
  /* 保持最小高度，防止内容过少时收缩 */
  align-items: flex-start;
  /* 保持内容顶部对齐，视觉上更美观 */
}

/* 默认隐藏所有控件 */
video::-webkit-media-controls-enclosure {
  /* 使用 visibility: hidden 隐藏，但保留其在布局中的空间（即它仍在底部） */
  visibility: hidden;
}

/* 鼠标 hover 时显示控件 */
video:hover::-webkit-media-controls-enclosure {
  /* 恢复可见性 */
  visibility: visible;
}
</style>