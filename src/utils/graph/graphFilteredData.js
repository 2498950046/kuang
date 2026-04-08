/**
 * 图谱过滤后的 nodes/links 计算（从 App.vue 抽离）
 *
 * 该函数刻意保持与原实现一致：
 * - side effects：会设置 TimeSliderCurrentView.value
 * - 会在过滤逻辑开始前触发 calculateMineralChildNodesCount()（用于矿物节点子节点数量缓存）
 */

export function computeFilteredData({
  rawData,
  styleConfig,
  expandLevel,
  expandedMineralNodes,
  expandedCategoryNodes,
  showAllNodesFromStats,
  TimeSliderCurrentView,
  currentSelectedRange,
  isMineralCategory,
  isCategoryType,
  isChildCategory,
  normalizeLinkTime,
  calculateMineralChildNodesCount,
}) {
  if (!rawData.nodes || rawData.nodes.length === 0) {
    return { nodes: [], links: [] };
  }

  if (!styleConfig.nodes || Object.keys(styleConfig.nodes).length === 0) {
    return { nodes: rawData.nodes || [], links: rawData.links || [] };
  }

  // 如果是从统计卡片点击触发的查询，显示所有节点，不应用任何过滤
  // 但 styleConfig 保持不变，这样当用户切换标本类型时会恢复只显示分类和矿物节点
  if (showAllNodesFromStats.value) {
    const allNodeIds = new Set(rawData.nodes.map((n) => String(n.id)));
    const allLinks = rawData.links.filter((l) => {
      const sourceId = String(typeof l.source === 'object' ? l.source.id : l.source);
      const targetId = String(typeof l.target === 'object' ? l.target.id : l.target);
      return allNodeIds.has(sourceId) && allNodeIds.has(targetId);
    });
    return { nodes: rawData.nodes, links: allLinks };
  }

  // 该副作用会更新 App.vue 内的矿物子节点计数缓存
  calculateMineralChildNodesCount();

  const hasTimeBasedLinks = (() => {
    const uniqueTimeValues = new Set();
    let hasTime = false;
    rawData.links.forEach((link) => {
      const properties = link.properties || {};
      if (properties.time_start != null) {
        uniqueTimeValues.add(properties.time_start);
        hasTime = true;
      }
      if (properties.time_end != null) {
        uniqueTimeValues.add(properties.time_end);
        hasTime = true;
      }
      if (properties.time_value != null) {
        uniqueTimeValues.add(properties.time_value);
        hasTime = true;
      }
      if (properties.time_period != null) {
        uniqueTimeValues.add(properties.time_period);
        hasTime = true;
      }
    });
    return hasTime && uniqueTimeValues.size > 1;
  })();

  const visibleNodeCategories = Object.keys(styleConfig.nodes).filter((cat) => styleConfig.nodes[cat]?.visible !== false);
  const nodeById = new Map(rawData.nodes.map((n) => [String(n.id), n]));
  const expandedMineralSet = new Set(expandedMineralNodes.value || []);
  const expandedCategorySet = new Set(expandedCategoryNodes.value || []);

  // 构建可见节点ID集合
  const visibleNodeIds = new Set();
  const currentLevel = expandLevel.value;

  // 构建父节点到子节点的映射
  const categoryToMinerals = new Map(); // 分类节点 -> 矿物节点集合
  const mineralToChildren = new Map(); // 矿物节点 -> 子节点集合（年份、颜色、产地）

  rawData.links.forEach((link) => {
    const sourceId = String(typeof link.source === 'object' ? link.source.id : link.source);
    const targetId = String(typeof link.target === 'object' ? link.target.id : link.target);
    const sourceNode = nodeById.get(sourceId);
    const targetNode = nodeById.get(targetId);

    if (!sourceNode || !targetNode) return;

    const sourceCat = sourceNode.category || '';
    const targetCat = targetNode.category || '';

    if ((link.name === 'BELONGS_TO' || link.name === '属于') && isMineralCategory(sourceCat) && isCategoryType(targetCat)) {
      if (!categoryToMinerals.has(targetId)) {
        categoryToMinerals.set(targetId, new Set());
      }
      categoryToMinerals.get(targetId).add(sourceId);
    }

    // FROM_LOCATION, HAS_COLOR, DISCOVERED_IN 关系：矿物 -> 子节点
    const isChildLink = link.name === 'FROM_LOCATION' || link.name === '来自' || link.name === 'HAS_COLOR' || link.name === '具有颜色' || link.name === 'DISCOVERED_IN' || link.name === '发现于';

    if (isChildLink) {
      if (isMineralCategory(sourceCat) && isChildCategory(targetCat)) {
        if (!mineralToChildren.has(sourceId)) {
          mineralToChildren.set(sourceId, new Set());
        }
        mineralToChildren.get(sourceId).add(targetId);
      } else if (isMineralCategory(targetCat) && isChildCategory(sourceCat)) {
        if (!mineralToChildren.has(targetId)) {
          mineralToChildren.set(targetId, new Set());
        }
        mineralToChildren.get(targetId).add(sourceId);
      }
    }
  });

  // 第一步：根据层级添加基础节点
  rawData.nodes.forEach((node) => {
    const category = node.category || '';
    const nodeId = String(node.id);
    const isCategory = isCategoryType(category);
    const isMineral = isMineralCategory(category);
    const isChild = isChildCategory(category);

    // 检查是否在styleConfig中可见
    const isStyleVisible = !node.category || !styleConfig.nodes[node.category] || visibleNodeCategories.includes(node.category);
    if (!isStyleVisible) return;

    // 1级：初始状态只显示分类节点，但双击展开的分类节点的子节点（矿物节点）也会显示
    // 双击矿物节点可以展开/收缩其子节点（颜色、产地、年份）
    if (currentLevel === 1) {
      if (isCategory) {
        visibleNodeIds.add(nodeId);
      } else if (isMineral) {
        // 检查该矿物节点是否属于已展开的分类节点（通过双击操作展开的）
        let shouldShow = false;
        for (const [categoryId, mineralIds] of categoryToMinerals.entries()) {
          if (mineralIds.has(nodeId) && expandedCategorySet.has(categoryId)) {
            shouldShow = true;
            break;
          }
        }
        if (shouldShow) {
          visibleNodeIds.add(nodeId);
        }
      } else if (isChild) {
        // 子节点（年份、颜色、产地）：只有当其父矿物节点展开时才显示
        let shouldShow = false;
        for (const [mineralId, childIds] of mineralToChildren.entries()) {
          if (childIds.has(nodeId) && expandedMineralSet.has(mineralId)) {
            // 还需要检查该矿物节点是否属于已展开的分类节点
            let mineralBelongsToExpandedCategory = false;
            for (const [categoryId, mineralIds] of categoryToMinerals.entries()) {
              if (mineralIds.has(mineralId) && expandedCategorySet.has(categoryId)) {
                mineralBelongsToExpandedCategory = true;
                break;
              }
            }
            if (mineralBelongsToExpandedCategory) {
              shouldShow = true;
              break;
            }
          }
        }
        if (shouldShow) {
          visibleNodeIds.add(nodeId);
        }
      }
    }
    // 2级：初始状态显示分类节点和矿物节点，双击操作可以展开/收缩
    else if (currentLevel === 2) {
      if (isCategory) {
        visibleNodeIds.add(nodeId);
      } else if (isMineral) {
        let shouldShow = true;
        const allCategoriesExpanded = rawData.nodes.filter((n) => isCategoryType(n.category)).length === expandedCategorySet.size;
        if (!allCategoriesExpanded) {
          // 有分类节点被收缩，只显示属于已展开分类节点的矿物节点
          shouldShow = false;
          for (const [categoryId, mineralIds] of categoryToMinerals.entries()) {
            if (mineralIds.has(nodeId) && expandedCategorySet.has(categoryId)) {
              shouldShow = true;
              break;
            }
          }
          // 如果没有找到父分类（可能是数据问题），默认显示
          if (!shouldShow) {
            let hasParent = false;
            for (const [categoryId, mineralIds] of categoryToMinerals.entries()) {
              if (mineralIds.has(nodeId)) {
                hasParent = true;
                break;
              }
            }
            if (!hasParent) {
              shouldShow = true;
            }
          }
        }
        if (shouldShow) {
          visibleNodeIds.add(nodeId);
        }
      }
    }
    // 3级：初始状态显示所有节点，双击操作可以展开/收缩
    else if (currentLevel === 3) {
      if (isCategory) {
        visibleNodeIds.add(nodeId);
      } else if (isMineral) {
        // 检查该矿物节点是否属于已展开的分类节点
        // 初始状态：所有分类节点都展开，所以所有矿物节点都显示
        // 双击操作后：只有属于已展开分类节点的矿物节点才显示
        let shouldShow = true;
        const allCategoriesExpanded = rawData.nodes.filter((n) => isCategoryType(n.category)).length === expandedCategorySet.size;
        if (!allCategoriesExpanded) {
          // 有分类节点被收缩，只显示属于已展开分类节点的矿物节点
          shouldShow = false;
          for (const [categoryId, mineralIds] of categoryToMinerals.entries()) {
            if (mineralIds.has(nodeId) && expandedCategorySet.has(categoryId)) {
              shouldShow = true;
              break;
            }
          }
          // 如果没有找到父分类（可能是数据问题），默认显示
          if (!shouldShow) {
            let hasParent = false;
            for (const [categoryId, mineralIds] of categoryToMinerals.entries()) {
              if (mineralIds.has(nodeId)) {
                hasParent = true;
                break;
              }
            }
            if (!hasParent) {
              shouldShow = true;
            }
          }
        }
        if (shouldShow) {
          visibleNodeIds.add(nodeId);
        }
      } else if (isChild) {
        // 子节点（年份、颜色、产地）：只有当其父矿物节点展开时才显示
        // 初始状态：所有矿物节点都展开，所以所有子节点都显示
        // 双击操作后：只有父矿物节点展开的子节点才显示
        let shouldShow = true;
        const allMineralsExpanded =
          rawData.nodes.filter((n) => isMineralCategory(n.category)).length === expandedMineralSet.size;
        if (!allMineralsExpanded) {
          // 有矿物节点被收缩，只显示属于已展开矿物节点的子节点
          shouldShow = false;
          for (const [mineralId, childIds] of mineralToChildren.entries()) {
            if (childIds.has(nodeId) && expandedMineralSet.has(mineralId)) {
              shouldShow = true;
              break;
            }
          }
        }
        if (shouldShow) {
          visibleNodeIds.add(nodeId);
        }
      }
    }
  });

  // 第二步：对于2级，已展开的矿物节点的子节点也要显示
  if (currentLevel === 2) {
    expandedMineralSet.forEach((expandedNodeId) => {
      const childNodes = mineralToChildren.get(expandedNodeId);
      if (childNodes) {
        childNodes.forEach((childId) => {
          const childNode = nodeById.get(childId);
          if (childNode && isChildCategory(childNode.category)) {
            if (!childNode.category || !styleConfig.nodes[childNode.category] || visibleNodeCategories.includes(childNode.category)) {
              visibleNodeIds.add(childId);
            }
          }
        });
      }
    });
  }

  let finalNodes = [];
  let finalLinks = [];

  if (hasTimeBasedLinks) {
    TimeSliderCurrentView.value = true;
    const [rangeStart, rangeEnd] = currentSelectedRange.value;

    const timeBasedLinks = [];
    const nonTimeBasedLinks = [];

    rawData.links.forEach((link) => {
      const properties = link.properties || {};
      if (properties.time_start || properties.time_end || properties.time_value || properties.time_period) {
        timeBasedLinks.push(link);
      } else {
        nonTimeBasedLinks.push(link);
      }
    });

    const filteredTimeBasedLinks = timeBasedLinks.filter((link) => {
      const [linkStart, linkEnd] = normalizeLinkTime(link);
      return linkStart <= rangeEnd && linkEnd >= rangeStart;
    });

    const combinedLinks = [...filteredTimeBasedLinks, ...nonTimeBasedLinks];

    // 时间过滤后的可见节点
    const visibleNodeIdsAfterTimeFilter = new Set();
    combinedLinks.forEach((link) => {
      const sourceId = String(typeof link.source === 'object' ? link.source.id : link.source);
      const targetId = String(typeof link.target === 'object' ? link.target.id : link.target);
      if (visibleNodeIds.has(sourceId)) {
        visibleNodeIdsAfterTimeFilter.add(sourceId);
      }
      if (visibleNodeIds.has(targetId)) {
        visibleNodeIdsAfterTimeFilter.add(targetId);
      }
    });

    finalNodes = rawData.nodes.filter((n) => {
      const nodeId = String(n.id);
      const inTimeFilter = visibleNodeIdsAfterTimeFilter.has(nodeId);
      if (!inTimeFilter) return false;
      return visibleNodeIds.has(nodeId);
    });

    const finalNodeIds = new Set(finalNodes.map((n) => String(n.id)));

    finalLinks = combinedLinks.filter((l) => {
      const sourceId = String(typeof l.source === 'object' ? l.source.id : l.source);
      const targetId = String(typeof l.target === 'object' ? l.target.id : l.target);
      if (!finalNodeIds.has(sourceId) || !finalNodeIds.has(targetId)) return false;
      if (styleConfig.edges[l.name]?.visible === false) return false;

      // 【收缩式交互规则】根据展开状态过滤连线
      const sourceNode = nodeById.get(sourceId);
      const targetNode = nodeById.get(targetId);
      const sourceCat = sourceNode?.category || '';
      const targetCat = targetNode?.category || '';

      const sourceIsMineral = isMineralCategory(sourceCat);
      const targetIsMineral = isMineralCategory(targetCat);
      const sourceIsCategory = isCategoryType(sourceCat);
      const targetIsCategory = isCategoryType(targetCat);
      const sourceIsChild = isChildCategory(sourceCat);
      const targetIsChild = isChildCategory(targetCat);

      // 父(分类) → 子(矿物) 方向 (BELONGS_TO)
      if (targetIsCategory && sourceIsMineral && (l.name === 'BELONGS_TO' || l.name === '属于')) {
        if (expandedCategorySet.size > 0 && !expandedCategorySet.has(targetId)) return false;
      }
      if (sourceIsCategory && targetIsMineral && (l.name === 'BELONGS_TO' || l.name === '属于')) {
        if (expandedCategorySet.size > 0 && !expandedCategorySet.has(sourceId)) return false;
      }

      // 父(矿物) → 子(年份/产地/颜色) 方向
      if (sourceIsMineral && targetIsChild) {
        if (expandedMineralSet.size > 0 && !expandedMineralSet.has(sourceId)) return false;
      }
      if (targetIsMineral && sourceIsChild) {
        if (expandedMineralSet.size > 0 && !expandedMineralSet.has(targetId)) return false;
      }

      return true;
    });
  } else {
    TimeSliderCurrentView.value = false;
    finalNodes = rawData.nodes.filter((n) => {
      return visibleNodeIds.has(String(n.id));
    });

    const finalNodeIds = new Set(finalNodes.map((n) => String(n.id)));

    finalLinks = rawData.links.filter((l) => {
      const sourceId = String(typeof l.source === 'object' ? l.source.id : l.source);
      const targetId = String(typeof l.target === 'object' ? l.target.id : l.target);
      if (!finalNodeIds.has(sourceId) || !finalNodeIds.has(targetId)) return false;
      if (styleConfig.edges[l.name]?.visible === false) return false;

      // 【收缩式交互规则】根据展开状态过滤连线
      const sourceNode = nodeById.get(sourceId);
      const targetNode = nodeById.get(targetId);
      const sourceCat = sourceNode?.category || '';
      const targetCat = targetNode?.category || '';

      const sourceIsMineral = isMineralCategory(sourceCat);
      const targetIsMineral = isMineralCategory(targetCat);
      const sourceIsCategory = isCategoryType(sourceCat);
      const targetIsCategory = isCategoryType(targetCat);
      const sourceIsChild = isChildCategory(sourceCat);
      const targetIsChild = isChildCategory(targetCat);

      // 父(分类) → 子(矿物) 方向 (BELONGS_TO)
      if (targetIsCategory && sourceIsMineral && (l.name === 'BELONGS_TO' || l.name === '属于')) {
        if (expandedCategorySet.size > 0 && !expandedCategorySet.has(targetId)) return false;
      }
      if (sourceIsCategory && targetIsMineral && (l.name === 'BELONGS_TO' || l.name === '属于')) {
        if (expandedCategorySet.size > 0 && !expandedCategorySet.has(sourceId)) return false;
      }

      // 父(矿物) → 子(年份/产地/颜色) 方向
      if (sourceIsMineral && targetIsChild) {
        if (expandedMineralSet.size > 0 && !expandedMineralSet.has(sourceId)) return false;
      }
      if (targetIsMineral && sourceIsChild) {
        if (expandedMineralSet.size > 0 && !expandedMineralSet.has(targetId)) return false;
      }

      return true;
    });
  }

  return { nodes: finalNodes, links: finalLinks };
}

