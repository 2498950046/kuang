/**
 * 图谱“引擎层”抽离：
 * - 不包含任何 watch / 生命周期
 * - 不依赖 App.vue 的局部变量（通过 deps 注入）
 * - 尽量复刻 App.vue 原有 runQuery/initGraphOnce/initializeStyleConfig 逻辑
 */

export function createGraphEngine(deps) {
  const {
    graphQuery,
    INVALID_VALUES,
    routePath,
    currentView,
    editor,
    rawData,
    tableData,
    styleConfig,
    selectedSpecimenType,
    specimenColorPalettes,
    expandLevel,
    showAllNodesFromStats,
    isLoading,
    viewLoading,
    chartKey,
    bootLoading,
    initializeLevelState,
    handleClearSelect,
    updateGraphDateRange,
    initialQuery,
  } = deps;

  let hasInitializedGraph = false;

  function initializeStyleConfig() {
    const nodeCategories = [...new Set(rawData.nodes.map((n) => n.category))];
    const edgeTypes = [...new Set(rawData.links.map((l) => l.name))];

    const specimenType = selectedSpecimenType.value || '矿物标本';
    const palette = specimenColorPalettes[specimenType] || specimenColorPalettes['矿物标本'];

    const categoryColors = {
      Category: palette.category,
      '分类': palette.category,
      Mineral: palette.mineral,
      '矿物': palette.mineral,
      Specimen: palette.mineral,
      '标本': palette.mineral,
      Color: palette.color,
      '颜色': palette.color,
      Location: palette.location,
      '产地': palette.location,
      Formula: palette.formula,
      '化学方程式': palette.formula,
      Year: palette.year,
      '年份': palette.year,
    };

    const defaultColors = ['#8be9fd', '#50fa7b', '#ff79c6', '#bd93f9', '#ff6e6e', '#f1fa8c'];
    const newNodesConfig = {};
    nodeCategories.forEach((cat, i) => {
      const color = categoryColors[cat] || defaultColors[i % defaultColors.length];
      newNodesConfig[cat] = {
        visible: true,
        color,
        size: 50,
        labelProp: 'name',
        labelFormatter: (n) => n.name,
      };
    });

    styleConfig.nodes = newNodesConfig;

    const newEdgesConfig = {};
    edgeTypes.forEach((type) => {
      newEdgesConfig[type] = {
        visible: true,
        color: '#6272a4',
        width: 1.5,
        labelProp: 'dynamic',
        labelFormatter: (l) =>
          l.properties.relationship ||
          l.properties.relationship_type ||
          l.properties.relationship_to_event ||
          l.properties.relationship_verb ||
          l.properties.role ||
          l.properties.type,
      };
    });
    styleConfig.edges = newEdgesConfig;
  }

  async function runQuery(cypher, fromStats = false) {
    isLoading.value = true;
    editor.visible = false;
    handleClearSelect();

    showAllNodesFromStats.value = fromStats;

    try {
      const result = await graphQuery(cypher);
      if (result?.error) throw new Error(result.error);

      if (result.type === 'graph') {
        const nodes = result.data.nodes || [];
        nodes.forEach((n) => {
          if ((n.category === 'Event' || n.category === 'Battle') && n.properties?.category) {
            n.category = n.properties.category;
          }
          if (n.category === 'Person' && n.properties?.generation) {
            n.category = n.properties.generation;
          }
        });

        // 过滤掉无效值节点
        const filteredNodes = nodes.filter((n) => {
          const name = n.name || n.properties?.name || '';
          const value = n.value || n.properties?.value || '';
          return !INVALID_VALUES.includes(name) && !INVALID_VALUES.includes(value);
        });

        rawData.nodes = filteredNodes;
        rawData.links = result.data.links || [];
        tableData.headers = [];
        tableData.rows = [];
        initializeStyleConfig();

        initializeLevelState(expandLevel.value);
        if (routePath() !== '/qa') {
          currentView.value = 'graph';
        }
        updateGraphDateRange();
      } else {
        tableData.headers = result.data.headers || [];
        tableData.rows = result.data.rows || [];
        rawData.nodes = [];
        rawData.links = [];
        currentView.value = 'table';
      }
    } catch (e) {
      // 保持与原实现一致：只打印，不中断 UI 逻辑
      console.error('查询或处理数据时出错:', e);
    } finally {
      isLoading.value = false;
      viewLoading.value = false;
      chartKey.value++;
      if (bootLoading.value) bootLoading.value = false;
    }
  }

  function initGraphOnce() {
    if (hasInitializedGraph) return;
    hasInitializedGraph = true;

    selectedSpecimenType.value = '矿物标本';
    runQuery(initialQuery);
    updateGraphDateRange();
  }

  return { runQuery, initGraphOnce, initializeStyleConfig };
}

