/**
 * 图谱展开层级状态维护（抽离自 App.vue）
 * - initExpandedState：根据 expandLevel 初始化 expandedCategoryNodes/expandedMineralNodes
 * - autoExpandMineralNodesInResult：基于当前 rawData 自动展开矿物节点
 *
 * 约定：本文件不直接操作 Vue ref，只返回 Set/对象，由 App.vue 赋值。
 */

export function initExpandedState({ nodes, level, isCategoryType, isMineralCategory }) {
  if (!nodes?.length) return null;

  const expandedCategoryNodes = new Set();
  const expandedMineralNodes = new Set();

  if (level === 1) {
    // level=1：仅显示分类以外的内容不打开（expanded* 保持空集）
    return { expandedCategoryNodes, expandedMineralNodes };
  }

  // 展开所有分类节点（2级和3级都需要）
  nodes.forEach((node) => {
    if (isCategoryType?.(node.category)) {
      expandedCategoryNodes.add(String(node.id));
    }
  });

  // 3级：展开所有矿物节点
  if (level === 3) {
    nodes.forEach((node) => {
      if (isMineralCategory?.(node.category)) {
        expandedMineralNodes.add(String(node.id));
      }
    });
  }

  return { expandedCategoryNodes, expandedMineralNodes };
}

export function computeAutoExpandMineralNodesInResult({
  nodes,
  links,
  isMineralCategory,
  isChildCategory,
}) {
  try {
    if (!Array.isArray(links)) {
      throw new Error('rawData.links is not an array');
    }

    const nodeById = new Map((nodes || []).map((n) => [String(n.id), n]));
    const mineralsToExpand = new Set();

    links.forEach((link) => {
      const sourceId = String(typeof link.source === 'object' ? link.source.id : link.source);
      const targetId = String(typeof link.target === 'object' ? link.target.id : link.target);
      const sourceNode = nodeById.get(sourceId);
      const targetNode = nodeById.get(targetId);

      if (!sourceNode || !targetNode) return;

      if (isMineralCategory?.(sourceNode.category) && isChildCategory?.(targetNode.category)) {
        mineralsToExpand.add(sourceId);
      }
      if (isMineralCategory?.(targetNode.category) && isChildCategory?.(sourceNode.category)) {
        mineralsToExpand.add(targetId);
      }
    });

    return mineralsToExpand;
  } catch (e) {
    console.warn('自动展开矿物子节点失败：', e);
    return null;
  }
}

