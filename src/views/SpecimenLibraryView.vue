<template>
  <div class="specimen-library-container">
    <div v-if="isLoading" class="loading-overlay">
      <Loading />
    </div>

    <div class="main-content" ref="mainContentRef">
      <button class="back-to-graph" @click="goBackToGraph">
        <span class="back-text">&lt;&lt;返回图谱</span>
      </button>

      <div class="tab-header">
        <h2 class="tab-title">宝玉石标本库</h2>
        <p class="tab-subtitle">探索世界各地的珍贵宝玉石标本</p>
      </div>

      <div class="toggle-wrapper">
        <div class="custom-toggle" :class="activeTab">
          <div class="toggle-bg"></div>
          <div class="toggle-option" @click="switchTab('specimen')" :class="{ active: activeTab === 'specimen' }">
            <span class="dash"></span> 标本展示
          </div>
          <div class="toggle-option" @click="switchTab('commodity')" :class="{ active: activeTab === 'commodity' }">
            <span class="dash"></span> 市场行情
          </div>
        </div>
      </div>

      <div v-show="activeTab === 'specimen'" class="minerals-grid">
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

      <div v-show="activeTab === 'commodity'" class="commodity-dashboard">
        <div class="gem-selector">
          <div 
            v-for="mineral in minerals" 
            :key="'cmd-' + mineral.name"
            class="selector-item"
            :class="{ active: selectedCommodity?.name === mineral.name }"
            @click="selectedCommodity = mineral"
          >
            <div class="color-dot" :style="{ backgroundColor: mineral.color }"></div>
            <span>{{ mineral.name }}</span>
          </div>
        </div>

        <CommodityDashboard :gemData="selectedCommodity" />
      </div>

    </div>
    
    <div class="sidebar-content">
      <RecommendationSidebar />
    </div>

    <Dino class="dino-floating" @navigate-to-ai="handleNavigateToAI" />

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
// 🌟 引入刚抽离的子组件
import CommodityDashboard from '../components/shangpin/CommodityDashboard.vue'; 
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

// === 🌟 新增：切换状态管理 ===
const activeTab = ref('specimen'); // 'specimen' 标本 | 'commodity' 商品
const selectedCommodity = ref(null);

const switchTab = (tab) => {
  activeTab.value = tab;
  // 首次切换到商品页时，默认选中列表里的第一个宝石
  if (tab === 'commodity' && !selectedCommodity.value && minerals.value.length > 0) {
    selectedCommodity.value = minerals.value[0];
  }
};
// =============================

let observer = null;
let scrollHandler = null;
let lastScrollTop = 0;
const goBackToGraph = () => router.push('/graph');
const handleNavigateToAI = () => router.push('/qa');

// 从 JSON 数据中提取矿物列表...
async function loadMinerals() {
  try {
    if (!gemstonesData || !Array.isArray(gemstonesData)) {
      minerals.value = [];
      return;
    }
    const baseList = gemstonesData.map((gem) => ({ name: gem.标本名 || gem.name }));
    const names = baseList.map((g) => g.name);

    let backendMap = new Map();
    try {
      const resp = await fetchGemsBatch(names, ['id', 'name', 'type', 'image_url', 'color']);
      if (resp && resp.code === 200 && Array.isArray(resp.data)) {
        backendMap = new Map(resp.data.map((item) => [item.name, item]));
      }
    } catch (e) {
      console.error('获取信息失败:', e);
    }

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

    baseList.forEach(({ name }, i) => {
      getCoverImageUrl(name).then((url) => {
        if (url && minerals.value[i] && minerals.value[i].name === name) {
          minerals.value[i].imageUrl = url;
        }
      });
    });
  } catch (error) {
    minerals.value = [];
    isLoading.value = false;
  }
}

// 预加载首屏可见的图片...
function preloadVisibleImages() {
  const preloadCount = Math.min(8, minerals.value.length);
  for (let i = 0; i < preloadCount; i++) {
    if (minerals.value[i]?.imageUrl) {
      const img = new Image();
      img.src = minerals.value[i].imageUrl;
    }
  }
}

function scrollToTop() {
  if (mainContentRef.value) mainContentRef.value.scrollTo({ top: 0, behavior: 'smooth' });
}

function handleScroll() {
  if (mainContentRef.value) {
    const scrollTop = mainContentRef.value.scrollTop;
    showBackToTop.value = scrollTop > 300;
    if (scrollTop > lastScrollTop && scrollTop > 300) {
      isScrollingDown.value = true;
      setTimeout(() => isScrollingDown.value = false, 200);
    }
    lastScrollTop = scrollTop;
  }
}

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
  } catch { return ''; }
}

