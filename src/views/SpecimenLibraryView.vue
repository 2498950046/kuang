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
        <p class="tab-subtitle">探索世界各地的珍贵宝玉石标本与市场动态</p>
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

      <div v-show="activeTab === 'commodity'" class="commodity-tab-container">
        
        <div v-if="!showCommodityDetail" class="commodity-mall-grid">
          <div
            v-for="(cmd, index) in shuffledCommodities"
            :key="index"
            class="mall-card-wrapper is-visible"
            :style="{ '--reveal-index': index % 15 }"
            @click="goToCommodityDetail(cmd)"
          >
            <div class="mall-card">
              <div class="mall-img" :style="{ backgroundImage: `url(${cmd.img})` }"></div>
              <div class="mall-info">
                <p class="mall-title" :title="cmd.t">{{ cmd.t }}</p>
                <div class="mall-price-row">
                  <p class="mall-price"><span class="currency">¥</span> {{ cmd.p.toLocaleString() }}</p>
                  <span class="mall-gem-tag">{{ cmd.gemName }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div v-else class="commodity-detail-view">
          <button class="back-to-home-btn" @click="showCommodityDetail = false">
            <span class="back-icon">←</span> 返回商城主页
          </button>
          
          <div class="commodity-dashboard-wrapper">
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

            <div class="child-component-box">
              <CommodityDashboard :gemData="selectedCommodity" />
            </div>
          </div>
        </div>

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

// === 🌟 行情与展示 状态管理 ===
const activeTab = ref('specimen'); 
const selectedCommodity = ref(null);
const showCommodityDetail = ref(false); 

// --- 把你子组件里的数据字典提出来，用于在父页面生成商城卡片 ---
const getImg = (keyword) => `https://tse1.mm.bing.net/th?q=${encodeURIComponent(keyword)}&w=400&h=400&c=7&rs=1`;
const marketDataDB = {
  '红宝石': { items: [{t: '1.02克拉 鸽血红 无烧裸石 (GRS)', p: 52000, img: getImg('鸽血红 红宝石 裸石')}, {t: '18K白金豪华群镶 红宝石女戒', p: 98000, img: getImg('红宝石 戒指 珠宝')}, {t: '复古宫廷风 鸽血红锁骨链', p: 26500, img: getImg('红宝石 项链 高清')}] },
  '蓝宝石': { items: [{t: '2.05克拉 皇家蓝 无烧蓝宝石', p: 48000, img: getImg('皇家蓝 蓝宝石 裸石')}, {t: '18K金 戴妃款 矢车菊钻戒', p: 35000, img: getImg('蓝宝石 戴妃 戒指')}, {t: '斯里兰卡 蓝宝石 豪华项链', p: 88000, img: getImg('蓝宝石 吊坠 项链')}] },
  '钻石': { items: [{t: '1.0克拉 D色 VVS1 3EX 裸钻', p: 56000, img: getImg('钻石 裸钻 GIA')}, {t: 'PT950铂金 经典六爪 50分钻戒', p: 16800, img: getImg('六爪 钻戒 求婚')}, {t: '阿盖尔 粉钻 18K金 群镶戒指', p: 188000, img: getImg('粉钻 戒指 珠宝')}] },
  '金绿宝石': { items: [{t: '亚历山大变石 强变色 顶级裸石', p: 88000, img: getImg('亚历山大变石 裸石')}, {t: '金绿猫眼 锐利活光 18K金男戒', p: 125000, img: getImg('金绿猫眼 戒指')}, {t: '变石 刻面 钻石群镶吊坠', p: 45000, img: getImg('变石 吊坠 项链')}] },
  '绿柱石族宝石': { items: [{t: '赞比亚 木木绿 祖母绿裸石', p: 58000, img: getImg('祖母绿 裸石 高清')}, {t: '圣玛利亚色 海蓝宝 满钻女戒', p: 16800, img: getImg('海蓝宝 戒指')}, {t: '天然摩根石 粉色系 原矿', p: 8500, img: getImg('摩根石 吊坠')}] },
  '碧玺': { items: [{t: '卢比来 极品红碧玺 鸽血红 裸石', p: 18500, img: getImg('红碧玺 裸石')}, {t: '巴西天然 西瓜碧玺 雕花挂件', p: 9800, img: getImg('西瓜碧玺 吊坠')}, {t: '帕拉伊巴 霓虹蓝 18K金戒指', p: 128000, img: getImg('帕拉伊巴 戒指')}] },
  '坦桑石': { items: [{t: '5A级 皇家蓝 坦桑石裸石', p: 18500, img: getImg('坦桑石 裸石')}, {t: '18K白金 坦桑石伴钻女戒', p: 28900, img: getImg('坦桑石 戒指')}, {t: '水滴形 坦桑石 钻石群镶项链', p: 46800, img: getImg('坦桑石 项链')}] },
  '尖晶石': { items: [{t: '绝地武士 霓虹粉红 尖晶石裸石', p: 38000, img: getImg('尖晶石 裸石')}, {t: '马亨盖 鲜艳热粉色 18K金钻戒', p: 25000, img: getImg('马亨盖 戒指')}, {t: '坦桑尼亚 天然钴蓝尖晶 吊坠', p: 18000, img: getImg('钴蓝尖晶石 吊坠')}] },
  '石榴石': { items: [{t: '翠榴石 强火彩 马尾包体 裸石', p: 15000, img: getImg('翠榴石 裸石')}, {t: '沙弗莱 浓艳翠绿 豪华女戒', p: 22000, img: getImg('沙弗莱 戒指')}, {t: '紫牙乌 极品紫红 多圈手链', p: 3500, img: getImg('紫牙乌 手链')}] },
  '托帕石': { items: [{t: '伦敦蓝 托帕石 10克拉全净裸石', p: 2500, img: getImg('伦敦蓝托帕石 裸石')}, {t: '瑞士蓝 18K金 海蓝之心 戒指', p: 4800, img: getImg('托帕石 戒指')}, {t: '帝国托帕石 金黄色 珍藏级标本', p: 12000, img: getImg('帝国托帕石 裸石')}] },
  '翡翠': { items: [{t: '老坑玻璃种 帝王绿 平安扣', p: 450000, img: getImg('帝王绿 翡翠 吊坠')}, {t: '高冰飘绿花 完美无纹裂 手镯', p: 280000, img: getImg('冰种 翡翠 手镯')}, {t: '木那雪花棉 18K金镶钻 福豆', p: 88000, img: getImg('雪花棉 翡翠 吊坠')}] },
  '软玉': { items: [{t: '新疆和田玉 籽料 羊脂白玉 把件', p: 280000, img: getImg('羊脂白玉 籽料')}, {t: '且末蓝 糖料 俄碧玉 无事牌', p: 35000, img: getImg('和田玉 碧玉 吊坠')}, {t: '老坑 塔青 细料无结构 手串', p: 12800, img: getImg('和田玉 塔青 手串')}] },
  '绿松石': { items: [{t: '原矿高瓷 丫角山 果冻蓝 108佛珠', p: 88000, img: getImg('绿松石 108 佛珠')}, {t: '顶级 乌兰花 铁线蜘蛛网 戒指', p: 15000, img: getImg('绿松石 乌兰花 戒指')}, {t: '睡美人 无铁线 纯净天空蓝 吊坠', p: 22000, img: getImg('绿松石 吊坠')}] },
  '珍珠': { items: [{t: '澳洲白珠 15mm 极光冷白', p: 12800, img: getImg('澳白 珍珠 项链')}, {t: '大溪地 天然孔雀绿 黑珍珠', p: 8600, img: getImg('大溪地 黑珍珠 戒指')}, {t: '日本Akoya 天女级 塔链', p: 28000, img: getImg('Akoya 天女 珍珠')}] }
};

const shuffledCommodities = ref([]);    

// 将所有商品拍平并打乱
const shuffleCommodities = () => {
  const allItems = [];
  Object.keys(marketDataDB).forEach(gemName => {
    marketDataDB[gemName].items.forEach(item => {
      allItems.push({ ...item, gemName });
    });
  });

  for (let i = allItems.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [allItems[i], allItems[j]] = [allItems[j], allItems[i]];
  }
  shuffledCommodities.value = allItems;
};

// 点击商品卡片 -> 匹配左侧菜单 -> 打开折线图页面
const goToCommodityDetail = (cmd) => {
  const targetMineral = minerals.value.find(m => m.name === cmd.gemName);
  selectedCommodity.value = targetMineral || { name: cmd.gemName };
  showCommodityDetail.value = true;
};

// 切换顶部的 大Tab
const switchTab = (tab) => {
  activeTab.value = tab;
  if (tab === 'commodity') {
    showCommodityDetail.value = false; 
    shuffleCommodities(); // 每次进入市场行情重新洗牌
  }
};
// =============================

let observer = null;
let scrollHandler = null;
let lastScrollTop = 0;
const goBackToGraph = () => router.push('/graph');
const handleNavigateToAI = () => router.push('/qa');

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

    shuffleCommodities();

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
.main-content { flex: 1; padding: 40px 60px; padding-top: 80px; overflow-y: auto; scrollbar-width: thin; scrollbar-color: rgba(255, 255, 255, 0.2) transparent; position: relative; display: flex; flex-direction: column; }
.main-content::-webkit-scrollbar { width: 8px; }
.main-content::-webkit-scrollbar-track { background: transparent; }
.main-content::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.2); border-radius: 4px; }
.main-content::-webkit-scrollbar-thumb:hover { background: rgba(255, 255, 255, 0.3); }

