<template>
  <div class="specimen-library-container">
    <!-- Loading组件 -->
    <div v-if="isLoading" class="loading-overlay">
      <Loading />
    </div>

    <!-- 左侧内容区域 -->
    <div class="main-content" ref="mainContentRef">
      <!-- 返回图谱按钮（相对于滚动容器定位） -->
      <button class="back-to-graph" @click="goBackToGraph">
        <span class="back-text">&lt;&lt;返回图谱</span>
      </button>
      <div class="tab-header">
        <h2 class="tab-title">宝玉石标本库</h2>
        <p class="tab-subtitle">探索世界各地的珍贵宝玉石标本</p>
      </div>
      <div class="minerals-grid">
        <div
          v-for="(mineral, index) in minerals"
          :key="mineral.name"
          class="mineral-item"
          :class="{ 'is-visible': isMineralVisible(mineral.name) }"
          :style="{ '--reveal-index': index }"
          :ref="(el) => registerMineralItem(el, mineral.name)"
        >
          <MineralCard
          :name="mineral.name"
          :type="mineral.type"
          :imageUrl="mineral.imageUrl"
          :color="mineral.color"
          @click="goToMineralDetail(mineral.name)"
        />
        </div>
      </div>
    </div>
    
    <!-- 右侧推荐栏 -->
    <div class="sidebar-content">
      <RecommendationSidebar />
    </div>

    <!-- 可拖拽小恐龙助手 -->
    <Dino class="dino-floating" @navigate-to-ai="handleNavigateToAI" />

    <!-- 回到顶部按钮 -->
    <button 
      class="back-to-top" 
      :class="{ visible: showBackToTop, 'scrolling-down': isScrollingDown }"
      @click="scrollToTop"
      title="回到顶部"
    >
      <img :src="backToTopIcon" alt="回到顶部" class="back-to-top-icon" />
      <span class="tooltip-text">回到顶部</span>
    </button>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, nextTick } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import MineralCard from '../components/MineralCard.vue';
import RecommendationSidebar from '../components/RecommendationSidebar.vue';
import Dino from '../components/Dino.vue';
import Loading from '../components/Loading.vue';
import gemstonesData from '../data/gemstones.json';
import { fetchGemsBatch } from '../api';
import backToTopIcon from '../assets/回到顶部.png';

const route = useRoute();
const router = useRouter();
const libraryType = route.params.type || '宝玉石';
const minerals = ref([]);
const visibleMinerals = ref(new Set());
const isLoading = ref(true);
const showBackToTop = ref(false);
const mainContentRef = ref(null);
const isScrollingDown = ref(false);
let observer = null;
let scrollHandler = null;
let lastScrollTop = 0;
const goBackToGraph = () => router.push('/graph');
const handleNavigateToAI = () => router.push('/qa');

// 从 JSON 数据中提取矿物列表，并对接后端接口获取英文名和图片
async function loadMinerals() {
  try {
    if (!gemstonesData || !Array.isArray(gemstonesData)) {
      minerals.value = [];
      return;
    }

    // 1. 先从本地 JSON 拿到中文名列表
    const baseList = gemstonesData.map((gem) => ({
      name: gem.标本名 || gem.name,
    }));

    const names = baseList.map((g) => g.name);

    // 2. 调用后端批量接口，获取英文名(type)、图片(image_url)、颜色(color)
    let backendMap = new Map();
    try {
      const resp = await fetchGemsBatch(names, ['id', 'name', 'type', 'image_url', 'color']);
      if (resp && resp.code === 200 && Array.isArray(resp.data)) {
        backendMap = new Map(resp.data.map((item) => [item.name, item]));
      }
    } catch (e) {
      console.error('从后端获取宝玉石信息失败，将退回本地占位数据:', e);
    }

    // 3. 合并数据：先不用 cover，用后端/占位图，页面先出来；再异步按需加载 cover 图替换
    minerals.value = baseList.map(({ name }) => {
      const backend = backendMap.get(name);
      return {
        name,
        type: backend?.type || '宝玉石',
        imageUrl: backend?.image_url || getImageUrl(name) || '/specimen-placeholder.svg',
        color: backend?.color || getColorForMineral(name),
      };
    });

    await nextTick();
    isLoading.value = false;

    // 封面图按需加载：从 @src/assets/cover 按中文名匹配，加载完再替换，不阻塞首屏
    baseList.forEach(({ name }, i) => {
      getCoverImageUrl(name).then((url) => {
        if (url && minerals.value[i] && minerals.value[i].name === name) {
          minerals.value[i].imageUrl = url;
        }
      });
    });
  } catch (error) {
    console.error('加载矿物数据失败:', error);
    minerals.value = [];
    isLoading.value = false;
  }
}

