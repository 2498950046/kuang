<template>
    <div ref="containerRef" style="width: 100%; height: 100%;"></div>
  </template>
  
  <script setup>
import { ref, onMounted, watch, onUnmounted, nextTick } from 'vue';
import ForceGraph3D from '3d-force-graph';
import * as THREE from 'three';
import { forceRadial } from 'd3-force-3d';
import SpriteText from 'three-spritetext';
import { createNodeClickHandler } from '../utils/graph/graphNodeClick.js';
  
  const props = defineProps({
    graphData: Object,
    styleConfig: Object,
    layoutConfig: Object,
    forceLabelShow: String,
    entityCategoryLabels: Object,
    edgeTypeLabels: Object,
    selectedSpecimenType: { type: String, default: '矿物标本' }, // 当前选择的图谱类型
    expandedMineralNodes: { type: Array, default: () => [] }, // 已展开的矿物节点ID数组
    expandedCategoryNodes: { type: Array, default: () => [] }, // 已展开的分类节点ID数组
    mineralChildNodesCount: { type: Object, default: () => ({}) }, // 每个矿物节点的子节点数量（对象格式）
    expandLevel: { type: Number, default: 3 }, // 展开层级：1级=只显示分类节点，2级=显示分类+矿物节点，3级=显示所有节点
  });
  
  const emit = defineEmits([
    'legend-select-changed',
    'query-related-nodes',
    'node-select',
    'edge-select',
    'clear-select',
    'toggle-mineral-expansion',
    'toggle-category-expansion'
  ]);
  
const containerRef = ref(null);
let graphInstance = null;
let selectedNodeId = ref(null); // 当前选中的节点ID
let connectedNodeIds = ref(new Set()); // 与选中节点直接相连的节点ID集合
const DEFAULT_TARGET = new THREE.Vector3(0, 0, 0);
// 保存点击节点之前的相机状态
let savedCameraState = null;
// 记录上一帧的节点位置，避免局部展开时全局跳动
let previousNodePositions = new Map();
let shouldRunFullLayout = true; // 仅在大规模变动时运行全局力导向

  // 基于节点属性/类别推断层级，用于径向分层布局
  // 级别最高的分类在中心（level=0），向外扩展
  function getNodeLevel(node) {
    if (!node) return 0;
    const levelValue = node.properties?.level ?? node.level;
    if (Number.isFinite(Number(levelValue))) {
      // 将数据库中的level转换为布局层级：level=1（最高级）-> 布局层级=0（中心）
      // level=2 -> 布局层级=1，level=3 -> 布局层级=2，以此类推
      const dbLevel = Number(levelValue);
      return Math.max(0, dbLevel - 1);
    }

    const category = node.category || '';
    // 顶层分类（Category level=1）在中心
    if (category === 'Category' || category === '分类') {
      // 检查是否是顶层分类（level=1）
      const catLevel = node.properties?.level ?? node.level;
      if (Number.isFinite(Number(catLevel)) && Number(catLevel) === 1) {
        return 0; // 顶层分类在中心
      }
      return 1; // 子分类在第一层
    }
    // 标本节点在最外层
    if (category === 'Specimen' || category === '标本') return 4;
    // 其他信息型节点（颜色、产地、年份、捐赠人等）在中间层
    if (category === 'Color' || category === '颜色' || 
        category === 'Location' || category === '产地' ||
        category === 'Year' || category === '年份' ||
        category === 'Donor' || category === '捐赠人') return 3;
    return 2; // 默认在第二层
  }

// 判定常用类别
function isMineralCategory(category) {
  return ['Mineral', '中文名称', '矿物', 'Specimen', '标本'].includes(category || '');
}

function isChildCategory(category) {
  return ['Year', '年份', 'Location', '产地', 'Color', '颜色'].includes(category || '');
}

