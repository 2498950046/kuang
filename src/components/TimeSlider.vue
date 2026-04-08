<template>
  <div class="time-slider-container">
    <!-- 时期标签层 -->
    <div class="period-labels-layer">
      <div v-for="period in displayedPeriods" :key="period.name" class="period-label-item"
        :class="{ 'period-label-alternate': period.alternate }" :style="{ left: period.position + '%' }"
        :title="period.name">
        {{ period.displayName }}
      </div>
    </div>

    <!-- 滑块层 -->
    <el-slider v-model="sliderValue" range :min="minSlider" :max="maxSlider" :format-tooltip="formatTooltip"
      :step="yearStep" :marks="marks" @change="handleSliderChange" />
  </div>
</template>

<script setup>
import { ref, watch, computed, onMounted } from 'vue';
import { ElSlider } from 'element-plus';

const props = defineProps({
  minDate: {
    type: Date,
    required: true,
  },
  maxDate: {
    type: Date,
    required: true,
  },
  selectedRange: {
    type: Array,
    default: () => [null, null],
  },
});

const emit = defineEmits(['update:selectedRange']);

// const PERIODS = [
//   { name: '早期革命时期', start: 1920, end: 1927, shortName: '早期革命' },
//   { name: '土地革命战争时期', start: 1927, end: 1937, shortName: '土地革命' },
//   { name: '抗日战争时期', start: 1937, end: 1945, shortName: '抗日战争' },
//   { name: '解放战争时期', start: 1945, end: 1949, shortName: '解放战争' },
//   { name: '新中国成立初期', start: 1949, end: 1956, shortName: '新中国成立初期' },
//   { name: '社会主义建设探索时期', start: 1956, end: 1966, shortName: '社会主义探索时期' },
//   { name: '文化大革命时期', start: 1966, end: 1976, shortName: '文革时期' },
//   { name: '改革开放初期', start: 1976, end: 1992, shortName: '改革开放初期' },
//   { name: '改革开放深化时期', start: 1992, end: 2012, shortName: '改革开放深化时期' },
//   { name: '新时代', start: 2012, end: 2025, shortName: '新时代' },
// ];

const PERIODS = [
  { name: '早期革命时期', start: 1920, end: 1927, shortName: '早期革命' },
  { name: '土地革命战争时期', start: 1927, end: 1937, shortName: '土地革命' },
  { name: '抗日战争时期', start: 1937, end: 1945, shortName: '抗日战争' },
  { name: '解放战争时期', start: 1945, end: 1949, shortName: '解放战争' },
  { name: '新中国成立初期', start: 1949, end: 1956, shortName: '新中国成立初' },
  { name: '社会主义建设探索时期', start: 1956, end: 1966, shortName: '社会主义探索' },
  { name: '文化大革命时期', start: 1966, end: 1976, shortName: '文革时期' },
  { name: '改革开放初期', start: 1976, end: 1992, shortName: '改革开放初期' },
  { name: '改革开放深化时期', start: 1992, end: 2012, shortName: '改革开放深化时期' },
  { name: '新时代', start: 2012, end: 2025, shortName: '新时代' },
];

// 直接使用年份作为滑块值
const minSlider = computed(() => props.minDate.getFullYear());
const maxSlider = computed(() => props.maxDate.getFullYear());

const sliderValue = ref([minSlider.value, maxSlider.value]);
const yearStep = 1;

const formatTooltip = (val) => val.toString();

watch(() => props.selectedRange, (newRange) => {
  if (newRange && newRange[0] && newRange[1]) {
    sliderValue.value = [newRange[0].getFullYear(), newRange[1].getFullYear()];
  }
}, { immediate: true });

const handleSliderChange = (newVal) => {
  const newRange = [new Date(newVal[0], 0, 1), new Date(newVal[1], 11, 31)];
  emit('update:selectedRange', newRange);
};

const getPosition = (year) => {
  const startYear = props.minDate.getFullYear();
  const endYear = props.maxDate.getFullYear();
  // console.log(`Calculating position for year ${year} between ${startYear} and ${endYear}`);
  return ((year - startYear) / (endYear - startYear)) * 100;
};