.tab-header { margin-bottom: 20px; margin-top:-20px; flex-shrink: 0; }
.tab-title {
  font-size: 2.5rem; font-weight: 700; margin: 0 0 12px 0;
  background: linear-gradient(to right, rgb(45, 212, 191), rgb(168, 85, 247));
  -webkit-background-clip: text; background-clip: text; color: transparent;
}
.tab-subtitle { font-size: 1.1rem; color: var(--text-secondary); margin: 0; }

.toggle-wrapper { margin-bottom: 30px; display: flex; justify-content: flex-start; flex-shrink: 0; }
.custom-toggle {
  display: flex; position: relative; width: 260px; height: 44px;
  background: rgba(30, 41, 59, 0.5); border-radius: 22px; padding: 4px;
  border: 1px solid rgba(255, 255, 255, 0.1); box-shadow: inset 0 2px 4px rgba(0,0,0,0.2);
}
.toggle-bg {
  position: absolute; top: 4px; left: 4px; width: calc(50% - 4px); height: 34px; border-radius: 18px;
  transition: transform 0.4s cubic-bezier(0.4, 0, 0.2, 1), background 0.4s ease;
}
.custom-toggle.specimen .toggle-bg { background: linear-gradient(to right, #0ea5e9, #8b5cf6); transform: translateX(0); }
.custom-toggle.commodity .toggle-bg { background: linear-gradient(to right, #f59e0b, #ef4444); transform: translateX(100%); }

.toggle-option {
  flex: 1; display: flex; align-items: center; justify-content: center; gap: 8px;
  position: relative; z-index: 1; font-size: 14px; font-weight: 600; color: #94a3b8;
  cursor: pointer; transition: color 0.3s ease;
}
.toggle-option.active { color: #ffffff; }
.dash { width: 12px; height: 3px; border-radius: 2px; background-color: currentColor; opacity: 0.5; transition: opacity 0.3s ease; }
.toggle-option.active .dash { opacity: 1; }

.minerals-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 24px; padding-bottom: 40px; }
.mineral-item { opacity: 0; transform: translateY(20px); transition: opacity 0.45s ease-out, transform 0.45s ease-out; transition-delay: calc(var(--reveal-index, 0) * 30ms); }
.mineral-item.is-visible { opacity: 1; transform: translateY(0); }

/* ========================================== */
/* 🌟 淘宝商城瀑布流主页                     */
/* ========================================== */
.commodity-tab-container {
  display: flex;
  flex-direction: column;
  flex: 1; 
  min-height: 0; /* 关键：防止 flex 子项溢出 */
}
.commodity-mall-grid {
  display: grid; 
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr)); 
  gap: 24px; 
  padding-bottom: 40px;
}
.mall-card-wrapper {
  opacity: 0; transform: translateY(20px); 
  transition: opacity 0.4s ease, transform 0.4s ease;
  transition-delay: calc(var(--reveal-index, 0) * 20ms); 
}
.mall-card-wrapper.is-visible {
  opacity: 1; transform: translateY(0);
}

.mall-card {
  background: rgba(30, 41, 59, 0.4);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  flex-direction: column;
  height: 100%;
}
.mall-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 15px 30px rgba(0,0,0,0.5);
  border-color: rgba(245, 158, 11, 0.5);
}

.mall-img {
  width: 100%;
  height: 220px;
  background-size: cover;
  background-position: center;
  transition: transform 0.5s ease;
}
.mall-card:hover .mall-img {
  transform: scale(1.05);
}

.mall-info {
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  flex: 1;
  background: rgba(15, 23, 42, 0.8); /* 盖在图片下面，防遮挡 */
  z-index: 2;
}
.mall-title {
  margin: 0;
  font-size: 15px;
  color: #f1f5f9;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  font-weight: 500;
}
.mall-price-row {
  margin-top: auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.mall-price {
  margin: 0;
  color: #fb7185; /* 明艳的红色 */
  font-size: 20px;
  font-weight: 800;
  font-family: 'Courier New', Courier, monospace;
}
.mall-price .currency {
  font-size: 14px;
}
.mall-gem-tag {
  font-size: 11px;
  color: #94a3b8;
  background: rgba(255,255,255,0.1);
  padding: 2px 8px;
  border-radius: 4px;
}

/* ========================================== */
/* 🌟 行情折线图详情页（高度彻底修复！）       */
/* ========================================== */
.commodity-detail-view {
  display: flex;
  flex-direction: column;
  flex: 1;
  animation: fadeIn 0.3s ease-out;
  min-height: 0; /* 关键 */
}
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.back-to-home-btn {
  align-self: flex-start;
  background: rgba(30, 41, 59, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: #e2e8f0;
  padding: 8px 16px;
  border-radius: 8px;
  cursor: pointer;
  margin-bottom: 20px;
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.2s ease;
  flex-shrink: 0;
}
.back-to-home-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
  border-color: rgba(245, 158, 11, 0.4);
  transform: translateX(-2px);
}
.back-icon { font-size: 16px; }

/* 🔥 这个 wrapper 的高度是修复图表的绝对关键 🔥 */
.commodity-dashboard-wrapper {
  display: flex; 
  gap: 30px; 
  flex: 1; /* 撑满剩余高度 */
  height: calc(100vh - 250px); /* 强制限定最大高度 */
  min-height: 600px;
  background: rgba(15, 23, 42, 0.4); 
  border-radius: 16px; 
  border: 1px solid rgba(255, 255, 255, 0.05); 
  padding: 20px;
  overflow: hidden;
}

.gem-selector { 
  width: 220px; 
  background: rgba(255, 255, 255, 0.02); 
  border-radius: 12px; 
  overflow-y: auto; 
  padding: 10px; 
  flex-shrink: 0;
}
.gem-selector::-webkit-scrollbar { width: 4px; }
.gem-selector::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.1); border-radius: 2px; }

.selector-item {
  display: flex; align-items: center; gap: 12px; padding: 12px 16px; margin-bottom: 8px;
  border-radius: 8px; cursor: pointer; color: #cbd5e1; transition: all 0.2s ease;
}
.selector-item:hover { background: rgba(255, 255, 255, 0.05); }
.selector-item.active { background: rgba(255, 255, 255, 0.1); color: #fff; font-weight: bold; }
.color-dot { width: 10px; height: 10px; border-radius: 50%; box-shadow: 0 0 8px currentColor; }

/* 限制子组件占满右侧，不溢出 */
.child-component-box {
  flex: 1;
  min-width: 0;
  height: 100%;
  position: relative;
}

/* ========================================== */
/* 原有基础辅助样式                           */
/* ========================================== */
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