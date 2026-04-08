<!-- src/components/GraphChart.vue -->
<template>
  <div ref="chartRef" style="width: 100%; height: 100%;"></div>
</template>

<script setup>
import { ref, onMounted, watch, onUnmounted } from 'vue';
import * as echarts from 'echarts';
import { ElMessage } from 'element-plus'

const props = defineProps({
  graphData: Object,
  styleConfig: Object,
  layoutConfig: Object,
  forceLabelShow: String,
  entityCategoryLabels: '[object Object]',
  edgeTypeLabels: '[object Object]',
});
const emit = defineEmits([
  'legend-select-changed',
  'query-related-nodes',
  'node-select',
  'edge-select',
  'clear-select'
]);


// 定义类别与描述性文本的映射
const categoryLabels = props.entityCategoryLabels;

const chartRef = ref(null);
let myChart = null;

onMounted(() => {
  initChart();
  window.addEventListener('resize', () => myChart?.resize());
});

onUnmounted(() => myChart?.dispose());

function initChart() {
  myChart = echarts.init(chartRef.value, 'dark');

  // 初始化事件监听
  myChart.on('finished', () => myChart.on('graphroam', updateLabelVisibility));
  myChart.on('legendselectchanged', (params) => emit('legend-select-changed', params.selected));

  // 添加双击节点事件监听
  myChart.on('dblclick', handleNodeDoubleClick);

  renderChart();

  window.addEventListener('resize', () => myChart?.resize());
  myChart.on('finished', () => myChart.on('graphroam', updateLabelVisibility));
  myChart.on('legendselectchanged', (params) => emit('legend-select-changed', params.selected));
  myChart.on('dragend', (params) => {
    if (params.target) {
      const option = myChart.getOption();
      option.series[0].data[params.dataIndex].fixed = true;
      myChart.setOption(option);
    }
  });



  let clickTimer = null;

  myChart.on('click', (params) => {
    if (clickTimer) clearTimeout(clickTimer);

    // 单击逻辑
    if (params.dataType === 'node') {
      clickTimer = setTimeout(() => {

        emit('node-select', params.data);
          // console.log(`单机了节点: ${nodeData.name}`);
          // console.log(nodeData);
        clickTimer = null;
      }, 250);

    } else if (params.dataType === 'edge') {
      emit('clear-select');
      emit('edge-select', params.data);
    }
    // 250ms 可根据实际体验调整
  });

  myChart.on('dblclick', (params) => {
    if (clickTimer) {
      clearTimeout(clickTimer);
      clickTimer = null;
    }
    // 双击逻辑
    if (params.dataType === 'node' && params.data.fixed) {
      const option = myChart.getOption();
      option.series[0].data[params.dataIndex].fixed = false;
      myChart.setOption(option);
    }
  });

  // 2. 新增底层 ZRender 事件监听，用于处理对【空白区域】的点击
  myChart.getZr().on('click', (event) => {
    // event.target 会在点击到图形元素时有值，点击到空白处时为 undefined
    if (!event.target) {
      // 当 event.target 为 undefined 时，意味着点击在了画布的空白区域
      emit('clear-select');
    }
  });

};


function handleNodeDoubleClick(params) {
  if (params.dataType === 'node') {
    const nodeData = params.data;
    const ID = nodeData.properties.person_id || nodeData.properties.event_id
    console.log(`双击了节点: ${nodeData.name}`);
    console.log(nodeData);

    // 触发查询关联节点的事件
    emit('query-related-nodes', nodeData.name);
  }
}

onUnmounted(() => myChart?.dispose());

watch(() => [props.graphData, 
props.styleConfig, 
props.layoutConfig, 
props.forceLabelShow], renderChart, { deep: true });

watch(() => document.body.className, () => {
  myChart?.dispose();
  myChart = echarts.init(chartRef.value, 'dark');

  renderChart();
});

function updateLabelVisibility() {
  if (!myChart) return;
  const option = myChart.getOption();
  if (!option || !option.series || !option.series.length) return;
  let showLabel;
  if (props.forceLabelShow === 'on') { showLabel = true; }
  else if (props.forceLabelShow === 'off') { showLabel = false; }
  else { const zoom = option.series[0].zoom; showLabel = zoom > 0.7; }
  myChart.setOption({ series: [{ label: { show: showLabel }, edgeLabel: { show: showLabel } }] });
}

function getTextColor() {
  return getComputedStyle(document.body)
    .getPropertyValue('--text-primary')
    .trim() || '#3c3c58';
}
function getTextShadowColor() {
  return getComputedStyle(document.body)
    .getPropertyValue('--border-color')
    .trim() || '#000';
}


