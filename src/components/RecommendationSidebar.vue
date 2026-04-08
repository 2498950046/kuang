<template>
  <div class="sidebar-container">
    <!-- Recommended Section -->
    <div class="section">
      <div class="section-header">
        <svg class="header-icon sparkles" xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M9.937 15.5A2 2 0 0 0 8.5 14.063l-6.135-1.582a.5.5 0 0 1 0-.962L8.5 9.936A2 2 0 0 0 9.937 8.5l1.582-6.135a.5.5 0 0 1 .963 0L14.063 8.5A2 2 0 0 0 15.5 9.937l6.135 1.582a.5.5 0 0 1 0 .963L15.5 14.063a2 2 0 0 0-1.437 1.437l-1.582 6.135a.5.5 0 0 1-.963 0z"/>
        </svg>
        <h3 class="section-title">精选推荐</h3>
      </div>
      <div class="recommendations-list">
        <div
          v-for="(item, index) in recommendations"
          :key="item.title"
          class="recommendation-item"
          :style="{ 
            animationDelay: `${index * 0.1}s`,
            '--item-color': item.color 
          }"
          @click="goToDetail(item)"
        >
          <div class="item-content">
            <div class="icon-wrapper">
              <component :is="getIconComponent(item.icon)" />
            </div>
            <div class="item-text">
              <h4 class="item-title">{{ item.title }}</h4>
              <p class="item-description">{{ item.description }}</p>
            </div>
          </div>
          <div class="hover-indicator" />
        </div>
      </div>
    </div>

    <!-- Latest Discoveries -->
    <div class="section">
      <div class="section-header">
        <svg class="header-icon trending" xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/>
          <polyline points="16 7 22 7 22 13"/>
        </svg>
        <h3 class="section-title">最新发现</h3>
      </div>
      <div class="discoveries-box">
        <div class="discoveries-list">
          <div
            v-for="(item, index) in latestDiscoveries"
            :key="item"
            class="discovery-item"
            :style="{ animationDelay: `${0.5 + index * 0.1}s` }"
          >
            <div class="discovery-dot" />
            <span class="discovery-text">{{ item }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Stats -->
    <div class="stats-section">
      <div class="stats-box">
        <div class="stats-grid">
          <div
            v-for="(stat, index) in stats"
            :key="stat.label"
            class="stat-item"
            :style="{ animationDelay: `${0.8 + index * 0.1}s` }"
          >
            <div class="stat-value">{{ stat.value }}</div>
            <div class="stat-label">{{ stat.label }}</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { h, onMounted, ref } from 'vue';
import { useRouter } from 'vue-router';

const StarIcon = () => h('svg', {
  xmlns: "http://www.w3.org/2000/svg",
  width: "16",
  height: "16",
  viewBox: "0 0 24 24",
  fill: "none",
  stroke: "currentColor",
  'stroke-width': "2",
  'stroke-linecap': "round",
  'stroke-linejoin': "round"
}, [
  h('polygon', { points: "12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2" })
]);

const SparklesIcon = () => h('svg', {
  xmlns: "http://www.w3.org/2000/svg",
  width: "16",
  height: "16",
  viewBox: "0 0 24 24",
  fill: "none",
  stroke: "currentColor",
  'stroke-width': "2",
  'stroke-linecap': "round",
  'stroke-linejoin': "round"
}, [
  h('path', { d: "M9.937 15.5A2 2 0 0 0 8.5 14.063l-6.135-1.582a.5.5 0 0 1 0-.962L8.5 9.936A2 2 0 0 0 9.937 8.5l1.582-6.135a.5.5 0 0 1 .963 0L14.063 8.5A2 2 0 0 0 15.5 9.937l6.135 1.582a.5.5 0 0 1 0 .963L15.5 14.063a2 2 0 0 0-1.437 1.437l-1.582 6.135a.5.5 0 0 1-.963 0z" })
]);

const TrendingUpIcon = () => h('svg', {
  xmlns: "http://www.w3.org/2000/svg",
  width: "16",
  height: "16",
  viewBox: "0 0 24 24",
  fill: "none",
  stroke: "currentColor",
  'stroke-width': "2",
  'stroke-linecap': "round",
  'stroke-linejoin': "round"
}, [
  h('polyline', { points: "22 7 13.5 15.5 8.5 10.5 2 17" }),
  h('polyline', { points: "16 7 22 7 22 13" })
]);

// 使用已接入 3D 模型的三种宝石：红宝石、蓝宝石、翡翠
const recommendations = [
  {
    title: "红宝石",
    description: "炽热红色宝石，象征热情与爱情之石",
    icon: "star",
    color: "#f97373",
    type: "宝玉石"
  },
  {
    title: "蓝宝石",
    description: "高贵深蓝宝石，被视为忠诚与智慧的象征",
    icon: "sparkles",
    color: "#3b82f6",
    type: "宝玉石"
  },
  {
    title: "翡翠",
    description: "东方传统珍贵玉石，以浓翠色与优雅水头著称",
    icon: "trending",
    color: "#22c55e",
    type: "宝玉石"
  }
];

const latestDiscoveries = [
  "稀土矿物新品种",
  "火星陨石样本",
  "深海矿物晶体",
  "新型超导材料",
  "极地冰川矿物"
];

const stats = ref([
  { label: "矿物种类", value: "44" },
  { label: "3D模型", value: "3" }
]);

const getIconComponent = (icon) => {
  switch (icon) {
    case 'star': return StarIcon;
    case 'sparkles': return SparklesIcon;
    case 'trending': return TrendingUpIcon;
    default: return SparklesIcon;
  }
};

const router = useRouter();

// 跳转到对应矿物的二级详情页（使用宝玉石标本库）
const goToDetail = (item) => {
  const type = item.type || '宝玉石';
  const name = item.title;
  router.push({
    name: 'mineral-detail',
    params: {
      type,
      name
    }
  });
};

onMounted(async () => {
  // 可以在这里加载统计数据
  // 目前使用静态数据
});
</script>

<style scoped>
.sidebar-container {
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  overflow-y: scroll;
  scrollbar-width: none;
  -ms-overflow-style: none;
}

.sidebar-container::-webkit-scrollbar {
  display: none;
}

.section {
  margin-bottom: 1rem;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.header-icon {
  width: 1.25rem;
  height: 1.25rem;
}

.header-icon.sparkles {
  color: rgb(245, 158, 11);
}

.header-icon.trending {
  color: rgb(20, 184, 166);
}

.section-title {
  color: white;
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
}

.recommendations-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.recommendation-item {
  background: linear-gradient(to bottom right, rgba(30, 41, 59, 0.6), rgba(15, 23, 42, 0.6));
  backdrop-filter: blur(12px);
  border: 1px solid rgba(51, 65, 85, 0.5);
  border-radius: 0.5rem;
  padding: 1rem;
  cursor: pointer;
  transition: transform 0.3s ease;
  animation: slideInRight 0.4s ease forwards;
  opacity: 0;
}

@keyframes slideInRight {
  from {
    opacity: 0;
    transform: translateX(20px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

.recommendation-item:hover {
  transform: translateX(5px);
}

.item-content {
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
}

.icon-wrapper {
  padding: 0.5rem;
  border-radius: 0.5rem;
  background-color: color-mix(in srgb, var(--item-color) 20%, transparent);
  color: var(--item-color);
}

.item-text {
  flex: 1;
}

.item-title {
  color: white;
  margin: 0 0 0.25rem 0;
  transition: color 0.3s ease;
  font-size: 0.9rem;
  font-weight: 600;
}

.recommendation-item:hover .item-title {
  color: rgb(20, 184, 166);
}

.item-description {
  color: rgb(148, 163, 184);
  font-size: 0.75rem;
  line-height: 1rem;
  margin: 0;
}

.hover-indicator {
  height: 0.25rem;
  margin-top: 0.75rem;
  border-radius: 9999px;
  background-color: var(--item-color);
  opacity: 0;
  transition: opacity 0.3s ease;
}

.recommendation-item:hover .hover-indicator {
  opacity: 1;
}

.discoveries-box {
  background: linear-gradient(to bottom right, rgba(30, 41, 59, 0.6), rgba(15, 23, 42, 0.6));
  backdrop-filter: blur(12px);
  border: 1px solid rgba(51, 65, 85, 0.5);
  border-radius: 0.5rem;
  padding: 1rem;
}

.discoveries-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.discovery-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: rgb(203, 213, 225);
  cursor: pointer;
  transition: color 0.3s ease;
  animation: fadeIn 0.3s ease forwards;
  opacity: 0;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

.discovery-item:hover {
  color: white;
}

.discovery-dot {
  width: 0.375rem;
  height: 0.375rem;
  border-radius: 50%;
  background-color: rgb(20, 184, 166);
  transition: transform 0.3s ease;
}

.discovery-item:hover .discovery-dot {
  transform: scale(1.5);
}

.discovery-text {
  font-size: 0.875rem;
  line-height: 1.25rem;
}

.stats-section {
  margin-top: auto;
}

.stats-box {
  background: linear-gradient(to bottom right, rgba(30, 41, 59, 0.6), rgba(15, 23, 42, 0.6));
  backdrop-filter: blur(12px);
  border: 1px solid rgba(51, 65, 85, 0.5);
  border-radius: 0.5rem;
  padding: 1rem;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
}

.stat-item {
  text-align: center;
  animation: scaleUp 0.3s ease forwards;
  opacity: 0;
  transform: scale(0);
}

@keyframes scaleUp {
  from {
    opacity: 0;
    transform: scale(0);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

.stat-value {
  font-size: 1.5rem;
  line-height: 2rem;
  background: linear-gradient(to right, rgb(45, 212, 191), rgb(168, 85, 247));
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
  font-weight: 700;
}

.stat-label {
  font-size: 0.75rem;
  line-height: 1rem;
  color: rgb(148, 163, 184);
  margin-top: 0.25rem;
}
</style>

