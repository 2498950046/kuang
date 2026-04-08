/**
 * App.vue 轻量工具抽离（尽量保持与原实现一致，降低行为差异风险）
 */

/**
 * 解析 gemsBasicInfo.csv，构建 chineseName -> englishName 的映射。
 * @param {string} gemsBasicInfoCsv
 * @returns {Map<string, string>}
 */
export function parseGemsBasicInfo(gemsBasicInfoCsv) {
  const gemNameMap = new Map();
  if (!gemsBasicInfoCsv) return gemNameMap;

  const lines = gemsBasicInfoCsv.trim().split('\n');
  lines.slice(1).forEach((line) => {
    // 跟原实现保持一致：简单按逗号切分
    const parts = line.split(',');
    if (parts.length >= 3) {
      const chineseName = parts[1];
      const englishName = parts[2];
      gemNameMap.set(chineseName, englishName);
    }
  });

  return gemNameMap;
}

/**
 * 从事件中获取指针 X 坐标（兼容触摸）。
 * @param {any} event
 * @returns {number}
 */
export function getPointerX(event) {
  if (event?.touches && event.touches.length) return event.touches[0].clientX;
  return event?.clientX || 0;
}

// 模块级缓存：避免重复 new Image()，与原 App.vue 的 cache 行为一致
const preloadedImageCache = new Map();

/**
 * 预加载单张图片
 * @param {string} url
 */
export function preloadImage(url) {
  if (!url || preloadedImageCache.has(url)) return;
  if (typeof window === 'undefined') return;
  const img = new Image();
  img.src = url;
  preloadedImageCache.set(url, img);
}

/**
 * 预加载样本图片（bigImages + smallImages）
 * @param {Array<{bigImages?: string[], smallImages?: string[]}>} samples
 */
export function preloadSamplesImages(samples) {
  if (!Array.isArray(samples) || !samples.length) return;
  samples.forEach((s) => {
    const allUrls = [...(s.bigImages || []), ...(s.smallImages || [])];
    allUrls.forEach((u) => preloadImage(u));
  });
}

