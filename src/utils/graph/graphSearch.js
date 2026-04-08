/**
 * 图谱搜索相关逻辑（从 App.vue 抽离）
 *
 * 返回：
 * - handleSearch(keyword)
 *
 * 该模块保持原行为：
 * - 支持缓存（searchCache）
 * - 支持 loading 并忽略并发
 * - NL2Cypher -> 解析 nodes/links -> rawData 写回 -> initializeStyleConfig -> currentView 切换
 */

export function createGraphSearchHandlers({
  nl2cypher,
  rawData,
  initializeStyleConfig,
  currentView,
  searchKeyword,
  searchType,
  searchLoading,
  searchCache,
  searchHistory,
}) {
  function applySearchResult(graphData) {
    rawData.nodes = graphData.nodes;
    rawData.links = graphData.links;
    initializeStyleConfig();
    currentView.value = 'graph';
  }

  function updateSearchHistory(searchTerm) {
    const historyItem = {
      term: searchTerm,
      type: searchType.value,
      timestamp: Date.now(),
    };

    // 移除重复的历史记录
    searchHistory.value = searchHistory.value.filter((item) => !(item.term === searchTerm && item.type === searchType.value));

    // 添加到历史开头
    searchHistory.value.unshift(historyItem);

    // 限制历史记录数量
    if (searchHistory.value.length > 10) {
      searchHistory.value = searchHistory.value.slice(0, 10);
    }
  }

  // 优化的搜索函数，支持缓存和加载状态
  function handleSearch(keyword) {
    const searchTerm = keyword?.trim() || searchKeyword.value.trim();
    if (!searchTerm) {
      return;
    }

    // 检查缓存
    const cacheKey = `${searchType.value}:${searchTerm}`;
    if (searchCache.value.has(cacheKey)) {
      console.log('使用缓存的搜索结果');
      const cachedData = searchCache.value.get(cacheKey);
      applySearchResult(cachedData);
      // 更新搜索历史
      updateSearchHistory(searchTerm);
      return;
    }

    // 如果正在搜索，忽略新的请求
    if (searchLoading.value) {
      console.log('搜索正在进行中，忽略新请求');
      return;
    }

    searchLoading.value = true;

    // 使用方式二：自然语言 -> Cypher 接口进行搜索
    // 根据搜索范围给模型一个简单前缀提示，提升生成 Cypher 的准确性
    let questionPrefix = '';
    switch (searchType.value) {
      case 'location':
        questionPrefix = '按产地搜索矿物：';
        break;
      default:
        questionPrefix = '按名称搜索矿物：';
    }

    const question = `${questionPrefix}${searchTerm}`;

    nl2cypher(question)
      .then((res) => {
        console.log('搜索框 NL2Cypher 响应:', res);

        const success = res?.success === true;
        if (!success || !res?.result) {
          console.warn('NL2Cypher 未返回有效结果，将保持当前视图。', res);
          return;
        }

        // 与 AIChat 中相同的解析逻辑：兼容多种返回结构
        let graphData = null;
        // 优先从 res.result.data 中获取图数据
        if (res.result?.data) {
          graphData = res.result.data;
        }
        // 兼容 res.result 直接包含 nodes/links 的情况
        else if (res.result?.nodes || res.result?.links) {
          graphData = res.result;
        }
        // 如果以上都不匹配，尝试将 res.result 整个作为 graphData
        else {
          graphData = res.result;
        }

        if (graphData?.nodes && graphData?.links) {
          // 缓存搜索结果
          searchCache.value.set(cacheKey, graphData);
          // 限制缓存大小，避免内存泄漏
          if (searchCache.value.size > 20) {
            const firstKey = searchCache.value.keys().next().value;
            searchCache.value.delete(firstKey);
          }

          applySearchResult(graphData);
          updateSearchHistory(searchTerm);
        } else {
          console.warn('NL2Cypher 结果中没有图数据（nodes/links），将保持当前视图。', res);
        }
      })
      .catch((err) => {
        console.error('调用 /ai/nl2cypher 失败：', err);
      })
      .finally(() => {
        searchLoading.value = false;
      });
  }

  return { handleSearch };
}