function getImageUrl(name) {
  const nameMap = { "红宝石": "ruby", "蓝宝石": "sapphire", "钻石": "diamond" };
  const enName = nameMap[name] || name.toLowerCase().replace(/\s+/g, '-');
  return `/images/${enName}/1.jpg` || '/specimen-placeholder.svg';
}

function getColorForMineral(name) {
  const colorMap = { "红宝石": "#FF0090", "蓝宝石": "#00B4D8", "钻石": "#E5E7EB" };
  return colorMap[name] || "#6200EA";
}

function goToMineralDetail(name) {
  router.push(`/specimen-library/${libraryType}/${name}`);
}

function registerMineralItem(el, name) {
  if (!el) return;
  if (!observer) {
    observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            visibleMinerals.value = new Set(visibleMinerals.value).add(entry.target.dataset.name);
            observer.unobserve(entry.target);
          }
        });
      },
      { root: null, threshold: 0.01, rootMargin: '0px 0px -15% 0px' }
    );
  }
  el.dataset.name = name;
  observer.observe(el);
}

const isMineralVisible = (name) => visibleMinerals.value.has(name);

onMounted(() => {
  loadMinerals();
  nextTick(() => {
    if (mainContentRef.value) {
      scrollHandler = handleScroll;
      mainContentRef.value.addEventListener('scroll', scrollHandler);
    }
  });
});

onBeforeUnmount(() => {
  if (observer) { observer.disconnect(); observer = null; }
  if (mainContentRef.value && scrollHandler) {
    mainContentRef.value.removeEventListener('scroll', scrollHandler);
  }
});
</script>

<style scoped>
/* 基础布局样式 */
.specimen-library-container { display: flex; width: 100%; height: 100vh; background: var(--bg-primary); color: var(--text-primary); overflow: hidden; }
.main-content { flex: 1; padding: 40px 60px; padding-top: 80px; overflow-y: auto; scrollbar-width: thin; scrollbar-color: rgba(255, 255, 255, 0.2) transparent; position: relative; }
.main-content::-webkit-scrollbar { width: 8px; }
.main-content::-webkit-scrollbar-track { background: transparent; }
.main-content::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.2); border-radius: 4px; }
.main-content::-webkit-scrollbar-thumb:hover { background: rgba(255, 255, 255, 0.3); }

.tab-header { margin-bottom: 20px; margin-top:-20px }
.tab-title {
  font-size: 2.5rem; font-weight: 700; margin: 0 0 12px 0;
  background: linear-gradient(to right, rgb(45, 212, 191), rgb(168, 85, 247));
  -webkit-background-clip: text; background-clip: text; color: transparent;
}
.tab-subtitle { font-size: 1.1rem; color: var(--text-secondary); margin: 0; }