// 预加载首屏可见的图片，提升首屏体验
function preloadVisibleImages() {
  const preloadCount = Math.min(8, minerals.value.length);
  for (let i = 0; i < preloadCount; i++) {
    const mineral = minerals.value[i];
    if (mineral && mineral.imageUrl) {
      const img = new Image();
      img.src = mineral.imageUrl;
    }
  }
}

// 滚动到顶部
function scrollToTop() {
  if (mainContentRef.value) {
    mainContentRef.value.scrollTo({
      top: 0,
      behavior: 'smooth'
    });
  }
}

// 处理滚动事件
function handleScroll() {
  if (mainContentRef.value) {
    const scrollTop = mainContentRef.value.scrollTop;
    showBackToTop.value = scrollTop > 300;
    
    // 检测滚动方向，添加动感效果
    if (scrollTop > lastScrollTop && scrollTop > 300) {
      // 向下滚动
      isScrollingDown.value = true;
      setTimeout(() => {
        isScrollingDown.value = false;
      }, 200);
    }
    lastScrollTop = scrollTop;
  }
}

// 封面图：从 @src/assets/cover 按中文名匹配，懒加载（不 eager），切换页面时只载入列表，图片按需加载
const coverModules = import.meta.glob('@/assets/cover/*.{jpg,jpeg,png,webp,gif}');
const coverPathByChineseName = (() => {
  const map = new Map();
  for (const path of Object.keys(coverModules)) {
    const filename = path.replace(/^.*[/\\]/, '').replace(/\.[^.]+$/, '');
    if (filename) map.set(filename, path);
  }
  return map;
})();

async function getCoverImageUrl(chineseName) {
  if (!chineseName) return '';
  const path = coverPathByChineseName.get(chineseName);
  if (!path || typeof coverModules[path] !== 'function') return '';
  try {
    const m = await coverModules[path]();
    return (m && typeof m === 'object' && 'default' in m ? m.default : m) || '';
  } catch {
    return '';
  }
}

// 根据矿物名称获取图片 URL（后端/占位用，封面优先用 cover）
function getImageUrl(name) {
  const nameMap = {
    "红宝石": "ruby",
    "蓝宝石": "sapphire",
    "水晶": "amethyst",
    "长石族宝石": "feldspar",
    "绿柱石族宝石": "beryl",
    "碧玺": "tourmaline",
    "方柱石": "scapolite",
    "橄榄石": "peridot",
    "堇青石": "iolite",
    "坦桑石": "tanzanite",
    "托帕石": "topaz",
    "萤石": "fluorite",
    "尖晶石": "spinel",
    "翡翠": "jadeite",
    "琥珀": "amber",
    "珍珠": "natural pearl",
    "珊瑚": "coral",
    "象牙": "ivory",
    "石榴石": "garnet",
    "矽线石": "sillimanite",
    "磷灰石": "apatite",
    "红柱石": "andalusite",
    "辉石": "pyroxene",
    "金绿宝石": "chrysoberyl",
    "钻石": "diamond",
    "锆石": "zircon",
    "天然玻璃": "natural glass",
    "孔雀石": "malachite",
    "寿山石": "larderite",
    "欧泊": "opal",
    "独山玉": "dushan jade",
    "石英质玉石": "quartzite",
    "绿松石": "turquoise",
    "蔷薇辉石": "rhodonite",
    "蛇纹石玉": "serpentine",
    "软玉": "nephrite",
    "钠长石玉": "albite jade",
    "青田石": "qingtian stone",
    "青金石": "lapis lazuli",
    "鸡血石": "chicken-blood stone",
    "煤精": "jet",
    "硅化木": "petrified wood",
    "贝壳": "shell",
    "龟甲": "tortoise shell"
  };
  
  const enName = nameMap[name] || name.toLowerCase().replace(/\s+/g, '-');
  // 返回占位图片或实际图片路径
  return `/images/${enName}/1.jpg` || '/specimen-placeholder.svg';
}

