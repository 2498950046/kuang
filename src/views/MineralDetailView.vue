<template>
  <transition name="detail-fade">
  <div v-if="showPage" class="container">
    <!-- 左侧 1/3 -->
    <div class="left-container">
      <!-- 返回按钮 -->
      <div class="back-button">
        <button @click="goBack" class="icon-btn">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="20" height="20" fill="currentColor">
            <path d="M15 18l-6-6 6-6" />
          </svg>
          <span>返回</span>
        </button>
      </div>
      <!-- 切换视图按钮 -->
      <div class="toggle-switch">
        <ToggleSwitch v-model="is3D" />
      </div>

      <div class="tab-content">
        <div v-if="is3D">
          <div class="page">
            <MineralViewer 
              :src="modelSrc" 
              :alt="`${mineralName} 3D 模型`" 
              :autoRotate="true" 
              :cameraControls="true"
              :shadowIntensity="1" 
              :exposure="1" 
            />
          </div>
        </div>
        <div v-else>
          <!-- 2D 图像展示区域 -->
          <div class="image-gallery">
            <ImageCarousel
              :images="images"
              :name="mineralName"
              :autoplay="true"
              :interval="3000"
              :loading="imagesLoading"
            />
          </div>
        </div>
      </div>
    </div>

    <!-- 右侧 2/3 -->
    <div class="right-container" v-if="gem">
      <div class="right-grid">
        <!-- 右侧左列 -->
        <div class="right-col left-col">
          <BasicInfoCard :gem="gem" />
        </div>
        <!-- 右侧右列 -->
        <div class="right-col right-col">
          <DescriptionCard :gem="gem" />
          <PropertiesCard :gem="gem" />
        </div>
      </div>
    </div>

    <!-- 可拖拽小恐龙助手 -->
    <Dino class="dino-floating" @navigate-to-ai="handleNavigateToAI" />
  </div>
  </transition>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import ToggleSwitch from '../components/ToggleSwitch.vue';
import MineralViewer from '../components/MineralViewer.vue';
import ImageCarousel from '../components/ImageCarousel.vue';
import BasicInfoCard from '../components/Cards/BasicInfoCard.vue';
import DescriptionCard from '../components/Cards/DescriptionCard.vue';
import PropertiesCard from '../components/Cards/PropertiesCard.vue';
import Dino from '../components/Dino.vue';
import gemstonesData from '../data/gemstones.json';

const route = useRoute();
const router = useRouter();
const mineralName = route.params.name;
const libraryType = route.params.type || '宝玉石';

const is3D = ref(false);
const gem = ref(null);
const images = ref([]);
const imagesLoading = ref(true);
const showPage = ref(false);

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

// 根据中文名获取图片
function getImageUrls(name) {
  const enName = nameMap[name];
  if (!enName) return [];

  // 使用 import.meta.glob 动态加载图片
  // 路径是 /src/assets/images/images/矿物名/
  const modules = import.meta.glob('/src/assets/images/images/**/*.{jpg,png,jpeg,gif}', { eager: true });

  // 过滤出属于该矿物目录的图片
  const imageList = Object.keys(modules)
    .filter(path => {
      // 处理不同的文件夹命名格式，支持大小写不敏感匹配
      const pathLower = path.toLowerCase();
      const enNameLower = enName.toLowerCase();
      // 匹配 /images/images/矿物名/ 或 /images/矿物名/
      return pathLower.includes(`/images/images/${enNameLower}/`) || 
             pathLower.includes(`/images/${enNameLower}/`);
    })
    .map(path => {
      const module = modules[path];
      return module?.default || module;
    })
    .filter(Boolean); // 过滤掉 undefined 或 null

  return imageList;
}

const modelMap = {
  "红宝石": new URL('../assets/ruby.glb', import.meta.url).href,
  "蓝宝石": new URL('../assets/sapphire.glb', import.meta.url).href,
  "翡翠": new URL('../assets/翡翠.glb', import.meta.url).href,
};

const modelSrc = computed(() => modelMap[mineralName] || null);


const handleNavigateToAI = () => router.push('/qa');

function goBack() {
  router.back();
}

onMounted(() => {
  // 先做一个轻微的进入动画
  showPage.value = false;
  requestAnimationFrame(() => {
    showPage.value = true;
  });

  // 从数据中查找对应的矿物
  try {
    if (gemstonesData && Array.isArray(gemstonesData)) {
      const found = gemstonesData.find(g => (g.标本名 || g.name) === mineralName);
      if (found) {
        gem.value = found;
        images.value = getImageUrls(mineralName);
        // 如果图片数组为空，添加占位符
        if (images.value.length === 0) {
          images.value = ['/specimen-placeholder.svg'];
        }
      }
    }
  } catch (error) {
    console.error('加载矿物数据失败:', error);
  } finally {
    imagesLoading.value = false;
  }
});
</script>

<style scoped>
/* 进入/离开过渡动画：轻微上浮 + 淡入 */
.detail-fade-enter-active,
.detail-fade-leave-active {
  transition: opacity 0.35s ease, transform 0.35s ease;
}

.detail-fade-enter-from,
.detail-fade-leave-to {
  opacity: 0;
  transform: translateY(16px);
}

.detail-fade-enter-to,
.detail-fade-leave-from {
  opacity: 1;
  transform: translateY(0);
}

.container {
  display: flex;
  gap: 20px;
  width: 100%;
  height: 100vh;
  box-sizing: border-box;
  overflow: hidden;
  /* background: rgb(14,17,30); */
  color: white;
  padding: 20px 0px 20px 20px; /* 右侧预留空间给小恐龙，避免遮挡文字 */
}

.left-container {
  flex: 1;
  box-sizing: border-box;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  height: 100%;
}

.right-container {
  flex: 2;
  padding: 20px;
  box-sizing: border-box;
  overflow: hidden;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.right-grid {
  display: grid;
  grid-template-columns: 1fr 1.2fr;
  gap: 20px;
  height: 100%;
  flex: 1;
  min-height: 0;
}

.right-col.left-col {
  display: flex;
  justify-content: center;
  height: 100%;
}

.right-col.left-col > * {
  /* width: 100%; */
  overflow: hidden;
}

.right-col.right-col {
  display: flex;
  flex-direction: column;
  gap: 20px;
  overflow-y: auto;
  height: 100%;
}

.right-col.right-col::-webkit-scrollbar {
  width: 8px;
}

.right-col.right-col::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 4px;
}

.right-col.right-col::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.4);
  border-radius: 4px;
}

.right-col.right-col::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.6);
}

.tab-content {
  margin-top: 70px;
  color: white;
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: hidden;
}

.page {
  width: 100%;
  height: 100%;
  flex: 1;
  min-height: 0;
}

.toggle-switch {
  width: 100px;
  margin: 0 auto 20px;
}

.back-button {
  position: relative;
  margin-bottom: 20px;
}

.icon-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  color: #e0e0e0;
  background: linear-gradient(135deg, #1a1a1a, #2c2c2c);
  box-shadow: 0 2px 6px rgba(0,0,0,0.6), inset 0 1px 2px rgba(255,255,255,0.1);
  transition: background 0.3s, transform 0.2s;
}

.icon-btn:hover {
  background: linear-gradient(135deg, #2c2c2c, #3a3a3a);
}

.icon-btn svg {
  fill: #9dd1ff;
}

.icon-btn span {
  font-weight: 500;
  color: #f0f0f0;
}

.image-gallery {
  flex: 1;
  width: 100%;
  height: 100%;
  min-height: 400px;
  display: flex;
  overflow: hidden;
}

.dino-floating {
  z-index: 90;
}
</style>