/* === 🌟 新增：带短横线滑块样式 === */
.toggle-wrapper {
  margin-bottom: 30px;
  display: flex;
  justify-content: flex-start;
}
.custom-toggle {
  display: flex; position: relative; width: 260px; height: 44px;
  background: rgba(30, 41, 59, 0.5); border-radius: 22px; padding: 4px;
  border: 1px solid rgba(255, 255, 255, 0.1); box-shadow: inset 0 2px 4px rgba(0,0,0,0.2);
}
.toggle-bg {
  position: absolute; top: 4px; left: 4px; width: calc(50% - 4px); height: 34px; border-radius: 18px;
  transition: transform 0.4s cubic-bezier(0.4, 0, 0.2, 1), background 0.4s ease;
}
/* 标本状态：冷色调 */
.custom-toggle.specimen .toggle-bg { background: linear-gradient(to right, #0ea5e9, #8b5cf6); transform: translateX(0); }
/* 商品状态：暖色调 */
.custom-toggle.commodity .toggle-bg { background: linear-gradient(to right, #f59e0b, #ef4444); transform: translateX(100%); }

.toggle-option {
  flex: 1; display: flex; align-items: center; justify-content: center; gap: 8px;
  position: relative; z-index: 1; font-size: 14px; font-weight: 600; color: #94a3b8;
  cursor: pointer; transition: color 0.3s ease;
}
.toggle-option.active { color: #ffffff; }
.dash { width: 12px; height: 3px; border-radius: 2px; background-color: currentColor; opacity: 0.5; transition: opacity 0.3s ease; }
.toggle-option.active .dash { opacity: 1; }

/* === 🌟 新增：商品看板布局样式 === */
.commodity-dashboard {
  display: flex; gap: 30px; height: calc(100% - 150px); min-height: 800px;
  background: rgba(15, 23, 42, 0.4); border-radius: 16px; border: 1px solid rgba(255, 255, 255, 0.05); padding: 20px;
}
.gem-selector { width: 220px; background: rgba(255, 255, 255, 0.02); border-radius: 12px; overflow-y: auto; padding: 10px; }
.gem-selector::-webkit-scrollbar { width: 4px; }
.gem-selector::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.1); border-radius: 2px; }
.selector-item {
  display: flex; align-items: center; gap: 12px; padding: 12px 16px; margin-bottom: 8px;
  border-radius: 8px; cursor: pointer; color: #cbd5e1; transition: all 0.2s ease;
}
.selector-item:hover { background: rgba(255, 255, 255, 0.05); }
.selector-item.active { background: rgba(255, 255, 255, 0.1); color: #fff; font-weight: bold; }
.color-dot { width: 10px; height: 10px; border-radius: 50%; box-shadow: 0 0 8px currentColor; }

/* 原有组件样式 */
.minerals-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 24px; }
.mineral-item { opacity: 0; transform: translateY(20px); transition: opacity 0.45s ease-out, transform 0.45s ease-out; transition-delay: calc(var(--reveal-index, 0) * 30ms); }
.mineral-item.is-visible { opacity: 1; transform: translateY(0); }

/* 侧边栏及按钮辅助样式 */
.sidebar-content { width: 360px; padding: 40px 24px; background: rgba(30, 41, 59, 0.3); backdrop-filter: blur(12px); border-left: 1px solid rgba(255, 255, 255, 0.1); overflow-y: auto; scrollbar-width: thin; scrollbar-color: rgba(255, 255, 255, 0.2) transparent; }
.sidebar-content::-webkit-scrollbar { width: 6px; }
.sidebar-content::-webkit-scrollbar-track { background: transparent; }
.sidebar-content::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.2); border-radius: 3px; }
.dino-floating { z-index: 90; }
.back-to-graph { position: absolute; top: 24px; left: 62px; z-index: 140; background: transparent; border: none; cursor: pointer; padding: 0; transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); }
.back-text { color: rgba(0, 255, 136, 0.7); font-size: 14px; font-weight: 500; transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); display: inline-block; }
.back-to-graph:hover { transform: translateX(-4px); }
.back-to-graph:hover .back-text { color: rgba(0, 255, 170, 0.9); text-shadow: 0 0 8px rgba(0, 255, 136, 0.5), 0 0 16px rgba(0, 255, 136, 0.3); transform: scale(1.05); }
.back-to-graph:active { transform: translateX(-2px); }
.loading-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: var(--bg-primary); display: flex; align-items: center; justify-content: center; z-index: 200; transition: opacity 0.3s ease; }
.back-to-top { position: fixed; right: 370px; bottom: 40px; width: 43px; height: 43px; border-radius: 50%; background: transparent; border: none; cursor: pointer; display: flex; align-items: center; justify-content: center; z-index: 100; opacity: 0; transform: translateY(20px) scale(0.8); transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1); pointer-events: none; padding: 0; }
.back-to-top.visible { opacity: 0.7; transform: translateY(0) scale(1); pointer-events: auto; }
.back-to-top:hover { opacity: 1; transform: translateY(-4px) scale(1.05); }
.back-to-top:active { transform: translateY(-2px) scale(1); }
.back-to-top.scrolling-down { animation: scrollBounce 0.2s ease-out; }
@keyframes scrollBounce { 0% { transform: translateY(0) scale(1); } 25% { transform: translateY(3px) scale(0.98); } 50% { transform: translateY(-2px) scale(1.02); } 75% { transform: translateY(1px) scale(0.99); } 100% { transform: translateY(0) scale(1); } }
.back-to-top-icon { width: 100%; height: 100%; object-fit: contain; transition: transform 0.3s ease; filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.3)); }
.back-to-top:hover .back-to-top-icon { transform: translateY(-2px); }
.tooltip-text { position: absolute; right: 60px; background: rgba(0, 0, 0, 0.9); color: #ffffff; padding: 8px 12px; border-radius: 6px; font-size: 12px; white-space: nowrap; opacity: 0; pointer-events: none; transition: opacity 0.3s ease, transform 0.3s ease; transform: translateX(10px); backdrop-filter: blur(8px); }
.back-to-top:hover .tooltip-text { opacity: 1; transform: translateX(0); }
.tooltip-text::after { content: ''; position: absolute; right: -6px; top: 50%; transform: translateY(-50%); border: 6px solid transparent; border-left-color: rgba(0, 0, 0, 0.9); }
</style>