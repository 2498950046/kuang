import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue';
import { parseMineralDescriptionKVs } from './mineralDescriptionParser.js';
import { getPointerX, preloadSamplesImages } from './mineralAppHelpers.js';

/**
 * 矿物节点“详细信息面板”逻辑（抽离自 App.vue）
 * - 负责：是否展示/面板数据推导/样品轮播与拖拽/宝玉石与刚玉族宝石的图片加载/预加载/相关 watch
 * - 纯粹把 Vue 逻辑从 App.vue 分出去：对外只通过返回值提供给 App.vue/模板
 */
export function useMineralDetailPanelLogic({
  selectedItem,
  rawData,
  selectedSpecimenType,
  styleConfig,
  entityCategoryLabels,
  gemNameMap,
  getMineralInfo,
  getSpecimenDescriptionByTable2Id,
  currentView,
  graphRef,
}) {
  // --- 面板展示判定 ---
  function isMineralNode(node) {
    if (!node) return false;

    const labels = node.labels || [];
    if (Array.isArray(labels)) {
      const hasMineralLabel = labels.some(
        (label) =>
          label.toLowerCase().includes('mineral') ||
          label.toLowerCase().includes('specimen') ||
          label === 'Mineral' ||
          label === 'Specimen',
      );
      if (hasMineralLabel) return true;
    }

    const categoryValue = (node?.category || node?.properties?.category || '').toString().toLowerCase();
    if (
      categoryValue.includes('mineral') ||
      categoryValue.includes('矿物') ||
      categoryValue.includes('specimen') ||
      categoryValue.includes('标本')
    ) {
      return true;
    }

    const categoryLabel = entityCategoryLabels[node?.category] || '';
    if (categoryLabel && (categoryLabel.includes('矿物') || categoryLabel.includes('标本'))) {
      return true;
    }

    return false;
  }

  const isMineralDetailVisible = computed(() => {
    if (!selectedItem.value || selectedItem.value.dataType !== 'node') return false;
    return isMineralNode(selectedItem.value.data);
  });

  const isGemstoneGraph = computed(() => selectedSpecimenType.value === '宝玉石');
  const mineralDetail = computed(() => (isMineralDetailVisible.value ? selectedItem.value.data : null));

  // --- 面板基础视觉/数据 ---
  const mineralBasicInfoFromApi = ref(null);

  const mineralTitleColor = computed(() => {
    const node = selectedItem.value?.data;
    if (!node || !node.category) {
      return getComputedStyle(document.body).getPropertyValue('--text-primary') || '#ffffff';
    }
    const cfg = styleConfig.nodes?.[node.category];
    return cfg?.color || getComputedStyle(document.body).getPropertyValue('--text-primary') || '#ffffff';
  });

  const mineralDetailImage = computed(() => {
    const props = mineralDetail.value?.properties || {};
    return props.image || props.photo || props.thumbnail || '/specimen-placeholder.svg';
  });

  const mineralCategories = computed(() => {
    if (!mineralDetail.value || !rawData.links) return [];

    const mineralId = mineralDetail.value.id;
    const categoryMap = new Map(); // 使用Map存储分类和其深度
    const visited = new Set();

    // 递归查找所有分类层级，记录深度
    function findCategories(nodeId, depth = 0) {
      if (visited.has(nodeId)) return;
      visited.add(nodeId);

      // 查找所有从该节点出发的BELONGS_TO关系（矿物 -> 分类）
      // 同时也查找指向该节点的BELONGS_TO关系（兼容不同的数据格式）
      const belongsToLinks = rawData.links.filter(
        (link) => (link.source === nodeId || link.target === nodeId) && link.name === 'BELONGS_TO',
      );

      for (const link of belongsToLinks) {
        // 确定分类节点的ID：如果source是当前节点，则target是分类；否则source是分类
        const categoryNodeId = link.source === nodeId ? link.target : link.source;
        const categoryNode = rawData.nodes.find((n) => n.id === categoryNodeId);
        if (categoryNode && categoryNode.category === 'Category') {
          const categoryName = categoryNode.name || categoryNode.properties?.name;
          if (categoryName) {
            // 如果已存在，只更新深度（取更小的深度，即更上层的分类）
            if (!categoryMap.has(categoryName) || categoryMap.get(categoryName) > depth) {
              categoryMap.set(categoryName, depth);
            }
            // 继续向上查找（分类也可能属于更上层的分类）
            findCategories(categoryNode.id, depth + 1);
          }
        }
      }

      // 同时查找HAS_SUBCATEGORY关系的反向（如果分类通过HAS_SUBCATEGORY连接到更上层分类）
      const subcategoryLinks = rawData.links.filter((link) => link.target === nodeId && link.name === 'HAS_SUBCATEGORY');

      for (const link of subcategoryLinks) {
        const parentCategoryNode = rawData.nodes.find((n) => n.id === link.source);
        if (parentCategoryNode && parentCategoryNode.category === 'Category') {
          const categoryName = parentCategoryNode.name || parentCategoryNode.properties?.name;
          if (categoryName) {
            // 如果已存在，只更新深度（取更小的深度，即更上层的分类）
            if (!categoryMap.has(categoryName) || categoryMap.get(categoryName) > depth) {
              categoryMap.set(categoryName, depth);
            }
            // 继续向上查找
            findCategories(parentCategoryNode.id, depth + 1);
          }
        }
      }
    }

    findCategories(mineralId);

    // 按照深度排序，深度小的（一级分类）在前，然后反转数组使一级分类在最前面
    const sortedCategories = Array.from(categoryMap.entries())
      .sort((a, b) => a[1] - b[1]) // 按深度升序排序
      .map(([name]) => name); // 只返回分类名称

    // 反转数组，使一级分类（深度小的）在最前面，二级分类紧跟其后
    return sortedCategories.reverse();
  });

  const mineralColors = computed(() => {
    if (!mineralDetail.value || !rawData.links || !rawData.nodes) return [];

    const mineralId = String(mineralDetail.value.id);
    const colors = [];

    // 查找所有HAS_COLOR关系（双向检查）
    for (const link of rawData.links) {
      if (link.name === 'HAS_COLOR') {
        const sourceId = String(typeof link.source === 'object' ? link.source.id : link.source);
        const targetId = String(typeof link.target === 'object' ? link.target.id : link.target);

        // 矿物 -> 颜色 或 颜色 -> 矿物
        if (sourceId === mineralId) {
          const colorNode = rawData.nodes.find((n) => String(n.id) === targetId);
          if (colorNode && (colorNode.category === 'Color' || colorNode.category === '颜色')) {
            const colorName = colorNode.name || colorNode.properties?.name;
            if (colorName && !colors.includes(colorName)) {
              colors.push(colorName);
            }
          }
        } else if (targetId === mineralId) {
          const colorNode = rawData.nodes.find((n) => String(n.id) === sourceId);
          if (colorNode && (colorNode.category === 'Color' || colorNode.category === '颜色')) {
            const colorName = colorNode.name || colorNode.properties?.name;
            if (colorName && !colors.includes(colorName)) {
              colors.push(colorName);
            }
          }
        }
      }
    }

    return colors;
  });

  const mineralLocation = computed(() => {
    if (!mineralDetail.value) return null;

    const props = mineralDetail.value.properties || {};
    // 先从properties中获取
    let location = props.location || props.产地;

    // 如果properties中没有，从图谱关系中获取
    if (!location && rawData.links && rawData.nodes) {
      const mineralId = String(mineralDetail.value.id);

      // 查找所有与矿物相关的产地关系（双向检查）
      for (const link of rawData.links) {
        const sourceId = String(typeof link.source === 'object' ? link.source.id : link.source);
        const targetId = String(typeof link.target === 'object' ? link.target.id : link.target);

        // 检查是否是 FROM_LOCATION 关系
        if (link.name === 'FROM_LOCATION') {
          // 矿物 -> 产地 或 产地 -> 矿物
          if (sourceId === mineralId) {
            const locationNode = rawData.nodes.find((n) => String(n.id) === targetId);
            if (locationNode && (locationNode.category === 'Location' || locationNode.category === '产地')) {
              location = locationNode.name || locationNode.properties?.name;
              break;
            }
          } else if (targetId === mineralId) {
            const locationNode = rawData.nodes.find((n) => String(n.id) === sourceId);
            if (locationNode && (locationNode.category === 'Location' || locationNode.category === '产地')) {
              location = locationNode.name || locationNode.properties?.name;
              break;
            }
          }
        }

        // 检查是否是 DISCOVERED_IN 关系，但目标节点是 Location 类型
        if (link.name === 'DISCOVERED_IN') {
          if (sourceId === mineralId) {
            const targetNode = rawData.nodes.find((n) => String(n.id) === targetId);
            // 如果目标节点是 Location 类型，则这是产地信息
            if (targetNode && (targetNode.category === 'Location' || targetNode.category === '产地')) {
              location = targetNode.name || targetNode.properties?.name;
              break;
            }
          } else if (targetId === mineralId) {
            const sourceNode = rawData.nodes.find((n) => String(n.id) === sourceId);
            // 如果源节点是 Location 类型，则这是产地信息
            if (sourceNode && (sourceNode.category === 'Location' || sourceNode.category === '产地')) {
              location = sourceNode.name || sourceNode.properties?.name;
              break;
            }
          }
        }
      }
    }

    return location;
  });

  const mineralDiscoveryYear = computed(() => {
    if (!mineralDetail.value) return null;

    const props = mineralDetail.value.properties || {};
    // 先从properties中获取
    let year = props.year || props.年份 || props.发现年份 || props.discoveryYear || props.era || props.年代;

    // 如果properties中没有，从图谱关系中获取
    if (!year && rawData.links && rawData.nodes) {
      const mineralId = String(mineralDetail.value.id);

      // 查找所有与矿物相关的年份关系（双向检查）
      for (const link of rawData.links) {
        if (link.name === 'DISCOVERED_IN') {
          const sourceId = String(typeof link.source === 'object' ? link.source.id : link.source);
          const targetId = String(typeof link.target === 'object' ? link.target.id : link.target);

          // 矿物 -> 年份 或 年份 -> 矿物
          if (sourceId === mineralId) {
            const yearNode = rawData.nodes.find((n) => String(n.id) === targetId);
            // 如果目标节点是 Year 类型，则这是年份信息
            if (yearNode && (yearNode.category === 'Year' || yearNode.category === '年份')) {
              year = yearNode.name || yearNode.properties?.name;
              break;
            }
          } else if (targetId === mineralId) {
            const yearNode = rawData.nodes.find((n) => String(n.id) === sourceId);
            // 如果源节点是 Year 类型，则这是年份信息
            if (yearNode && (yearNode.category === 'Year' || yearNode.category === '年份')) {
              year = yearNode.name || yearNode.properties?.name;
              break;
            }
          }
        }
      }
    }

    return year;
  });

  // 基本信息：优先用 API 数据，未返回时用图谱节点数据兜底，保证点击节点时面板有内容
  const mineralBasicInfo = computed(() => {
    if (mineralBasicInfoFromApi.value) return mineralBasicInfoFromApi.value;
    if (!mineralDetail.value) return null;
    const d = mineralDetail.value;
    const props = d.properties || {};
    return {
      name: d.name || props.name || props['中文名称'] || '-',
      color: mineralColors.value?.length ? mineralColors.value.join(', ') : (props.color || props['颜色'] || '-'),
      location: mineralLocation.value || props.location || props['产地'] || '-',
      discoveryYear: mineralDiscoveryYear.value || props['发现年份'] || props.year || '-',
      categories: mineralCategories.value?.length ? mineralCategories.value : [],
    };
  });

  const mineralDescription = computed(() => {
    if (!mineralDetail.value) return '';
    const props = mineralDetail.value.properties || {};
    return props.description || props.描述 || props.desc || '暂无描述';
  });

  // 将“基本描述”按「字段名：内容」拆成键值对，字段名列定宽，内容可多行
  const mineralDescriptionKVs = computed(() => parseMineralDescriptionKVs(mineralDescription.value));

  // --- 样品轮播（宝玉石 + 非宝玉石） ---
  const mineralImgModules = import.meta.glob('/src/assets/mineral_img_data/**/*.{jpg,png,jpeg,gif}', { eager: true });
  let mineralFolderIndexCache = null;

  function getMineralFolderIndex() {
    if (mineralFolderIndexCache) return mineralFolderIndexCache;
    const folderToUrlLists = new Map();
    for (const path of Object.keys(mineralImgModules)) {
      const normalizedPath = path.replace(/\\/g, '/');
      const match = normalizedPath.match(/mineral_img_data\/([^/]+)\//);
      const folderName = match ? match[1] : (normalizedPath.split('/').find((seg, i, arr) => arr[i - 1] === 'mineral_img_data') || '');
      if (!folderName) continue;
      const mod = mineralImgModules[path];
      const url = mod && typeof mod === 'object' && 'default' in mod ? mod.default : mod;
      if (!url || typeof url !== 'string') continue;
      if (!folderToUrlLists.has(folderName)) folderToUrlLists.set(folderName, []);
      folderToUrlLists.get(folderName).push(url);
    }
    mineralFolderIndexCache = folderToUrlLists;
    return mineralFolderIndexCache;
  }

  // 节点首次点击后，将该节点所有样品图片一次性预加载到浏览器缓存中，
  // 避免后续 GS 手势快速切换图片时出现明显卡顿。
  const specimenState = reactive({
    samples: [],
    activeSampleIndex: 0,
    frameIndex: 0,
    viewMode: 'small', // small | big
    dragging: false,
    dragStartX: 0,
    dragAccum: 0,
  });

  const activeSpecimen = computed(() => specimenState.samples[specimenState.activeSampleIndex] || null);
  const specimenViewMode = computed(() => specimenState.viewMode);
  const activeFrameCount = computed(() => {
    const imgs = specimenViewMode.value === 'big' ? activeSpecimen.value?.bigImages : activeSpecimen.value?.smallImages;
    return imgs?.length || 1;
  });

  const specimenFrameIndex = computed(() => Math.min(specimenState.frameIndex, Math.max(activeFrameCount.value - 1, 0)));

  const currentSpecimenImage = computed(() => {
    const imgs = specimenViewMode.value === 'big' ? activeSpecimen.value?.bigImages : activeSpecimen.value?.smallImages;
    if (!imgs || imgs.length === 0) return mineralDetailImage.value;
    const safeIndex = Math.min(specimenState.frameIndex, imgs.length - 1);
    return imgs[safeIndex];
  });

  const specimenDescription = computed(() => activeSpecimen.value?.description || mineralDescription.value);

  const isFullscreen = ref(false);

  function resetSpecimenState() {
    specimenState.samples = [];
    specimenState.activeSampleIndex = 0;
    specimenState.frameIndex = 0;
    specimenState.viewMode = 'small';
    specimenState.dragging = false;
    specimenState.dragStartX = 0;
    specimenState.dragAccum = 0;
  }

  function normalizeSample(sample) {
    const bigImages = (sample?.bigImages || []).filter(Boolean);
    const smallImages = (sample?.smallImages || []).filter(Boolean);
    return {
      sampleName: sample?.sampleName || '',
      description: sample?.description || '',
      bigImages,
      smallImages: smallImages.length ? smallImages : bigImages,
    };
  }

  async function loadSpecimenSamples(name) {
    resetSpecimenState();
    if (!name) return;

    // 特殊处理“刚玉族宝石”
    if (name === '刚玉族宝石') {
      const sapphireEnglishName = gemNameMap.get('蓝宝石');
      const rubyEnglishName = gemNameMap.get('红宝石');

      let allImages = [];
      const modules = import.meta.glob('/src/assets/images/images/**/*.{jpg,png,jpeg,gif}', { eager: true });

      const loadImageList = (enName) => {
        if (!enName) return [];
        const enNameLower = enName.toLowerCase();
        return Object.keys(modules)
          .filter((path) => {
            const pathLower = path.toLowerCase();
            return (
              pathLower.includes(`/images/images/${enNameLower}/`) ||
              pathLower.includes(`/images/images/${enNameLower}/`)
            );
          })
          .map((path) => {
            const module = modules[path];
            return module?.default || module;
          })
          .filter(Boolean);
      };

      if (sapphireEnglishName) allImages = allImages.concat(loadImageList(sapphireEnglishName));
      if (rubyEnglishName) allImages = allImages.concat(loadImageList(rubyEnglishName));

      if (allImages.length > 0) {
        specimenState.samples = [
          {
            sampleName: name,
            description: '',
            bigImages: allImages,
            smallImages: allImages,
          },
        ];
      } else {
        specimenState.samples = [
          {
            sampleName: name,
            description: '暂无图片',
            bigImages: ['/specimen-placeholder.svg'],
            smallImages: ['/specimen-placeholder.svg'],
          },
        ];
      }

      // 刚玉族宝石：节点第一次被点击就预加载所有图片，后续拖动更流畅
      preloadSamplesImages(specimenState.samples);
      return; // 刚玉族宝石处理完毕，直接返回
    }

    // 非刚玉族宝石且为“宝玉石”图谱，使用原有逻辑
    if (selectedSpecimenType.value === '宝玉石') {
      const englishName = gemNameMap.get(name);
      if (!englishName) {
        console.warn(`未在 gemsBasicInfo.csv 中找到 ${name} 的英文名。`);
        specimenState.samples = [
          {
            sampleName: name,
            description: '暂无图片',
            bigImages: ['/specimen-placeholder.svg'],
            smallImages: ['/specimen-placeholder.svg'],
          },
        ];
        return;
      }

      try {
        const modules = import.meta.glob('/src/assets/images/images/**/*.{jpg,png,jpeg,gif}', { eager: true });
        const imageList = Object.keys(modules)
          .filter((path) => {
            const pathLower = path.toLowerCase();
            const enNameLower = englishName.toLowerCase();
            return (
              pathLower.includes(`/images/images/${enNameLower}/`) ||
              pathLower.includes(`/images/images/${enNameLower}/`)
            );
          })
          .map((path) => {
            const module = modules[path];
            return module?.default || module;
          })
          .filter(Boolean);

        if (imageList.length > 0) {
          specimenState.samples = [
            {
              sampleName: name,
              description: '',
              bigImages: imageList,
              smallImages: imageList,
            },
          ];
        } else {
          specimenState.samples = [
            {
              sampleName: name,
              description: '暂无图片',
              bigImages: ['/specimen-placeholder.svg'],
              smallImages: ['/specimen-placeholder.svg'],
            },
          ];
        }

        // 宝玉石图谱：首次点击该矿物节点时，将该矿物的所有样品图片预加载
        preloadSamplesImages(specimenState.samples);
      } catch (e) {
        console.error('加载宝玉石样品图片失败', e);
        specimenState.samples = [
          {
            sampleName: name,
            description: '加载失败',
            bigImages: ['/specimen-placeholder.svg'],
            smallImages: ['/specimen-placeholder.svg'],
          },
        ];
      }
    } else {
      // 非宝玉石图谱：按需加载图片，索引首次点击时再建
      try {
        const nameTrimmed = (name || '').trim();
        const folderIndex = getMineralFolderIndex();
        const matchedFolders = [];

        for (const folderName of folderIndex.keys()) {
          const firstUnderscore = folderName.indexOf('_');
          if (firstUnderscore === -1) continue;

          const idPart = folderName.slice(0, firstUnderscore);
          const namePart = folderName.slice(firstUnderscore + 1).replace(/^_+/, '').trim();
          if (namePart !== nameTrimmed) continue;

          const urlList = folderIndex.get(folderName);
          if (!urlList || urlList.length === 0) continue;

          const folderId = idPart ? parseInt(idPart, 10) : NaN;
          matchedFolders.push({
            folderName,
            folderId: Number.isNaN(folderId) ? null : folderId,
            urlList,
          });
        }

        if (matchedFolders.length > 0) {
          specimenState.samples = matchedFolders.map(() => ({
            sampleName: name,
            description: '',
            bigImages: [],
            smallImages: [],
          }));

          Promise.all(
            matchedFolders.map((mf, i) => {
              const urlList = mf.urlList || [];
              const bigUrlList = urlList.filter((p) => /_big_/i.test(p));
              const smallUrlList = urlList.filter((p) => /_small_/i.test(p));
              const hasBigOrSmall = bigUrlList.length > 0 || smallUrlList.length > 0;

              if (hasBigOrSmall) {
                const bigList = bigUrlList.length ? bigUrlList : urlList;
                const smallList = smallUrlList.length ? smallUrlList : urlList;
                return Promise.resolve({
                  index: i,
                  bigImages: bigList?.length ? bigList : smallList?.length ? smallList : ['/specimen-placeholder.svg'],
                  smallImages: smallList?.length ? smallList : bigList?.length ? bigList : ['/specimen-placeholder.svg'],
                });
              }

              const list = urlList?.length ? urlList : ['/specimen-placeholder.svg'];
              return Promise.resolve({ index: i, bigImages: list, smallImages: list });
            }),
          ).then((results) => {
            results.forEach((r) => {
              if (specimenState.samples[r.index]) {
                specimenState.samples = specimenState.samples.map((s, j) =>
                  j === r.index ? { ...s, bigImages: r.bigImages, smallImages: r.smallImages } : s,
                );
              }
            });
            // 非宝玉石图谱：当所有图片路径解析完毕后，一次性预加载所有样品图片
            preloadSamplesImages(specimenState.samples);
          });

          matchedFolders.forEach(({ folderId }, index) => {
            if (folderId != null) {
              getSpecimenDescriptionByTable2Id(folderId)
                .then((desc) => {
                  if (specimenState.samples[index]) {
                    specimenState.samples = specimenState.samples.map((s, i) =>
                      i === index ? { ...s, description: desc || '' } : s,
                    );
                  }
                })
                .catch(() => {});
            }
          });
        } else {
          specimenState.samples = [
            {
              sampleName: name,
              description: '暂无图片',
              bigImages: ['/specimen-placeholder.svg'],
              smallImages: ['/specimen-placeholder.svg'],
            },
          ];
        }
      } catch (e) {
        console.error('从 mineral_img_data 加载矿物图片失败', e);
        specimenState.samples = [
          {
            sampleName: name,
            description: '加载失败',
            bigImages: ['/specimen-placeholder.svg'],
            smallImages: ['/specimen-placeholder.svg'],
          },
        ];
      }
    }
  }

  function setActiveSample(index) {
    if (!specimenState.samples.length) return;
    const normalized = (index + specimenState.samples.length) % specimenState.samples.length;
    specimenState.activeSampleIndex = normalized;
    specimenState.frameIndex = 0;
  }

  function nextSample() {
    setActiveSample(specimenState.activeSampleIndex + 1);
  }

  function prevSample() {
    setActiveSample(specimenState.activeSampleIndex - 1);
  }

  function changeFrame(step) {
    const count = activeFrameCount.value;
    if (count <= 0) return;
    specimenState.frameIndex = (specimenState.frameIndex + step + count) % count;
  }

  function onImagePointerDown(event) {
    if (!activeSpecimen.value) return;
    specimenState.dragging = true;
    specimenState.dragStartX = getPointerX(event);
    specimenState.dragAccum = 0;
  }

  function onImagePointerMove(event) {
    if (!specimenState.dragging) return;
    const currentX = getPointerX(event);
    const delta = currentX - specimenState.dragStartX;
    specimenState.dragStartX = currentX;
    specimenState.dragAccum += delta;
    const threshold = 6; // px per frame
    while (Math.abs(specimenState.dragAccum) >= threshold) {
      const step = specimenState.dragAccum < 0 ? 1 : -1; // 左滑增加索引，右滑减小
      changeFrame(step);
      specimenState.dragAccum += step * threshold;
    }
  }

  function onImagePointerUp() {
    specimenState.dragging = false;
    specimenState.dragAccum = 0;
  }

  function toggleSpecimenZoom() {
    specimenState.viewMode = specimenState.viewMode === 'big' ? 'small' : 'big';
    specimenState.frameIndex = Math.min(specimenState.frameIndex, activeFrameCount.value - 1);
  }

  // 面板 requestFullscreen 的后续监听（App.vue 里原有逻辑）
  const handleFullscreenChange = () => {
    isFullscreen.value = !!document.fullscreenElement;
  };

  onMounted(() => {
    document.addEventListener('fullscreenchange', handleFullscreenChange);
  });

  onBeforeUnmount(() => {
    document.removeEventListener('fullscreenchange', handleFullscreenChange);
  });

  watch(mineralDetail, (val) => {
    const name = val?.name || val?.properties?.name || val?.properties?.['中文名称'] || '';
    if (!val) {
      mineralBasicInfoFromApi.value = null;
      resetSpecimenState();
      return;
    }
    if (isMineralDetailVisible.value) {
      loadSpecimenSamples(name);
    } else {
      resetSpecimenState();
    }

    // 从 POST /mineral/info 获取基本信息（名称、产地、颜色、发现年份、分类）
    mineralBasicInfoFromApi.value = null;
    getMineralInfo({ mineral_name: name })
      .then((data) => {
        const categories = [
          data['标本分类1-1'],
          data['标本分类1-2'],
          data['标本分类1-3'],
          data['标本分类1-4'],
          data['标本分类2-1'],
          data['标本分类2-2'],
          data['标本分类2-3'],
          data['标本分类2-4'],
          data['标本分类3-1'],
          data['标本分类3-2'],
          data['标本分类3-3'],
          data['标本分类3-4'],
        ].filter(Boolean);
        mineralBasicInfoFromApi.value = {
          name: data['中文名称'] ?? name,
          color: data['颜色'] ?? '-',
          location: data['产地'] ?? '-',
          discoveryYear: data['发现年份'] ?? '-',
          categories,
        };
      })
      .catch(() => {
        mineralBasicInfoFromApi.value = null;
      });
  });

  watch(isMineralDetailVisible, () => {
    if (currentView.value !== 'graph') {
      currentView.value = 'graph';
    }
    nextTick(() => {
      graphRef.value?.refreshGraph?.();
    });
  });

  // 全屏由 MineralDetailPanel 内部处理（点击放大按钮即 requestFullscreen）
  function toggleSpecimenFullscreen() {}

  return {
    isMineralNode,
    isMineralDetailVisible,
    isGemstoneGraph,

    mineralDetail,
    mineralDetailImage,

    mineralTitleColor,
    mineralBasicInfoFromApi,
    mineralCategories,
    mineralColors,
    mineralLocation,
    mineralDiscoveryYear,
    mineralBasicInfo,

    mineralDescription,
    mineralDescriptionKVs,

    specimenState,
    activeSpecimen,
    specimenViewMode,
    activeFrameCount,
    specimenFrameIndex,
    currentSpecimenImage,
    specimenDescription,

    resetSpecimenState,
    loadSpecimenSamples,
    nextSample,
    prevSample,
    changeFrame,
    onImagePointerDown,
    onImagePointerMove,
    onImagePointerUp,
    toggleSpecimenZoom,
    toggleSpecimenFullscreen,
  };
}