function renderChart() {
  console.log('DEBUG: renderChart called!');
  console.log('DEBUG: props.graphData received:', props.graphData);
  console.log('DEBUG: props.graphData.nodes:', props.graphData.nodes);
  console.log('DEBUG: props.graphData.links:', props.graphData.links);
  // 【核心修复】添加防御性编程，确保所有必要数据都已准备好
  if (!myChart || !props.graphData || !props.graphData.nodes || props.graphData.nodes.length === 0 || !props.styleConfig.nodes || Object.keys(props.styleConfig.nodes).length === 0) {
    myChart.clear(); // 如果数据不完整，清空图表
    console.log('DEBUG: renderChart returned early due to incomplete data.');
    return;
  }


  const labelColor = getTextColor();          // ← 这次一定拿到 #rrggbb
  const textShadowColor = getTextShadowColor();
  // console.log('【当前主题色】', labelColor);   // 调试用，可删

  const nodes = props.graphData.nodes.map(node => {
    const style = props.styleConfig.nodes[node.category] || {};
    const labelFormatter = style.labelFormatter || (n => n.name);


    return {
      ...node,
      symbolSize: style.size || 35,
      itemStyle: { color: style.color },
      label: {
        formatter: labelFormatter(node),
        color: labelColor,
        textShadowBlur: 2,
        textShadowColor: textShadowColor,


      }
    }; 
  });


  // 创建一个 Map 来跟踪节点对之间的边
  const edgeGroups = new Map();

  // 第一次遍历：对边进行分组
  props.graphData.links.forEach(link => {
    const edgePair = `${link.source}-${link.target}`;
    if (!edgeGroups.has(edgePair)) {
      edgeGroups.set(edgePair, []);
    }
    edgeGroups.get(edgePair).push(link);
  });


  const links = props.graphData.links.map(link => {
    const style = props.styleConfig.edges[link.name] || {};
    const labelFormatter = style.labelFormatter || ((l) => l.name);

    // 获取相同源目标节点的所有边
    const edgePair = `${link.source}-${link.target}`;
    const group = edgeGroups.get(edgePair);
    const index = group.indexOf(link);
    const total = group.length;

    // 优化曲度计算
    let curveness = 0;
    if (total > 0) {
      curveness = 0.1 + (index * 0.1);
    }

    return {
      ...link,
      lineStyle: {
        color: style.color,
        width: style.width || 1,
        curveness: curveness,
        opacity: 0.8,
        type: 'solid'
      },
      label: {
        show: true,
        formatter: labelFormatter(link),
        fontSize: 12,
        color: style.color || '#999',
        position: 'middle',
        padding: [4, 8],
        borderRadius: 4,
        distance: 5
      },
      emphasis: {
        lineStyle: {
          width: 3,
          opacity: 1
        },
        label: {
          fontSize: 14,
          backgroundColor: 'rgba(255, 255, 255, 0.9)'
        }
      }
    };
  });

  console.log('DEBUG: Final nodes for ECharts:', nodes);
  console.log('DEBUG: Final links for ECharts:', links);

  const categories = Object.keys(props.styleConfig.nodes).map(name => ({
    name: name, // 保持英文
    itemStyle: { color: props.styleConfig.nodes[name].color }
  }));

  // 添加调试输出
  
  console.log('echarts得到的数据props.graphData:', props.graphData);
  console.log('原始 categories:', JSON.parse(JSON.stringify(categories)));
  console.log('映射表 categoryLabels:', categoryLabels);
  
  

  const legendSelected = {};
  Object.entries(props.styleConfig.nodes).forEach(([name, config]) => {
    legendSelected[name] = config.visible; // 使用英文名称作为 key
  });



  myChart.setOption({
    tooltip: {
      formatter: (params) => {
        if (params.dataType === 'node') return `<b>${params.data.name}</b> (${params.data.category})`;
        if (params.dataType === 'edge') {
          const source = props.graphData.nodes.find(n => n.id === params.data.source)?.name || '未知';
          const target = props.graphData.nodes.find(n => n.id === params.data.target)?.name || '未知';
          return `${source} -[${params.data.name}]-> ${target}`;
        }
      }
    },
    legend: {
      show: true,
      top: '20px',
      left: '20px',
      orient: 'vertical',
      data: categories.map(cat => cat.name), // 使用英文名称
      selected: legendSelected,
      formatter: function (name) {
        return categoryLabels[name] || name; // 动态映射为中文描述性文本
      },
      textStyle: { color: 'inherit' }
    },

    series: [{
      type: 'graph',
      layout: 'force',
      roam: true,
      draggable: true,
      data: nodes,
      links: links,
      categories: categories,
      label: {
        show: false,
        position: 'inside',
        fontSize: 14,
      },
      edgeSymbol: ['none', 'arrow'],
      edgeSymbolSize: [4, 10],
      edgeLabel: {
        show: true,
        position: 'middle',
        fontSize: 12,
        color: 'inherit',
        formatter: (params) => {
          const relationshipName = params.data.name;
          return relationshipName;
        }

      },
      lineStyle: { opacity: 0.8 },
      force: {
        repulsion: props.layoutConfig.repulsion,
        edgeLength: props.layoutConfig.edgeLength,
        gravity: 0.05,
        friction: 0.4,
        layoutAnimation: true,
    
      },

      itemStyle: {
        borderWidth: 1.5,
        borderColor: 'rgba(255,255,255,0.3)',
        shadowBlur: 10,
        shadowColor: 'rgba(0,0,0,0.2)'
      },
      emphasis: {
        focus: 'adjacency',
        lineStyle: {
          width: 4
        },
        edgeLabel: {
          fontSize: 14,
          backgroundColor: 'rgba(255, 255, 255, 0.7)',
          padding: [4, 8],
          borderRadius: 4
        }
      }
    }]
  }, { notMerge: true });
  setTimeout(updateLabelVisibility, 100);


}

</script>
