<template>
  <div class="global-stats">
    <!-- 实体统计项 -->
    <!-- 人物查询：MATCH (n:Person) RETURN n -->
    <div 
      class="stat-item clickable" 
      @click="handleStatClick(QUERIES.person)"
      :style="getStatItemStyle('mineral')"
    >
      <div class="text-content">
        <span class="stat-title" :style="{ color: getStatColor('mineral') }">
          <Gem class="stat-icon" :size="14" stroke-width="2" :style="{ color: getStatColor('mineral') }" />矿物名
        </span>
        <span class="stat-value" :style="{ color: getStatColor('mineral') }">
          <span v-if="isLoading" class="stat-loading">···</span>
          <span v-else>{{ totalPersonNodes }}</span>
          <span class="stat-unit">个</span>
        </span>
      </div>
    </div>

    <!-- 颜色查询：MATCH (n:Color) RETURN n -->
    <div 
      class="stat-item clickable" 
      @click="handleStatClick(QUERIES.event)"
      :style="getStatItemStyle('color')"
    >
      <div class="text-content">
        <span class="stat-title" :style="{ color: getStatColor('color') }">
          <Palette class="stat-icon" :size="14" stroke-width="2" :style="{ color: getStatColor('color') }" />
          颜色
        </span>
        <span class="stat-value" :style="{ color: getStatColor('color') }">
          <span v-if="isLoading" class="stat-loading">···</span>
          <span v-else>{{ totalEventNodes }}</span>
          <span class="stat-unit">个</span>
        </span>
      </div>
    </div>

    <!-- 战役战斗查询：MATCH (n:Event {category:"参加的战役战斗"}) RETURN n -->
    <div 
      class="stat-item clickable" 
      @click="handleStatClick(QUERIES.battle)"
      :style="getStatItemStyle('location')"
    >
      <div class="text-content">
        <span class="stat-title" :style="{ color: getStatColor('location') }">
          <MapPin class="stat-icon" :size="14" stroke-width="2" :style="{ color: getStatColor('location') }" />
          发现地区
        </span>
        <span class="stat-value" :style="{ color: getStatColor('location') }">
          <span v-if="isLoading" class="stat-loading">···</span>
          <span v-else>{{ totalBattleNodes }}</span>
          <span class="stat-unit">处</span>
        </span>
      </div>
    </div>

    <!-- 关系统计项 -->
    <!-- 战友关系查询：MATCH (n1)-[r:COMRADE_WITH|COMRADE]->(n2) RETURN r,n1,n2 LIMIT 250 -->
    <div 
      class="stat-item clickable" 
      @click="handleStatClick(QUERIES.comrade)"
      :style="getStatItemStyle('category')"
    >
      <div class="text-content relationship-count">
        <span class="stat-title" :style="{ color: getStatColor('category') }">
          <Share2 class="stat-icon" :size="14" stroke-width="2" :style="{ color: getStatColor('category') }" />
          分类关系
        </span>
        <span class="stat-value" :style="{ color: getStatColor('category') }">
          <span v-if="isLoading" class="stat-loading">···</span>
          <span v-else>{{ totalComradeEdges }}</span>
          <span class="stat-unit">个</span>
        </span>
      </div>
    </div>

    <!-- 参与关系查询（假设关系类型为 PARTICIPATED）：MATCH (n1)-[r:PARTICIPATED]->(n2) RETURN r,n1,n2 LIMIT 250 -->
    <div 
      class="stat-item clickable" 
      @click="handleStatClick(QUERIES.participated)"
      :style="getStatItemStyle('year')"
    >
      <div class="text-content relationship-count">
        <span class="stat-title" :style="{ color: getStatColor('year') }">
          <Share2 class="stat-icon" :size="14" stroke-width="2" :style="{ color: getStatColor('year') }" />
          时间关系
        </span>
        <span class="stat-value" :style="{ color: getStatColor('year') }">
          <span v-if="isLoading" class="stat-loading">···</span>
          <span v-else>{{ totalParticipatedEdges }}</span>
          <span class="stat-unit">个</span>
        </span>
      </div>
    </div>

    <!-- 亲友关系查询：MATCH (n1)-[r:FAMILY_WITH]->(n2) RETURN r,n1,n2 -->
    <div 
      class="stat-item clickable" 
      @click="handleStatClick(QUERIES.family)"
      :style="getStatItemStyle('formula')"
    >
      <div class="text-content relationship-count">
        <span class="stat-title" :style="{ color: getStatColor('formula') }">
          <Share2 class="stat-icon" :size="14" stroke-width="2" :style="{ color: getStatColor('formula') }" />
          层级关系
        </span>
        <span class="stat-value" :style="{ color: getStatColor('formula') }">
          <span v-if="isLoading" class="stat-loading">···</span>
          <span v-else>{{ totalFamilyEdges }}</span>
          <span class="stat-unit">个</span>
        </span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { Share2, Gem, MapPin, Building, Palette } from 'lucide-vue-next';
import { defineProps, defineEmits, computed } from 'vue'; // 确保导入 defineEmits

// 定义组件可发出的事件，包括 'runQuery'，它将携带 Cypher 查询字符串
const emit = defineEmits(['runQuery']);