// 供外部调用的缩放方法，模拟鼠标滚轮缩放相机距离
  function adjustZoom(factor = 1) {
    if (!graphInstance) return;
    const cam = graphInstance.camera();
    const controls = graphInstance.controls?.();
    const target = controls?.target || DEFAULT_TARGET;
    const dir = cam.position.clone().sub(target);
    const newLen = THREE.MathUtils.clamp(dir.length() * factor, 150, 5000);
    dir.setLength(newLen);
    cam.position.copy(target.clone().add(dir));
    cam.updateProjectionMatrix();
    controls?.update();
  }

  // 保存当前相机状态
  function saveCameraState() {
    if (!graphInstance) return;
    const cam = graphInstance.camera();
    const controls = graphInstance.controls?.();
    if (cam && controls) {
      savedCameraState = {
        position: cam.position.clone(),
        target: controls.target.clone()
      };
    }
  }

  // 重置相机到保存的状态（不锁定任何节点）
  function resetCameraToDefault() {
    if (!graphInstance) return;
    
    // 如果有保存的相机状态，恢复到保存的状态
    if (savedCameraState) {
      const cam = graphInstance.camera();
      const controls = graphInstance.controls?.();
      if (cam && controls) {
        // 恢复相机位置和目标，但不锁定到节点
        cam.position.copy(savedCameraState.position);
        controls.target.copy(savedCameraState.target);
        controls.update();
        cam.updateProjectionMatrix();
      }
    } else {
      // 如果没有保存的状态，重置到默认位置（拉远一点，让初始图谱不会太大，无动画）
      graphInstance.cameraPosition({ x: 0, y: 0, z: 2000 }, null, 0);
    }
  }

  // 将层级转换为目标半径，形成明显的球壳分布
  // 增加层级间距，让球体效果更明显
  function getTargetRadiusByLevel(node) {
    // 检测当前图谱数据是否是层级关系图谱
    let isHierarchical = false;
    if (graphInstance) {
      try {
        const data = graphInstance.graphData?.();
        if (data) {
          isHierarchical = isHierarchicalGraph(data);
        }
      } catch (e) {
        // 如果获取数据失败，使用默认值
      }
    }
    
    // 层级关系图谱使用更大的间距
    const base = isHierarchical ? 120 : (props.layoutConfig?.radialBase ?? 80);
    const step = isHierarchical ? 280 : (props.layoutConfig?.radialStep ?? 180);
    const level = Math.max(0, getNodeLevel(node));
    return base + step * level;
  }
  
  // 定义各图谱的颜色配置
  const specimenColorPalettes = {
    '宝玉石': {
      category: '#6200EA', // Deep Vivid Velvet Purple
    mineral: '#FF0090', // Electric Magenta/Rose (Very Vivid)
    color: '#00B4D8',   // Bright Cyan
    location: '#00E676',// Vivid Emerald
    formula: '#FFD600', // Pure Gold
    year: '#FF6D00'     // Vivid Orange      
    },
    '岩石标本': {
      // 黄色+青绿色色调配置 - 层次分明，分类和矿物节点颜色完全不同
      category: '#F57F17', // 分类节点：深橙黄色（饱和度高，偏橙，最突出）✨
      mineral: '#FFDD4B',  // 矿物节点：鲜亮纯黄色（饱和度高，纯黄，与橙黄完全不同）💛
      color: '#FFF59D',    // 颜色节点：青绿色（中等饱和度，明显可见）
      location: '#8BC34A', // 产地节点：浅青绿（中等饱和度，清晰）
      formula: '#A5D6A7',  // 化学式节点：浅绿色（中等饱和度，淡雅）
      year: '#C0CA33'      // 年份节点：极浅黄绿（饱和度适中，最淡）
    },
    '矿石标本': {
      // 橙色+橘色色调配置 - 层次分明，分类和矿物节点颜色完全不同
      category: '#FF5722', // 分类节点：深橙红色（饱和度高，偏红，最突出）✨
      mineral: '#FF8A65',  // 矿物节点：琥珀金色（饱和度高，偏黄，与橙红完全不同）🧡
      color: '#FF9800',    // 颜色节点：柔和珊瑚橘（中等饱和度，明显可见）
      location: '#FFCC80', // 产地节点：浅橘色（中等饱和度，清晰）
      formula: '#FFE082',  // 化学式节点：浅黄橘（中等饱和度，淡雅）
      year: '#FFF59D'      // 年份节点：极浅黄（饱和度适中，最淡）
    },
    '铀矿物': {
      category: '#1B5E20', // Dark Radiation Green
    mineral: '#76FF03', // Fluorescent Lime (High contrast)
    color: '#00BFA5',   // Teal Green (Distinct from Lime)
    location: '#AFB42B',// Olive Yellow
    formula: '#FFFF00', // Pure Yellow (Warning sign color)
    year: '#69F0AE'     // Mint Green
    },
    '构造标本': {
      // 灰黄色调渐变色配置：每个节点使用两种颜色 [主色, 渐变色]
      // 分类节点使用最亮的金黄色渐变，重点突出
      category: ['#FFD700', '#FFA500'], // 分类节点：纯金黄到橙黄色渐变（最突出）
      mineral: ['#D4A574', '#B8936A'],   // 矿物节点：金黄到深黄渐变（次突出）
      color: ['#F4C430', '#E8B923'],     // 颜色节点：金丝雀黄渐变（明显可见）
      location: ['#C9B8A0', '#A89B87'],  // 产地节点：浅灰棕到灰褐渐变（偏灰，与矿物节点区分）
      formula: ['#DEB887', '#C19A6B'],   // 化学式节点：硬木色到驼色渐变（明显可见）
      year: ['#F0E68C', '#EDD382']       // 年份节点：卡其黄渐变（明显可见）
    },
    '矿物标本': {
      category: '#2962FF', 
      mineral: '#00B0FF',  
      color: '#00E5FF',    
      location: '#00E676', 
      formula: '#C6FF00',  
      year: '#C6FF00'      
    }
  };

  // 1. 颜色逻辑：按指定调色板，根据当前选择的图谱类型
  function getNodeColor(node) {
    if (props.styleConfig?.nodes && node.category) {
      const style = props.styleConfig.nodes[node.category];
      if (style && style.visible === false) return 'rgba(128, 128, 128, 0.1)';
    }
  
    // 根据当前选择的图谱类型获取对应的调色板
    const specimenType = props.selectedSpecimenType || '矿物标本';
    const palette = specimenColorPalettes[specimenType] || specimenColorPalettes['矿物标本'];

    const category = node.category || '';
  
    // 核心分类
    if (category === 'Category' || category === '分类') return palette.category;
    // 矿物/标本
    if (category === 'Mineral' || category === '中文名称' || category === '矿物' || category === 'Specimen' || category === '标本') return palette.mineral;
    // 颜色
    if (category === 'Color' || category === '颜色') return palette.color;
    // 产地
    if (category === 'Location' || category === '产地') return palette.location;
    // 化学式
    if (category === 'Formula' || category === '化学方程式') return palette.formula;
    // 年份
    if (category === 'Year' || category === '年份') return palette.year;
  
    // 自定义配置兜底
    if (props.styleConfig?.nodes && node.category) {
      const style = props.styleConfig.nodes[node.category];
      if (style && style.color) return style.color;
    }
  
    return '#4facfe'; // 默认
  }

  // 创建渐变shader材质（用于构造标本的渐变色节点）
  function createGradientMaterial(colorArray, opacity = 1.0, isCategory = false) {
    const color1 = new THREE.Color(colorArray[0]);
    const color2 = new THREE.Color(colorArray[1]);
    
    const vertexShader = `
      varying vec3 vWorldPosition;
      varying vec3 vNormal;
      varying vec3 vPosition;
      
      void main() {
        vec4 worldPosition = modelMatrix * vec4(position, 1.0);
        vWorldPosition = worldPosition.xyz;
        vNormal = normalize(normalMatrix * normal);
        vPosition = position;
        gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
      }
    `;
    
    const fragmentShader = `
      uniform vec3 color1;
      uniform vec3 color2;
      uniform float opacity;
      uniform bool isCategory;
      varying vec3 vWorldPosition;
      varying vec3 vNormal;
      varying vec3 vPosition;
      
      void main() {
        // 基于法线的Y分量和位置创建从顶部到底部的渐变
        // 使用球面坐标创建更自然的渐变效果
        float yFactor = (vNormal.y + 1.0) * 0.5;
        
        // 添加径向渐变效果（从中心到边缘）
        float radialFactor = length(vPosition) / 1.0;
        radialFactor = smoothstep(0.0, 1.0, radialFactor);
        
        // 组合渐变因子，让渐变更明显
        float gradientFactor = mix(yFactor, radialFactor, 0.3);
        
        // 分类节点使用更强的渐变对比度
        if (isCategory) {
          gradientFactor = smoothstep(0.2, 0.8, gradientFactor);
        }
        
        // 混合两种颜色，使用smoothstep让过渡更平滑
        vec3 finalColor = mix(color2, color1, gradientFactor);
        
        // 分类节点增加一些发光效果
        if (isCategory) {
          float glow = pow(1.0 - abs(vNormal.y), 2.0) * 0.2;
          finalColor += glow * color1;
        }
        
        gl_FragColor = vec4(finalColor, opacity);
      }
    `;
    
    return new THREE.ShaderMaterial({
      uniforms: {
        color1: { value: color1 },
        color2: { value: color2 },
        opacity: { value: opacity },
        isCategory: { value: isCategory }
      },
      vertexShader: vertexShader,
      fragmentShader: fragmentShader,
      transparent: true,
      side: THREE.DoubleSide
    });
  }
  
  // 2. 节点大小逻辑：为不同类型节点设置不同大小
  function getNodeSize(node) {
    if (props.styleConfig?.nodes && node.category) {
      const style = props.styleConfig.nodes[node.category];
      if (style && style.visible === false) return 0;
    }
  
    const category = node.category || '';
  
    // 分类节点：根据层级设置大小（最大）
    if (category === 'Category' || category === '分类') {
      const level = node.properties?.level ?? node.level ?? 0;
      const sizeMap = {
        0: 90,
        1: 62,
        2: 42,
        3: 30,
        4: 24,
        5: 20
      };
      return sizeMap[level] || 18;
    }
  
    // 矿物/标本节点：较大（次大）
    if (category === 'Mineral' || category === '中文名称' || category === '矿物' || category === 'Specimen' || category === '标本') {
      return 22;
    }
  
    // 颜色、产地、年份、化学式节点：中等大小（确保可见）
    if (category === 'Color' || category === '颜色') return 20;
    if (category === 'Location' || category === '产地') return 20;
    if (category === 'Year' || category === '年份') return 20;
    if (category === 'Formula' || category === '化学方程式') return 20;
  
    return 18; // 其他节点默认大小
  }
  
  // 获取标签文本
  function getNodeLabelText(node) {
    if (props.styleConfig?.nodes && node.category) {
      const style = props.styleConfig.nodes[node.category];
      if (style && style.visible === false) return '';
      if (style && style.labelFormatter) {
        const label = style.labelFormatter(node);
        if (label) return label;
      }
    }
  
    const category = node.category || '';
    if (category === 'Category' || category === '分类') return node.name || node.properties?.name || node.id || '';
    if (category === 'Formula' || category === '化学方程式') return node.value || node.properties?.value || node.name || '';
    if (category === 'Year' || category === '年份') return node.value || node.properties?.value || node.name || '';
  
    return node.name || node.properties?.name || node.id || '';
  }
  
  // 检查节点是否应该高亮（选中节点或与选中节点相连的节点）
  function isNodeHighlighted(nodeId) {
    if (!selectedNodeId.value) return true; // 没有选中节点时，所有节点都正常显示
    const nodeIdStr = String(nodeId);
    return String(selectedNodeId.value) === nodeIdStr || connectedNodeIds.value.has(nodeIdStr);
  }

  // 3. 修改重点：解决文字遮挡，仅修改了文字位置
  function createNodeObject(node) {
    const size = getNodeSize(node);
    const color = getNodeColor(node);
    const isHighlighted = isNodeHighlighted(node.id);
    const category = node.category || '';
    const isCategory = category === 'Category' || category === '分类';
    const isMineral = category === 'Mineral' || category === '中文名称' || 
                      category === '矿物' || category === 'Specimen' || category === '标本';
    
    // 根据是否高亮设置透明度：高亮的节点完全不透明，其他节点几乎看不见（进一步降低透明度）
    const opacity = isHighlighted ? 1.0 : 0.01;
  
    // 创建球体
    let material;
    // 检查是否为渐变色数组（构造标本使用渐变色）
    if (Array.isArray(color) && color.length === 2) {
      // 使用渐变shader材质，分类节点使用更强的渐变效果
      material = createGradientMaterial(color, opacity, isCategory);
    } else {
      // 使用普通Phong材质
      const colorValue = typeof color === 'string' ? color : (color[0] || '#4facfe');
      material = new THREE.MeshPhongMaterial({
        color: colorValue,
        shininess: 100,
        specular: 0x888888,
        transparent: true,
        opacity: opacity,
        emissive: colorValue,
        emissiveIntensity: isCategory ? 0.6 : 0.4  // 分类节点增加发光强度
      });
    }
    
    const sphere = new THREE.Mesh(
      new THREE.SphereGeometry(size, 32, 32),
      material
    );
  
    // 使用Group来组合球体和可能的标签
    const group = new THREE.Group();
    group.add(sphere);
  
    // 如果是收缩状态的矿物节点，添加数字标签
    if (isMineral) {
      const nodeId = String(node.id);
      // 使用props传入的展开状态（数组格式）
      const expandedSet = new Set(props.expandedMineralNodes || []);
      const isExpanded = expandedSet.has(nodeId);
      
      // 只要矿物节点未展开，就显示子节点数量；展开后不显示数字
      const shouldShowCount = !isExpanded;
      
      if (shouldShowCount) {
        const anyHighlighted = !!selectedNodeId.value;
        // 存在高亮节点且当前节点未高亮时，不显示数字
        if (anyHighlighted && !isHighlighted) {
          // 跳过数字标签
        } else {
        // 获取子节点数量（对象格式）
        const count = props.mineralChildNodesCount?.[nodeId] || 0;
        if (count > 0) {
          try {
            const countText = new SpriteText(count.toString());
            // 纯白色数字，无任何背景和边框，显示在球体内部
            countText.color = '#FFFFFF'; // 纯白色，高对比度
            countText.opacity = isHighlighted ? 1.0 : 0.9; // 高亮时完全不透明，非高亮时稍微透明
            // 移除所有背景和边框
            countText.backgroundColor = false;
            countText.borderColor = false;
            countText.borderWidth = 0;
            // 大幅增加数字大小，确保从球体内部也能清晰可见
            countText.textHeight = Math.max(16, size * 1.0); // 增大到球体直径大小，确保清晰可见
            countText.fontWeight = '900'; // 使用最粗的字体
            countText.fontFace = 'Arial, "Microsoft YaHei"';
            // 数字放在球体内部中心位置，从内部显示出来
            countText.position.set(0, 0, 0); // 放在球体中心
            // 设置渲染顺序，确保数字显示在球体前面
            countText.renderOrder = 999; // 设置较高的渲染顺序，确保数字在球体前面渲染
            // 如果 SpriteText 有 material 属性，设置深度测试
            if (countText.material) {
              countText.material.depthTest = false; // 禁用深度测试，确保数字始终可见
              countText.material.depthWrite = false; // 不写入深度缓冲
            }
            group.add(countText);
          } catch (e) {
            console.warn('创建数字标签失败:', e);
          }
        }
        }
      }
    }
  
    if (props.forceLabelShow === 'off') {
      return group;
    }
  
    const labelText = getNodeLabelText(node);
    if (!labelText) return group;
  
    try {
      // 如果节点不高亮，不创建文字标签（完全隐藏）
      if (!isHighlighted) {
        return group;
      }
      
      const sprite = new SpriteText(labelText);
      // 根据是否高亮设置文字颜色和透明度
      const textColor = getTextColor();
      sprite.color = textColor;
      sprite.opacity = 1.0;
      sprite.backgroundColor = false;
      sprite.borderColor = false;
  
      // --- 优化文字标签布局，减少遮挡 ---
      
      // 减小字体大小，减少遮挡面积
      const baseTextHeight = Math.max(8, size / 2.0);
      sprite.textHeight = baseTextHeight * 1.35; // 从1.35减小到1.2
      
      // 根据节点的3D位置计算偏移方向，让文字标签分散在不同位置
      // 使用节点的x, y, z坐标生成一个伪随机但稳定的偏移方向
      const nodeId = String(node.id || node.identity || 0);
      const hash = nodeId.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0);
      
      // 计算偏移角度（基于节点ID的哈希值，确保同一节点总是使用相同偏移）
      const angle1 = (hash % 360) * Math.PI / 180; // 水平角度
      const angle2 = ((hash * 7) % 180 - 90) * Math.PI / 180; // 垂直角度（-90到90度）
      
      // 计算偏移距离（增加距离以减少遮挡）
      const offsetDistance = size * 1.8 + 6; // 从1.5增加到1.8，并增加基础偏移
      
      // 计算3D偏移位置（球面分布）
      const offsetX = Math.cos(angle2) * Math.cos(angle1) * offsetDistance;
      const offsetY = Math.sin(angle2) * offsetDistance + 2; // 稍微向上偏移
      const offsetZ = Math.cos(angle2) * Math.sin(angle1) * offsetDistance;
      
      sprite.position.set(offsetX, offsetY, offsetZ);
      
      // --- 修改结束 ---
  
      // 高亮时使用更粗的字体（extra bold）
      sprite.fontWeight = '900';
      sprite.fontFace = 'Arial, "Microsoft YaHei"';
  
      group.add(sprite);
      return group;
    } catch (e) {
      return group;
    }
  }
  