// 根据矿物名称获取颜色
function getColorForMineral(name) {
  const colorMap = {
    "红宝石": "#FF0090",
    "蓝宝石": "#00B4D8",
    "水晶": "#A855F7",
    "长石族宝石": "#FFD600",
    "绿柱石族宝石": "#10B981",
    "碧玺": "#EC4899",
    "方柱石": "#8B5CF6",
    "橄榄石": "#84CC16",
    "堇青石": "#6366F1",
    "坦桑石": "#3B82F6",
    "托帕石": "#F59E0B",
    "萤石": "#14B8A6",
    "尖晶石": "#EF4444",
    "翡翠": "#10B981",
    "琥珀": "#F97316",
    "珍珠": "#E5E7EB",
    "珊瑚": "#F87171",
    "象牙": "#F3F4F6",
    "石榴石": "#DC2626",
    "钻石": "#E5E7EB"
  };
  return colorMap[name] || "#6200EA";
}

function goToMineralDetail(name) {
  router.push(`/specimen-library/${libraryType}/${name}`);
}

// 注册每个矿物卡片的 DOM，用 IntersectionObserver 监听进入视口
function registerMineralItem(el, name) {
  if (!el) return;

  if (!observer) {
    observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          const itemName = entry.target.dataset.name;
          if (!itemName) return;

          if (entry.isIntersecting) {
            const next = new Set(visibleMinerals.value);
            next.add(itemName);
            visibleMinerals.value = next;
            observer.unobserve(entry.target);
          }
        });
      },
      {
        root: null,
        // 提前一点触发，让元素刚进入视口就开始动画
        threshold: 0.01,
        rootMargin: '0px 0px -15% 0px',
      }
    );
  }

  el.dataset.name = name;
  observer.observe(el);
}

const isMineralVisible = (name) => visibleMinerals.value.has(name);

onMounted(() => {
  loadMinerals();
  
  // 添加滚动监听
  nextTick(() => {
    if (mainContentRef.value) {
      scrollHandler = handleScroll;
      mainContentRef.value.addEventListener('scroll', scrollHandler);
    }
  });
});

onBeforeUnmount(() => {
  if (observer) {
    observer.disconnect();
    observer = null;
  }
  if (mainContentRef.value && scrollHandler) {
    mainContentRef.value.removeEventListener('scroll', scrollHandler);
  }
});
</script>

<style scoped>
.specimen-library-container {
  display: flex;
  width: 100%;
  height: 100vh;
  background: var(--bg-primary);
  color: var(--text-primary);
  overflow: hidden;
}

.main-content {
  flex: 1;
  padding: 40px 60px;
  padding-top: 80px;
  overflow-y: auto;
  scrollbar-width: thin;
  scrollbar-color: rgba(255, 255, 255, 0.2) transparent;
  position: relative;
}

.main-content::-webkit-scrollbar {
  width: 8px;
}

.main-content::-webkit-scrollbar-track {
  background: transparent;
}

.main-content::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.2);
  border-radius: 4px;
}

.main-content::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.3);
}

.tab-header {
  margin-bottom: 40px;
  margin-top:-20px
}

.tab-title {
  font-size: 2.5rem;
  font-weight: 700;
  margin: 0 0 12px 0;
  background: linear-gradient(to right, rgb(45, 212, 191), rgb(168, 85, 247));
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}

.tab-subtitle {
  font-size: 1.1rem;
  color: var(--text-secondary);
  margin: 0;
}