// 智能处理时期标签显示
// const displayedPeriods = computed(() => {
//   const startYear = props.minDate.getFullYear();
//   const endYear = props.maxDate.getFullYear();
//   const totalYears = endYear - startYear;

//   console.log(`Calculating displayed periods from ${startYear} to ${endYear}`);

//   // 过滤出在范围内的时期
//   let periods = PERIODS.filter(period =>
//     period.start >= startYear && period.start < endYear
//   ).map(period => ({
//     ...period,
//     position: getPosition(period.start + (period.end - period.start) / 2),
//     displayName: period.name,
//     alternate: false
//   }));

//   console.log('periods', periods);


//   // 年份范围越大，越需要使用简称
//   const useShortName = totalYears > 30; // 大于30年使用简称

//   if (useShortName) {
//     periods = periods.map(p => ({
//       ...p,
//       displayName: p.shortName || p.name
//     }));
//   }

//   return periods;
// });

// const displayedPeriods = computed(() => {
//   const startYear = props.minDate.getFullYear();
//   const endYear = props.maxDate.getFullYear();
//   const totalYears = endYear - startYear;

//   // 过滤出在范围内的时期
//   let periods = PERIODS.filter(period =>
//     period.start >= startYear && period.end <= endYear
//   ).map(period => ({
//     ...period,
//     position: getPosition(period.start + (period.end - period.start) / 2),
//     displayName: period.name,
//     alternate: false
//   }));

//   // 年份范围越大，越需要使用简称
//   const useShortName = totalYears > 30; // 大于30年使用简称

//   if (useShortName) {
//     periods = periods.map(p => ({
//       ...p,
//       displayName: p.shortName || p.name
//     }));
//   }




//   return periods;
// });

const displayedPeriods = computed(() => {
  const startYear = props.minDate.getFullYear();
  const endYear = props.maxDate.getFullYear();
  const totalYears = endYear - startYear;
  const widthPerYear = 100 / (endYear - startYear);

  // 获取所有在范围内的时期
  let periods = PERIODS.filter(period => 
    period.start >= startYear && period.end <= endYear
  ).map(period => ({
    ...period,
    position: getPosition(period.start + (period.end - period.start) / 2),
    width: (period.end - period.start) * widthPerYear,
    displayName: totalYears > 30 ? (period.shortName || period.name) : period.name,
    alternate: false // 默认不下移
  }));

  // 检测并处理密集标签
  const MIN_SPACING = 8; // 最小间距百分比
  for (let i = 1; i < periods.length; i++) {
    const prev = periods[i - 1];
    const current = periods[i];
    
    // 计算与前一个标签的间距
    const spacing = current.position - prev.position;
    
    // 如果间距太小且当前标签不是alternate，则上移当前标签
    if (spacing < MIN_SPACING && !prev.alternate) {
      current.alternate = true;
    }
  }

  // 特别处理：如果标签宽度太小，强制使用简称
  return periods.map(p => ({
    ...p,
    displayName: p.width < 10 ? (p.shortName || p.name) : p.displayName
  }));
});


// 年份标记，避免与时期标签重叠
const marks = computed(() => {
  const yearMarks = {};
  const startYear = props.minDate.getFullYear();
  const endYear = props.maxDate.getFullYear();
  const rangeYears = endYear - startYear;

  // 获取所有时期开始年份
  const periodStartYears = displayedPeriods.value.map(p => p.start);

  // 动态计算年份间隔
  let interval = 1;
  if (rangeYears > 100) {
    interval = 100;
  } else if (rangeYears > 50) {
    interval = 50;
  } else if (rangeYears > 20) {
    interval = 20;
  } else if (rangeYears > 10) {
    interval = 10;
  }


  // 添加年份标记
  for (let year = startYear; year <= endYear; year++) {
    const isPeriodStart = periodStartYears.includes(year);

    // 如果是时期开始年份，一定要显示
    if (isPeriodStart) {
      yearMarks[year] = {
        style: {
          color: 'var(--text-muted)',
          fontSize: '10px',
          fontWeight: '500',
          marginTop: '10px'
        },
        label: year.toString()
      };
    }
    // 其他年份根据间隔显示，但要检查是否会与时期年份太近
    else if (year === startYear || year === endYear || (year - startYear) % interval === 0) {
      // 检查是否与时期年份太近
      const tooClose = periodStartYears.some(py => Math.abs(py - year) < interval / 2);

      if (!tooClose) {
        yearMarks[year] = {
          style: {
            color: 'var(--text-muted)',
            fontSize: '10px',
            opacity: '0.5' // 非时期年份稍微淡一些
          },
          label: year.toString()
        };
      }
    }
  }

  return yearMarks;
});