// 背景色：随主题切换
  function getBackgroundColor() {
  return '#0f131f';
  }

  // 根据主题获取文本颜色
  function getTextColor() {
    return '#ffffff';
  }

  // 根据主题获取连线文本颜色
  function getLinkTextColor() {
    return 'rgba(180, 190, 200, 0.9)';
  }

  // 根据主题获取无关连线的颜色（用于隐藏）
  function getDimmedLinkColor() {
    return '#000000';
  }

// 将 link 的 source/target 引用解析为节点对象
function resolveNodeRef(nodeRef) {
  if (!nodeRef) return null;
  if (typeof nodeRef === 'object') return nodeRef;
  const data = graphInstance?.graphData?.();
  return data?.nodes?.find(n => String(n.id) === String(nodeRef)) || null;
}

// 为子节点生成稳定的偏移，确保每次展开位置一致且靠近父节点
function getStableOffset(seedId, radius = 80) {
  let hash = 0;
  for (let i = 0; i < seedId.length; i++) {
    hash = (hash * 31 + seedId.charCodeAt(i)) >>> 0;
  }
  const angle1 = (hash % 360) * (Math.PI / 180);
  const angle2 = ((hash >> 8) % 360) * (Math.PI / 180);
  const r = radius + (hash % 20); // 稍微抖动半径，避免完全重叠
  return {
    x: Math.cos(angle1) * Math.sin(angle2) * r,
    y: Math.sin(angle1) * Math.sin(angle2) * r,
    z: Math.cos(angle2) * r
  };
}