.minerals-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 24px;
}

/* 矿物卡片滚动浮现动画 */
.mineral-item {
  opacity: 0;
  transform: translateY(20px);
  transition:
    opacity 0.45s ease-out,
    transform 0.45s ease-out;
  /* 同一屏内做一个很轻微的错位动画，避免整体太慢 */
  transition-delay: calc(var(--reveal-index, 0) * 30ms);
}

.mineral-item.is-visible {
  opacity: 1;
  transform: translateY(0);
}

.sidebar-content {
  width: 360px;
  padding: 40px 24px;
  background: rgba(30, 41, 59, 0.3);
  backdrop-filter: blur(12px);
  border-left: 1px solid rgba(255, 255, 255, 0.1);
  overflow-y: auto;
  scrollbar-width: thin;
  scrollbar-color: rgba(255, 255, 255, 0.2) transparent;
}

.sidebar-content::-webkit-scrollbar {
  width: 6px;
}

.sidebar-content::-webkit-scrollbar-track {
  background: transparent;
}

.sidebar-content::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.2);
  border-radius: 3px;
}

.dino-floating {
  z-index: 90;
}

.back-to-graph {
  position: absolute;
  top: 24px;
  left: 62px;
  z-index: 140;
  background: transparent;
  border: none;
  cursor: pointer;
  padding: 0;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.back-text {
  color: rgba(0, 255, 136, 0.7);
  font-size: 14px;
  font-weight: 500;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  display: inline-block;
}

.back-to-graph:hover {
  transform: translateX(-4px);
}

.back-to-graph:hover .back-text {
  color: rgba(0, 255, 170, 0.9);
  text-shadow: 0 0 8px rgba(0, 255, 136, 0.5), 0 0 16px rgba(0, 255, 136, 0.3);
  transform: scale(1.05);
}

.back-to-graph:active {
  transform: translateX(-2px);
}

.loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: var(--bg-primary);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 200;
  transition: opacity 0.3s ease;
}

.back-to-top {
  position: fixed;
  right: 370px;
  bottom: 40px;
  width: 43px;
  height: 43px;
  border-radius: 50%;
  background: transparent;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
  opacity: 0;
  transform: translateY(20px) scale(0.8);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  pointer-events: none;
  padding: 0;
}

.back-to-top.visible {
  opacity: 0.7;
  transform: translateY(0) scale(1);
  pointer-events: auto;
}

.back-to-top:hover {
  opacity: 1;
  transform: translateY(-4px) scale(1.05);
}

.back-to-top:active {
  transform: translateY(-2px) scale(1);
}

/* 向下滑动时的动感效果 */
.back-to-top.scrolling-down {
  animation: scrollBounce 0.2s ease-out;
}

@keyframes scrollBounce {
  0% {
    transform: translateY(0) scale(1);
  }
  25% {
    transform: translateY(3px) scale(0.98);
  }
  50% {
    transform: translateY(-2px) scale(1.02);
  }
  75% {
    transform: translateY(1px) scale(0.99);
  }
  100% {
    transform: translateY(0) scale(1);
  }
}

.back-to-top-icon {
  width: 100%;
  height: 100%;
  object-fit: contain;
  transition: transform 0.3s ease;
  filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.3));
}

.back-to-top:hover .back-to-top-icon {
  transform: translateY(-2px);
}

.tooltip-text {
  position: absolute;
  right: 60px;
  background: rgba(0, 0, 0, 0.9);
  color: #ffffff;
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 12px;
  white-space: nowrap;
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.3s ease, transform 0.3s ease;
  transform: translateX(10px);
  backdrop-filter: blur(8px);
}

.back-to-top:hover .tooltip-text {
  opacity: 1;
  transform: translateX(0);
}

.tooltip-text::after {
  content: '';
  position: absolute;
  right: -6px;
  top: 50%;
  transform: translateY(-50%);
  border: 6px solid transparent;
  border-left-color: rgba(0, 0, 0, 0.9);
}
</style>