onMounted(() => {
  if (!props.selectedRange || !props.selectedRange[0] || !props.selectedRange[1]) {
    sliderValue.value = [minSlider.value, maxSlider.value];
    emit('update:selectedRange', [props.minDate, props.maxDate]);
  }
});
</script>

<style scoped>
.time-slider-container {
  bottom: 62px;
  left: 5px;
  transform: translateX(0%);
  max-width: 71.2%;
  min-height: 52px;
  background-color: var(--bg-secondary);
  border-radius: 30px;
  padding: 8px 13px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
  display: flex;
  flex-direction: column;
  align-items: center;
  z-index: 1000;
  box-sizing: border-box;
  position: relative;
}

/* 时期标签层 */
.period-labels-layer {
  position: inherit;
  top: 4px;
  left: auto;
  right: auto;
  pointer-events: none;
  width: 95%;
  height: 0px;
}

.period-label-item {
  position: absolute;
  top: 0px;
  transform: translateX(-50%);
  font-size: 10px;
  color: var(--text-muted);
  white-space: nowrap;
  font-weight: 500;
  /* padding: 2px 4px; */
  /* background-color: var(--bg-secondary); */
  border-radius: 3px;
  transition: all 0.3s ease;
}

/* 交替显示的标签位置上移 */
.period-label-alternate {
  top: 0;
  font-size: 10px;
  opacity: 0.9;
}

/* 鼠标悬停效果 */
.time-slider-container:hover .period-label-item {
  opacity: 1;
}

.period-label-item::after {
  content: '';
  position: absolute;
  bottom: -5px;
  left: 50%;
  transform: translateX(-50%);
  width: 1px;
  height: 5px;
  background-color: var(--text-muted);
  opacity: 0.3;
}

/* 滑块样式 */
.time-slider-container :deep(.el-slider) {
  width: 95%;
  margin-top: 8px;
}

.time-slider-container :deep(.el-slider__runway) {
  background-color: var(--border-color);
  height: 6px;
}

.time-slider-container :deep(.el-slider__bar) {
  background-color: var(--color-accent);
  height: 6px;
}

.time-slider-container :deep(.el-slider__button-wrapper) {
  top: -15px;
}

.time-slider-container :deep(.el-slider__button) {
  border-color: var(--color-accent);
  background-color: var(--bg-primary);
  box-shadow: 0 0 0 3px rgba(var(--color-accent-rgb), 0.3);
  width: 16px;
  height: 16px;
}

/* 年份标记样式 */
.time-slider-container :deep(.el-slider__marks-text) {
  margin-top: 15px;
  font-size: 0.85em;
  color: var(--text-muted);
  transition: opacity 0.3s ease;
}

.time-slider-container :deep(.el-slider__stop) {
  background-color: var(--text-muted);
  width: 1px;
  height: 8px;
  top: 0px;
}

/* 响应式处理 */
@media (max-width: 768px) {
  .period-label-item {
    font-size: 0.75em;
  }

  .period-label-alternate {
    font-size: 0.7em;
  }

  .time-slider-container :deep(.el-slider__marks-text) {
    font-size: 0.75em;
  }
}


/* 上移的标签样式 */
.period-label-alternate {
  top: -10px; 
  opacity: 0.9;
}

/* 连接线样式 */
.period-label-item::after {
  content: '';
  position: absolute;
  bottom: -5px;
  left: 50%;
  transform: translateX(-50%);
  width: 1px;
  height: 5px;
  background-color: var(--text-muted);
  opacity: 0.3;
}
</style>