// 为新加入的子节点寻找最邻近的父节点位置
function findClosestParentPosition(nodeId, links, positionMap, nodeLookup) {
  for (const link of links) {
    const sourceId = String(typeof link.source === 'object' ? link.source.id : link.source);
    const targetId = String(typeof link.target === 'object' ? link.target.id : link.target);
    const sourceNode = nodeLookup.get(sourceId);
    const targetNode = nodeLookup.get(targetId);

    if (targetId === nodeId && sourceNode && isMineralCategory(sourceNode.category)) {
      const pos = positionMap.get(sourceId);
      if (pos) return pos;
    }
    if (sourceId === nodeId && targetNode && isMineralCategory(targetNode.category)) {
      const pos = positionMap.get(targetId);
      if (pos) return pos;
    }
  }
  return null;
}

  // 更新与选中节点直接相连的节点ID集合
  function updateConnectedNodes(nodeId) {
    if (!graphInstance || !nodeId) {
      connectedNodeIds.value = new Set();
      return;
    }
    
    const nodeIdStr = String(nodeId);
    const links = graphInstance.graphData().links || [];
    const connected = new Set();
    
    links.forEach(link => {
      const sourceId = String(typeof link.source === 'object' ? link.source.id : link.source);
      const targetId = String(typeof link.target === 'object' ? link.target.id : link.target);
      
      if (sourceId === nodeIdStr) {
        connected.add(targetId);
      } else if (targetId === nodeIdStr) {
        connected.add(sourceId);
      }
    });
    
    connectedNodeIds.value = connected;
  }

  // 计算矿物节点的子节点数量（年份、产地、颜色）
  function getMineralChildNodesCount(mineralNodeId, allNodes, allLinks) {
    const childCategories = ['Year', '年份', 'Location', '产地', 'Color', '颜色'];
    const connectedNodeIds = new Set();
    
    allLinks.forEach(link => {
      const sourceId = String(typeof link.source === 'object' ? link.source.id : link.source);
      const targetId = String(typeof link.target === 'object' ? link.target.id : link.target);
      
      if (sourceId === String(mineralNodeId)) {
        connectedNodeIds.add(targetId);
      } else if (targetId === String(mineralNodeId)) {
        connectedNodeIds.add(sourceId);
      }
    });
    
    let count = 0;
    allNodes.forEach(node => {
      if (connectedNodeIds.has(String(node.id))) {
        const category = node.category || '';
        if (childCategories.includes(category)) {
          count++;
        }
      }
    });
    
    return count;
  }

  // 检查连线是否应该高亮（连接选中节点或与选中节点相连的节点）
  function isLinkHighlighted(link) {
    if (!selectedNodeId.value) return true; // 没有选中节点时，所有连线都正常显示
    
    const sourceId = String(typeof link.source === 'object' ? link.source.id : link.source);
    const targetId = String(typeof link.target === 'object' ? link.target.id : link.target);
    
    // 如果连线的两端都是高亮的节点，则连线也高亮
    const sourceHighlighted = selectedNodeId.value === sourceId || connectedNodeIds.value.has(sourceId);
    const targetHighlighted = selectedNodeId.value === targetId || connectedNodeIds.value.has(targetId);
    
    return sourceHighlighted && targetHighlighted;
  }
  
  function initGraph() {
    if (!containerRef.value) return;
  
    if (graphInstance) {
      graphInstance._destructor();
      graphInstance = null;
    }
  
    // 背景色根据主题变化
    const BG_COLOR = getBackgroundColor();
  
    graphInstance = new ForceGraph3D(containerRef.value)
      .nodeLabel(node => getNodeLabelText(node))
      .nodeThreeObject(node => createNodeObject(node))
      .nodeThreeObjectExtend(false)
      .nodeVal(node => getNodeSize(node))
      .nodeRelSize(1)
  
      // 4. 连线样式：根据是否高亮调整颜色和透明度（降低可见度，突出节点）
      .linkColor(link => {
        const isHighlighted = isLinkHighlighted(link);
        if (!isHighlighted) {
          // 非高亮的连线根据主题使用接近背景色的颜色（自适应隐藏）
          return getDimmedLinkColor();
        }
        
        if (props.styleConfig?.edges && link.name) {
          const style = props.styleConfig.edges[link.name];
          if (style && style.color) return style.color;
        }
        // 使用更浅更淡的颜色，降低连线存在感
        return '#a0a8b0';
      })
      .linkOpacity(link => {
        const isHighlighted = isLinkHighlighted(link);
        // 进一步降低连线透明度，使节点更突出
        if (isHighlighted) {
          return 0.15;  // 从0.3降低到0.15，使连线更淡
        } else {
          return 0.02;
        }
      })
      .linkWidth(link => {
        const isHighlighted = isLinkHighlighted(link);
        // 增粗连线以匹配放大的节点
        return isHighlighted ? 1.3 : 0.6;
      })
  
      // 连线文字
      .linkThreeObjectExtend(true)
      .linkThreeObject(link => {
        const label = link.name || '';
        if (!label) return null;
        if (props.styleConfig?.edges && link.name) {
          const style = props.styleConfig.edges[link.name];
          if (style && style.visible === false) return null;
        }
        
        // 如果连线不高亮，不创建文字标签（完全隐藏）
        const isHighlighted = isLinkHighlighted(link);
        if (!isHighlighted) {
          return null;
        }
        
        // 使用edgeTypeLabels将英文关系类型转换为中文
        const translatedLabel = props.edgeTypeLabels?.[label] || label;
        
        const sprite = new SpriteText(translatedLabel);
        sprite.color = getLinkTextColor();
        sprite.opacity = 0.5;  // 降低连线文字透明度，使其更淡
        // 高亮时连线文字稍微缩小，降低存在感
        sprite.textHeight = 3.5 * 1.2;  // 从1.5降低到1.2
        sprite.fontWeight = '700';  // 从900降低到700，使文字不那么粗
        sprite.backgroundColor = false;
        return sprite;
      })
      .linkPositionUpdate((sprite, { start, end }) => {
        // 如果 sprite 为 null（无关连线不创建文字），直接返回
        if (!sprite) {
          return false;
        }
        const middlePos = Object.assign({}, start, {
          x: start.x + (end.x - start.x) / 2,
          y: start.y + (end.y - start.y) / 2,
          z: start.z + (end.z - start.z) / 2
        });
        Object.assign(sprite.position, middlePos);
        return false;
      })
  
      .linkDirectionalArrowLength(3.5)
      .linkDirectionalArrowRelPos(1)
      .linkDirectionalArrowColor(link => {
        const isHighlighted = isLinkHighlighted(link);
        // 降低箭头颜色亮度，使其更淡，突出节点
        return isHighlighted ? '#a0a8b0' : getDimmedLinkColor();  // 使用更浅的颜色
      })
      // 移除展开连线的流动粒子效果，保持静态线条
      .linkDirectionalParticles(0)
      .linkDirectionalParticleWidth(0)
      .linkDirectionalParticleSpeed(0)
      .linkDirectionalParticleColor(() => getDimmedLinkColor())
  
      .backgroundColor(BG_COLOR)
      .showNavInfo(false)
      .enableNodeDrag(true)
      .onNodeClick(handleNodeClick)
      .onNodeRightClick((node, event) => {})
      .onBackgroundClick(handleBackgroundClick);
  
    // 同步 three.js 清屏色，避免与页面背景有差异
    const renderer = graphInstance.renderer?.();
    if (renderer?.setClearColor) {
      renderer.setClearColor(BG_COLOR, 1);
    }
  
    // 相机位置：默认拉远一些，让初始显示的图谱更适中，无动画
    graphInstance.cameraPosition({ x: 0, y: 0, z: 2000 }, null, 0);
  
    // 灯光
    const ambientLight = new THREE.AmbientLight(0xcccccc, 0.6);
    graphInstance.scene().add(ambientLight);
    const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
    directionalLight.position.set(50, 50, 100);
    graphInstance.scene().add(directionalLight);
  
    // 雾化效果根据主题调整
    const fogDensity = 0.0000001;
    graphInstance.scene().fog = new THREE.FogExp2(BG_COLOR, fogDensity);
  
    if (props.graphData && props.graphData.nodes && props.graphData.nodes.length > 0) {
      updateGraphData();
    }
  }
  
  const { handleNodeClick, handleBackgroundClick } = createNodeClickHandler({
    emit,
    getGraphInstance: () => graphInstance,
    saveCameraState,
    resetCameraToDefault,
    selectedNodeId,
    connectedNodeIds,
    updateConnectedNodes,
  });
  
  function updateGraphData() {
    if (!graphInstance || !props.graphData) return;
  
  // 记录上一帧节点位置，用于局部展开保持稳定
  const prevData = graphInstance.graphData ? graphInstance.graphData() : null;
  previousNodePositions = new Map();
  const prevIds = new Set();
  if (prevData?.nodes) {
    prevData.nodes.forEach(n => {
      const id = String(n.id);
      prevIds.add(id);
      previousNodePositions.set(id, {
        x: n.x,
        y: n.y,
        z: n.z,
        vx: n.vx || 0,
        vy: n.vy || 0,
        vz: n.vz || 0
      });
    });
  }
  
    const nodes = (props.graphData.nodes || []).map(node => ({
      ...node,
      id: String(node.id || node.identity || node.elementId || `node_${Math.random()}`),
      category: node.category || (node.labels && node.labels[0]) || 'Unknown'
    }));
  
    const nodeIdMap = new Set(nodes.map(n => n.id));
  
    const links = (props.graphData.links || []).filter(link => {
      const sourceId = String(typeof link.source === 'object' ? link.source.id : link.source);
      const targetId = String(typeof link.target === 'object' ? link.target.id : link.target);
      return nodeIdMap.has(sourceId) && nodeIdMap.has(targetId);
    }).map(link => ({
      ...link,
      source: String(typeof link.source === 'object' ? link.source.id : link.source),
      target: String(typeof link.target === 'object' ? link.target.id : link.target)
    }));
  
  const newIds = new Set(nodes.map(n => n.id));
  const addedNodes = nodes.filter(n => !prevIds.has(n.id));
  const removedCount = [...prevIds].filter(id => !newIds.has(id)).length;
  const commonCount = nodes.length - addedNodes.length;
  const baseCount = Math.max(prevIds.size, nodes.length, 1);
  const changeRatio = 1 - (commonCount / baseCount);
  const isMajorGraphChange = prevIds.size === 0 || changeRatio > 0.35;
  shouldRunFullLayout = isMajorGraphChange;
  const nodeLookup = new Map(nodes.map(n => [n.id, n]));

  // 为现有节点复用位置，避免全局跳动；新子节点靠近父节点放置
  const positionedNodes = nodes.map(node => {
    const id = String(node.id);
    const saved = previousNodePositions.get(id);
    if (saved) {
      return { ...node, ...saved };
    }

    // 新节点：尝试找到关联的已知父节点位置
    const parentPos = findClosestParentPosition(id, links, previousNodePositions, nodeLookup);
    if (parentPos) {
      const offset = getStableOffset(id, 95);
      return {
        ...node,
        x: parentPos.x + offset.x,
        y: parentPos.y + offset.y,
        z: parentPos.z + offset.z,
        vx: 0, vy: 0, vz: 0
      };
    }

    return node;
  });

  graphInstance.graphData({ nodes: positionedNodes, links });

  // 将已有节点短暂锁定，防止局部操作触发全局位移
  const pinnedNodes = [];
  const currentNodes = graphInstance.graphData()?.nodes || [];
  currentNodes.forEach(n => {
    const saved = previousNodePositions.get(String(n.id));
    if (saved) {
      n.x = saved.x; n.y = saved.y; n.z = saved.z;
      n.vx = 0; n.vy = 0; n.vz = 0;
      n.fx = saved.x; n.fy = saved.y; n.fz = saved.z;
      pinnedNodes.push(n);
    }
  });
  graphInstance.refresh();
  const lockDuration = isMajorGraphChange ? 400 : 1200;
  setTimeout(() => {
    pinnedNodes.forEach(n => { n.fx = n.fy = n.fz = undefined; });
  }, lockDuration);

  // 大幅数据变动时才重置相机 / 选中状态
  if (isMajorGraphChange) {
    selectedNodeId.value = null;
    connectedNodeIds.value = new Set();
    savedCameraState = null;
    nextTick(() => {
      graphInstance.cameraPosition({ x: 0, y: 0, z: 2000 }, null, 0);
    });
  }
    
    // 延迟应用布局，确保数据设置完成且布局已初始化（仅在大幅变动时）
    if (shouldRunFullLayout) {
      requestAnimationFrame(() => {
        setTimeout(() => {
          applyLayoutForces(true);
        }, 50);
      });
    }
  }

  // 当节点数据刚加载进来时，稍后再做一次布局收紧，避免 layout 未初始化
  watch(() => props.graphData, () => {
    if (!shouldRunFullLayout) return;
    // 延时一帧等待 graphData 生效后再收紧
    requestAnimationFrame(() => {
      setTimeout(() => {
        applyLayoutForces(true);
      }, 50);
    });
  });

  // 检测是否是层级关系图谱（主要通过HAS_SUBCATEGORY关系）
  function isHierarchicalGraph(data) {
    if (!data || !data.links || data.links.length === 0) return false;
    
    // 统计HAS_SUBCATEGORY关系的比例
    const hasSubcategoryCount = data.links.filter(link => {
      const linkName = link.name || link.type || '';
      return linkName === 'HAS_SUBCATEGORY' || linkName === '包含子类';
    }).length;
    
    // 如果HAS_SUBCATEGORY关系占比超过30%，认为是层级关系图谱
    const hierarchicalRatio = hasSubcategoryCount / data.links.length;
    return hierarchicalRatio > 0.3;
  }

  // 将布局参数应用到 d3 力导向，确保中心节点与层级球壳清晰
  function applyLayoutForces(forceRun = shouldRunFullLayout) {
    // 小变动（仅展开/收缩）跳过全局力导向，保持稳定
    if (!forceRun) return;
    // 多重防护，避免在 layout 未初始化时调用导致 tick 报错
    if (!graphInstance || typeof graphInstance.d3Force !== 'function') return;
    
    const data = graphInstance.graphData && graphInstance.graphData();
    if (!data || !data.nodes || data.nodes.length === 0) return; // 需要数据驱动布局
    
    // 确保数据已经设置到图形实例中，布局已经初始化
    // 通过尝试访问一个简单的力来检查布局是否就绪
    let layoutReady = false;
    try {
      const testForce = graphInstance.d3Force('charge');
      if (testForce) {
        layoutReady = true;
      }
    } catch (e) {
      // 布局未就绪，延迟重试
      setTimeout(() => applyLayoutForces(forceRun), 100);
      return;
    }
    
    if (!layoutReady) {
      setTimeout(() => applyLayoutForces(forceRun), 100);
      return;
    }

    // 检测是否是层级关系图谱
    const isHierarchical = isHierarchicalGraph(data);
    
    // 如果是层级关系图谱，使用更大的间距参数
    const baseRepulsion = isHierarchical 
      ? (props.layoutConfig?.repulsion ?? 400) * 2.5  // 层级关系图谱：增加2.5倍排斥力
      : (props.layoutConfig?.repulsion ?? 400);       // 其他图谱：保持原值
      
    const baseEdge = isHierarchical
      ? (props.layoutConfig?.edgeLength ?? 160) * 2.0  // 层级关系图谱：增加2倍边长度
      : (props.layoutConfig?.edgeLength ?? 160);       // 其他图谱：保持原值
    
    // 使用 try-catch 包裹所有 d3Force 调用，防止布局未初始化时出错
    try {
      const chargeForce = graphInstance.d3Force('charge');
      if (chargeForce && typeof chargeForce.strength === 'function') {
        chargeForce.strength(node => {
          const level = getNodeLevel(node);
          // 中心层（level=0）排斥力较小，外层排斥力增大，形成更明显的球体
          return -baseRepulsion * (1 + level * 0.2);
        });
      }
    } catch (e) {
      console.warn('设置 charge 力失败:', e);
    }
    
    try {
      const linkForce = graphInstance.d3Force('link');
      if (linkForce && typeof linkForce.distance === 'function') {
        linkForce.distance(link => {
          const sourceNode = typeof link.source === 'object' ? link.source : graphInstance.graphData()?.nodes?.find(n => String(n.id) === String(link.source));
          const targetNode = typeof link.target === 'object' ? link.target : graphInstance.graphData()?.nodes?.find(n => String(n.id) === String(link.target));
          
          const sourceLevel = getNodeLevel(sourceNode);
          const targetLevel = getNodeLevel(targetNode);
          const levelGap = Math.abs(sourceLevel - targetLevel);
          
          // 获取节点的类别
          const sourceCategory = sourceNode?.category || '';
          const targetCategory = targetNode?.category || '';
          
          // 判断是否是分类节点
          const sourceIsCategory = sourceCategory === 'Category' || sourceCategory === '分类';
          const targetIsCategory = targetCategory === 'Category' || targetCategory === '分类';
          
          // 判断是否是矿物节点
          const sourceIsMineral = isMineralCategory(sourceCategory);
          const targetIsMineral = isMineralCategory(targetCategory);
          
          // 计算基础边长度
          let edgeDistance = baseEdge * (1 + levelGap * 0.5);
          
          // 如果是分类-分类或分类-矿物之间的边，缩短长度（减少20%）
          if ((sourceIsCategory && targetIsCategory) || 
              (sourceIsCategory && targetIsMineral) || 
              (sourceIsMineral && targetIsCategory)) {
            edgeDistance = edgeDistance * 0.8;  // 缩短20%
          }
          
          return edgeDistance;
        });
      }
    } catch (e) {
      console.warn('设置 link 力失败:', e);
    }

    // 层级关系图谱使用更强的径向力和更大的间距
    const radialStrength = isHierarchical
      ? (props.layoutConfig?.radialStrength ?? 0.25) * 1.5  // 层级关系图谱：增加1.5倍径向力强度
      : (props.layoutConfig?.radialStrength ?? 0.25);       // 其他图谱：保持原值
    
    // 动态调整径向半径，层级关系图谱使用更大的间距
    const radialBase = isHierarchical ? 120 : (props.layoutConfig?.radialBase ?? 80);
    const radialStep = isHierarchical ? 280 : (props.layoutConfig?.radialStep ?? 180);
    
    try {
      const radialForce = forceRadial(node => {
        const level = Math.max(0, getNodeLevel(node));
        return radialBase + radialStep * level;
      }, 0, 0, 0).strength(radialStrength);
      graphInstance.d3Force('radial', radialForce);
    } catch (e) {
      console.warn('设置 radial 力失败:', e);
    }

    // 延迟一帧再重热，确保 layout 已存在
    requestAnimationFrame(() => {
      try {
        // 再次检查图形实例和方法是否存在
        if (graphInstance && typeof graphInstance.d3ReheatSimulation === 'function') {
          // 检查数据是否仍然存在
          const currentData = graphInstance.graphData && graphInstance.graphData();
          if (currentData && currentData.nodes && currentData.nodes.length > 0) {
            graphInstance.d3ReheatSimulation();
          }
        }
      } catch (e) {
        // 如果仍失败，静默跳过，避免打断动画循环
        console.warn('重热模拟失败:', e);
      }
    });
  }
  
  onMounted(() => {
    nextTick(() => {
      initGraph();
      window.addEventListener('resize', handleResize);
    });
  });
  
  onUnmounted(() => {
    if (graphInstance) {
      graphInstance._destructor();
      graphInstance = null;
    }
    window.removeEventListener('resize', handleResize);
  });
  
  function handleResize() {
    if (graphInstance && containerRef.value) {
      graphInstance.width(containerRef.value.clientWidth);
      graphInstance.height(containerRef.value.clientHeight);
      graphInstance.refresh();
    } else {
      // 当容器还未渲染好时稍后再尝试
      requestAnimationFrame(() => {
        if (graphInstance && containerRef.value) {
          graphInstance.width(containerRef.value.clientWidth);
          graphInstance.height(containerRef.value.clientHeight);
          graphInstance.refresh();
        }
      });
    }
  }
  
  watch(() => props.graphData, updateGraphData, { deep: true });
  
  watch(() => props.styleConfig, () => {
      if(graphInstance) graphInstance.refresh();
  }, { deep: true });
  
  watch(() => props.forceLabelShow, () => {
    if (graphInstance) graphInstance.refresh();
  });

  watch(() => props.layoutConfig, () => {
    // 延迟应用布局配置，确保布局已初始化
    requestAnimationFrame(() => {
      setTimeout(() => {
        applyLayoutForces(true);
      }, 50);
    });
  }, { deep: true });
  
  // 监听主题变化，更新背景色和雾化
  watch(() => document.body.className, () => {
    if (graphInstance) {
      const newBgColor = getBackgroundColor();
      graphInstance.backgroundColor(newBgColor);
      const fogDensity = 0.00035;
      graphInstance.scene().fog = new THREE.FogExp2(newBgColor, fogDensity);
      const renderer = graphInstance.renderer?.();
      if (renderer?.setClearColor) renderer.setClearColor(newBgColor, 1);
      graphInstance.refresh();
    }
  });
  
function refreshGraph() {
  handleResize();
  graphInstance?.refresh();
}

// 旋转图谱（用于手势控制）
function rotateGraph(deltaX, deltaY) {
  if (!graphInstance) return;
  
  const cam = graphInstance.camera();
  const controls = graphInstance.controls?.();
  
  if (!cam || !controls) return;
  
  const { x, y, z } = cam.position;
  const r = Math.sqrt(x * x + y * y + z * z);
  let theta = Math.atan2(x, z);
  let phi = Math.acos(y / r);

  theta -= deltaX * Math.PI;
  phi -= deltaY * Math.PI;
  phi = Math.max(0.1, Math.min(Math.PI - 0.1, phi));

  graphInstance.cameraPosition({
    x: r * Math.sin(phi) * Math.sin(theta),
    y: r * Math.cos(phi),
    z: r * Math.sin(phi) * Math.cos(theta)
  });
}

defineExpose({ adjustZoom, refreshGraph, resetCameraToDefault, rotateGraph, graphInstance: () => graphInstance });
  </script>
  
  <style scoped>
  div {
  background: var(--bg-primary);
  transition: background 0.3s ease;
  }
  </style>