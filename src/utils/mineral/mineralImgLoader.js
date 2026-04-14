// /**
//  * 矿物图片按需加载：仅在被动态 import 时才会执行，主包不包含本模块，刷新时不加载
//  */
// const mineralImgGlob = import.meta.glob('/mineral_img_data/**/*.{jpg,png,jpeg,gif}');
// const mineralImgGlobB = import.meta.glob('/mineral_img_data/**/*.{jpg,png,jpeg,gif}');
// const mineralImgModules = { ...mineralImgGlob, ...mineralImgGlobB };

// let mineralFolderIndexCache = null;

// export function getMineralFolderIndex() {
//   if (mineralFolderIndexCache) return mineralFolderIndexCache;
//   const folderToPathLists = new Map();
//   for (const path of Object.keys(mineralImgModules)) {
//     const normalizedPath = path.replace(/\\/g, '/');
//     const match = normalizedPath.match(/mineral_img_data\/([^/]+)\//);
//     const folderName = match ? match[1] : (normalizedPath.split('/').find((seg, i, arr) => arr[i - 1] === 'mineral_img_data') || '');
//     if (!folderName) continue;
//     if (!folderToPathLists.has(folderName)) folderToPathLists.set(folderName, []);
//     folderToPathLists.get(folderName).push(path);
//   }
//   mineralFolderIndexCache = folderToPathLists;
//   return mineralFolderIndexCache;
// }

// export async function loadMineralImagesForPaths(pathList) {
//   const urls = await Promise.all(
//     pathList.map((path) => {
//       const fn = mineralImgModules[path];
//       if (!fn || typeof fn !== 'function') return Promise.resolve('');
//       return fn().then((m) => (m && typeof m === 'object' && 'default' in m ? m.default : m)).catch(() => '');
//     })
//   );
//   return urls.filter((u) => typeof u === 'string' && u);
// }