// 定义每个统计项对应的 Cypher 查询
const QUERIES = {
  // 矿物名
  person: 'MATCH (n:Specimen) RETURN n',
  // 发祥地
  battle: 'MATCH (n:Location) RETURN n',
  // battle: 'MATCH (n:Event) WHERE n.category IN ["参加的战役战斗", "战役战斗"] RETURN n',
  // 颜色
  event: 'MATCH (n:Color) RETURN n',
  // 矿物类别层级关系
  family: 'MATCH (n1)-[r:HAS_SUBCATEGORY]->(n2) RETURN r,n1,n2',
  // 分类关系
  comrade: 'MATCH (n1)-[r:BELONGS_TO]->(n2) RETURN r,n1,n2 LIMIT 250',
  // 时间关系（假设关系类型为 PARTICIPATED）
  participated: 'MATCH (n1)-[r:DISCOVERED_IN]->(n2) RETURN r,n1,n2 LIMIT 250',
};

// 定义各图谱的颜色配置（与App.vue和GraphChart3D.vue保持一致）
const specimenColorPalettes = {
  '宝玉石': {
    category: '#6200EA',
    mineral: '#FF0090',
    color: '#00B4D8',
    location: '#00E676',
    formula: '#FFD600',
    year: '#FF6D00',
  },
  '岩石标本': {
    category: '#F57F17',
    mineral: '#FFDD4B',
    color: '#FFF59D',
    location: '#8BC34A',
    formula: '#A5D6A7',
    year: '#C0CA33',
  },
  '矿石标本': {
    category: '#FF5722',
    mineral: '#FF9800',
    color: '#FF8A65',
    location: '#FFCC80',
    formula: '#FFE082',
    year: '#FFF59D',
  },
  '铀矿物': {
    category: '#1B5E20',
    mineral: '#76FF03',
    color: '#00BFA5',
    location: '#AFB42B',
    formula: '#FFFF00',
    year: '#69F0AE',
  },
  '构造标本': {
    category: '#3F51B5',
    mineral: '#5C6BC0',
    color: '#7986CB',
    location: '#9FA8DA',
    formula: '#C5CAE9',
    year: '#E8EAF6',
  },
  '矿物标本': {
    category: '#007AFF',
    mineral: '#5AC8FA',
    color: '#34C759',
    location: '#FF9500',
    formula: '#FF2D55',
    year: '#AF52DE',
  },
};

const props = defineProps({
  totalPersonNodes: { type: Number, default: 0 },
  totalBattleNodes: { type: Number, default: 0 },
  totalEventNodes: { type: Number, default: 0 },
  totalComradeEdges: { type: Number, default: 0 },
  totalParticipatedEdges: { type: Number, default: 0 },
  totalFamilyEdges: { type: Number, default: 0 },
  selectedSpecimenType: { type: String, default: '矿物标本' },
  isLoading: { type: Boolean, default: false },
});

// 获取当前图谱类型的颜色配置
const currentPalette = computed(() => {
  return specimenColorPalettes[props.selectedSpecimenType] || specimenColorPalettes['矿物标本'];
});

// 获取统计项的颜色
const getStatColor = (type) => {
  return currentPalette.value[type] || '#ffffff';
};

// 获取统计项的样式（包括边框颜色）
const getStatItemStyle = (type) => {
  const color = getStatColor(type);
  return {
    borderColor: color,
    boxShadow: `0 2px 8px rgba(0, 0, 0, 0.15), 0 0 0 1.5px ${color}40`,
  };
};

/**
 * 处理统计项点击事件，发出 runQuery 事件，并将 Cypher 语句作为参数传递给父组件。
 * @param {string} query 要执行的 Cypher 语句
 */
const handleStatClick = (query) => {
  console.log(`Stat clicked. Emitting query: ${query}`);
  emit('runQuery', query);
};
</script>

<style scoped>
/* 根容器：3列2行布局 */
.global-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 6px;
  padding: 5px;
  max-height: 180px; 
}

/* 核心：单个统计卡片的样式 */
.stat-item {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 6px 6px;
  margin: 0;
  border-radius: 8px;
  background: var(--card-bg);
  backdrop-filter: blur(16px) saturate(180%);
  border: 1.5px solid var(--border-color);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15),
    0 0 0 1px rgba(212, 165, 116, 0.15);
  transition: all 0.3s ease;
  width: 100%;
}

/* 添加可点击样式 */
.stat-item.clickable {
  cursor: pointer;
}

/* 鼠标悬停时的交互效果 */
.stat-item.clickable:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 15px rgba(0, 0, 0, 0.2), 0 0 20px currentColor;
  background: var(--bg-hover);
}

/* 鼠标按下时的点击反馈 */
.stat-item.clickable:active {
  transform: translateY(0);
  opacity: 0.9;
}

/* 图标样式 */
.stat-icon {
  color: var(--text-secondary);
  margin-right: 4px;
  flex-shrink: 0;
}

/* 文字内容容器 - 统一使用 column 布局以更好地控制垂直空间 */
.text-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 100%;
}

/* 标题样式 */
.stat-title {
  font-size: 13px;
  color: var(--text-muted);
  margin-bottom: 2px;
  white-space: nowrap;
  display: flex;
  align-items: center;
}

/* 数值样式 */
.stat-value {
  font-size: 20px;
  font-weight: 400;
  color: var(--text-primary);
  line-height: 1;
  display: flex;
  align-items: stretch;
}

/* 单位样式 */
.stat-unit {
  font-size: 17px;
  font-weight: 500;
  color: var(--text-muted);
  margin-left: 4px;
  padding-bottom: 2px;
}

.stat-loading {
  display: inline-block;
  font-size: 16px;
  letter-spacing: 2px;
  animation: blink 1s infinite;
}

@keyframes blink {
  0%, 100% { opacity: 0.3; }
  50% { opacity: 1; }
}
</style>