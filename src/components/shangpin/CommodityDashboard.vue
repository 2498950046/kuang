<template>
  <div class="dashboard-content" v-if="gemData">
    <div class="dashboard-header">
      <h3>{{ gemData.name }} <span class="en-name">市场价值深度分析</span></h3>
      <p class="header-desc">AI 根据当前市场数据为您推荐以下 Top3 拍品，点击商品即可查看专属价格走势。</p>
    </div>

    <div class="recommendations-row">
      <div class="rec-cards">
        <div 
          class="rec-card" 
          v-for="(item, index) in currentItems" 
          :key="index"
          :class="{ 'active-card': activeProductIndex === index }"
          @click="selectProduct(index)"
        >
          <div class="rec-img" :style="{ backgroundImage: `url(${item.img})` }"></div>
          <div class="rec-info">
            <p class="rec-title" :title="item.t">{{ item.t }}</p>
            <p class="rec-price">¥ {{ item.p.toLocaleString() }}</p>
          </div>
          <div class="active-badge" v-if="activeProductIndex === index">查看行情中</div>
        </div>
      </div>
    </div>

    <div class="chart-section" v-if="activeProduct">
      <div class="chart-title">
        <span class="highlight-text">{{ activeProduct.t }}</span> 的历史成交与 AI 预测走势
      </div>
      <div class="chart-container" ref="chartRef"></div>
    </div>
  </div>
  <div v-else class="empty-state">
    正在加载市场数据...
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch, nextTick, computed } from 'vue';
import * as echarts from 'echarts';

const props = defineProps({
  gemData: { type: Object, required: true, default: () => null }
});

const currentItems = ref([]);
const currentTrend = ref('up');
const activeProductIndex = ref(0);
const chartRef = ref(null);
let echartInstance = null;

const activeProduct = computed(() => currentItems.value[activeProductIndex.value]);

// 获取 Bing 动态免防盗链图库
const getImg = (keyword) => `https://tse1.mm.bing.net/th?q=${encodeURIComponent(keyword)}&w=400&h=400&c=7&rs=1`;

const marketDataDB = {
  // --- 贵重宝石篇 ---
  '红宝石': { base: 45000, unit: '/克拉', trend: 'up', items: [{t: '1.02克拉 鸽血红 无烧裸石 (GRS)', p: 52000, img: getImg('鸽血红 红宝石 裸石')}, {t: '18K白金豪华群镶 红宝石女戒', p: 98000, img: getImg('红宝石 戒指 珠宝')}, {t: '复古宫廷风 鸽血红锁骨链', p: 26500, img: getImg('红宝石 项链 高清')}] },
  '蓝宝石': { base: 22000, unit: '/克拉', trend: 'stable', items: [{t: '2.05克拉 皇家蓝 无烧蓝宝石', p: 48000, img: getImg('皇家蓝 蓝宝石 裸石')}, {t: '18K金 戴妃款 矢车菊钻戒', p: 35000, img: getImg('蓝宝石 戴妃 戒指')}, {t: '斯里兰卡 蓝宝石 豪华项链', p: 88000, img: getImg('蓝宝石 吊坠 项链')}] },
  '钻石': { base: 42000, unit: '/克拉', trend: 'down', items: [{t: '1.0克拉 D色 VVS1 3EX 裸钻', p: 56000, img: getImg('钻石 裸钻 GIA')}, {t: 'PT950铂金 经典六爪 50分钻戒', p: 16800, img: getImg('六爪 钻戒 求婚')}, {t: '阿盖尔 粉钻 18K金 群镶戒指', p: 188000, img: getImg('粉钻 戒指 珠宝')}] },
  '金绿宝石': { base: 35000, unit: '/克拉', trend: 'up', items: [{t: '亚历山大变石 强变色 顶级裸石', p: 88000, img: getImg('亚历山大变石 裸石')}, {t: '金绿猫眼 锐利活光 18K金男戒', p: 125000, img: getImg('金绿猫眼 戒指')}, {t: '变石 刻面 钻石群镶吊坠', p: 45000, img: getImg('变石 吊坠 项链')}] },
  '绿柱石族宝石': { base: 38000, unit: '/克拉', trend: 'up', items: [{t: '赞比亚 木木绿 祖母绿裸石', p: 58000, img: getImg('祖母绿 裸石 高清')}, {t: '圣玛利亚色 海蓝宝 满钻女戒', p: 16800, img: getImg('海蓝宝 戒指')}, {t: '天然摩根石 粉色系 原矿', p: 8500, img: getImg('摩根石 吊坠')}] },

  // --- 中高档彩色宝石篇 ---
  '碧玺': { base: 2500, unit: '/克拉', trend: 'up', items: [{t: '卢比来 极品红碧玺 鸽血红 裸石', p: 18500, img: getImg('红碧玺 裸石')}, {t: '巴西天然 西瓜碧玺 雕花挂件', p: 9800, img: getImg('西瓜碧玺 吊坠')}, {t: '帕拉伊巴 霓虹蓝 18K金戒指', p: 128000, img: getImg('帕拉伊巴 戒指')}] },
  '坦桑石': { base: 3500, unit: '/克拉', trend: 'stable', items: [{t: '5A级 皇家蓝 坦桑石裸石', p: 18500, img: getImg('坦桑石 裸石')}, {t: '18K白金 坦桑石伴钻女戒', p: 28900, img: getImg('坦桑石 戒指')}, {t: '水滴形 坦桑石 钻石群镶项链', p: 46800, img: getImg('坦桑石 项链')}] },
  '尖晶石': { base: 12000, unit: '/克拉', trend: 'up', items: [{t: '绝地武士 霓虹粉红 尖晶石裸石', p: 38000, img: getImg('尖晶石 裸石')}, {t: '马亨盖 鲜艳热粉色 18K金钻戒', p: 25000, img: getImg('马亨盖 戒指')}, {t: '坦桑尼亚 天然钴蓝尖晶 吊坠', p: 18000, img: getImg('钴蓝尖晶石 吊坠')}] },
  '石榴石': { base: 800, unit: '/克拉', trend: 'stable', items: [{t: '翠榴石 强火彩 马尾包体 裸石', p: 15000, img: getImg('翠榴石 裸石')}, {t: '沙弗莱 浓艳翠绿 豪华女戒', p: 22000, img: getImg('沙弗莱 戒指')}, {t: '紫牙乌 极品紫红 多圈手链', p: 3500, img: getImg('紫牙乌 手链')}] },
  '托帕石': { base: 200, unit: '/克拉', trend: 'stable', items: [{t: '伦敦蓝 托帕石 10克拉全净裸石', p: 2500, img: getImg('伦敦蓝托帕石 裸石')}, {t: '瑞士蓝 18K金 海蓝之心 戒指', p: 4800, img: getImg('托帕石 戒指')}, {t: '帝国托帕石 金黄色 珍藏级标本', p: 12000, img: getImg('帝国托帕石 裸石')}] },
  '橄榄石': { base: 800, unit: '/克拉', trend: 'stable', items: [{t: '帕敢 天然高净度 橄榄石裸石', p: 3200, img: getImg('橄榄石 裸石')}, {t: '18K金镶嵌 浓绿 碎钻围镶女戒', p: 6800, img: getImg('橄榄石 戒指')}, {t: '陨石提取 橄榄石原石标本', p: 15000, img: getImg('橄榄石 吊坠')}] },
  '锆石': { base: 800, unit: '/克拉', trend: 'stable', items: [{t: '柬埔寨 天然强火彩 蓝锆石', p: 3500, img: getImg('蓝锆石 裸石')}, {t: '高色散 钻石平替 白锆石耳钉', p: 1800, img: getImg('白锆石 耳钉')}, {t: '天然红褐色 锆石 原矿标本', p: 600, img: getImg('红锆石 裸石')}] },
  '堇青石': { base: 500, unit: '/克拉', trend: 'up', items: [{t: '顶级血滴堇青石 强多色性', p: 2800, img: getImg('堇青石 裸石')}, {t: '斯里兰卡 蓝紫罗兰色 手串', p: 1500, img: getImg('堇青石 手串')}, {t: '水光蓝 18K金 堇青石锁骨链', p: 3200, img: getImg('堇青石 项链')}] },
  '磷灰石': { base: 400, unit: '/克拉', trend: 'up', items: [{t: '帕拉伊巴色 霓虹蓝磷灰石', p: 2500, img: getImg('磷灰石 裸石')}, {t: '天然黄绿双色 磷灰石原石', p: 600, img: getImg('磷灰石 原石')}, {t: '18K金镶嵌 磷灰石 满钻锁骨链', p: 4800, img: getImg('磷灰石 项链')}] },
  '红柱石': { base: 500, unit: '/克拉', trend: 'stable', items: [{t: '强多色性 红柱石 十字石 裸石', p: 3200, img: getImg('红柱石 裸石')}, {t: '天然空心十字 红柱石 切片标本', p: 1200, img: getImg('空心十字石')}, {t: '变色龙效应 925银镶嵌戒指', p: 2600, img: getImg('红柱石 戒指')}] },
  '长石族宝石': { base: 300, unit: '/克拉', trend: 'up', items: [{t: '斯里兰卡 顶级蓝光 月光石', p: 1500, img: getImg('月光石 裸石')}, {t: '天然金草莓 太阳石 强光晕手串', p: 2200, img: getImg('太阳石 手串')}, {t: '18K玫瑰金 拉长石复古风戒指', p: 3800, img: getImg('拉长石 戒指')}] },
  '方柱石': { base: 200, unit: '/克拉', trend: 'stable', items: [{t: '罕见紫色 强荧光 方柱石刻面', p: 1200, img: getImg('方柱石 裸石')}, {t: '金黄色 猫眼方柱石 原矿标本', p: 2500, img: getImg('猫眼方柱石')}, {t: '18K白金镶嵌 浅紫色吊坠', p: 3800, img: getImg('方柱石 吊坠')}] },
  '矽线石': { base: 300, unit: '/克拉', trend: 'stable', items: [{t: '稀有 强猫眼效应 矽线石 蛋面', p: 3800, img: getImg('矽线石 猫眼')}, {t: '天然晶体 矽线石 教学标本', p: 800, img: getImg('矽线石 晶体')}, {t: '18K金复古镶嵌 矽线石男戒', p: 5600, img: getImg('矽线石 戒指')}] },
  '辉石': { base: 800, unit: '/克拉', trend: 'stable', items: [{t: '祖母绿平替 铬透辉石 裸石', p: 4500, img: getImg('透辉石 裸石')}, {t: '天然硬玉 辉石族 共生标本', p: 1500, img: getImg('辉石 矿物')}, {t: '星光效应 黑星石 霸气男戒', p: 3800, img: getImg('黑星石 戒指')}] },

  // --- 玉石及特色品种篇 ---
  '翡翠': { base: 85000, unit: '/件(均价)', trend: 'up', items: [{t: '老坑玻璃种 帝王绿 平安扣', p: 450000, img: getImg('帝王绿 翡翠 吊坠')}, {t: '高冰飘绿花 完美无纹裂 手镯', p: 280000, img: getImg('冰种 翡翠 手镯')}, {t: '木那雪花棉 18K金镶钻 福豆', p: 88000, img: getImg('雪花棉 翡翠 吊坠')}] },
  '软玉': { base: 8000, unit: '/克', trend: 'up', items: [{t: '新疆和田玉 籽料 羊脂白玉 把件', p: 280000, img: getImg('羊脂白玉 籽料')}, {t: '且末蓝 糖料 俄碧玉 无事牌', p: 35000, img: getImg('和田玉 碧玉 吊坠')}, {t: '老坑 塔青 细料无结构 手串', p: 12800, img: getImg('和田玉 塔青 手串')}] },
  '独山玉': { base: 12000, unit: '/件(均价)', trend: 'stable', items: [{t: '南阳 独山玉 天蓝底色 雕花手镯', p: 28000, img: getImg('独山玉 手镯')}, {t: '老坑 透水白 名家俏色 山水牌', p: 15000, img: getImg('独山玉 雕件')}, {t: '白天蓝绿 俏色 百鸟朝凤摆件', p: 56000, img: getImg('独山玉 摆件')}] },
  '蛇纹石玉': { base: 1500, unit: '/件(均价)', trend: 'stable', items: [{t: '岫岩玉 180料 极品深绿 手镯', p: 5800, img: getImg('岫玉 手镯')}, {t: '岫岩玉 花玉 巧雕 大型白菜摆件', p: 12800, img: getImg('岫玉 摆件')}, {t: '酒泉玉 仿古龙凤 双面透雕挂件', p: 2500, img: getImg('岫玉 吊坠')}] },
  '钠长石玉': { base: 3000, unit: '/件(均价)', trend: 'stable', items: [{t: '水沫玉 冰种飘蓝花 极似翡翠', p: 8500, img: getImg('水沫玉 手镯')}, {t: '玻璃种 水沫子 饱满起光 戒面', p: 2800, img: getImg('水沫玉 裸石')}, {t: '水沫玉 飘绿丝 弥勒佛 吊坠', p: 4500, img: getImg('水沫玉 吊坠')}] },
  '绿松石': { base: 1500, unit: '/克', trend: 'up', items: [{t: '原矿高瓷 丫角山 果冻蓝 108佛珠', p: 88000, img: getImg('绿松石 108 佛珠')}, {t: '顶级 乌兰花 铁线蜘蛛网 戒指', p: 15000, img: getImg('绿松石 乌兰花 戒指')}, {t: '睡美人 无铁线 纯净天空蓝 吊坠', p: 22000, img: getImg('绿松石 吊坠')}] },
  '青金石': { base: 150, unit: '/克', trend: 'stable', items: [{t: '帝王青 老矿无金无白 圆珠手串', p: 6800, img: getImg('青金石 手串')}, {t: '满金撒金 18K金镶嵌 吊坠', p: 3200, img: getImg('青金石 吊坠')}, {t: '佛教七宝 镇宅大方牌 无事牌', p: 5500, img: getImg('青金石 无事牌')}] },
  '孔雀石': { base: 50, unit: '/克', trend: 'stable', items: [{t: '天然孔雀石 高瓷带眼 平安扣', p: 1200, img: getImg('孔雀石 平安扣')}, {t: '孔雀石 绒毛状晶簇 极品标本', p: 3500, img: getImg('孔雀石 矿物晶体')}, {t: '18K金 梵克雅宝同款 四叶草项链', p: 8500, img: getImg('孔雀石 四叶草')}] },
  '石英质玉石': { base: 200, unit: '/克', trend: 'up', items: [{t: '凉山九口 满肉柿子红 南红玛瑙', p: 8500, img: getImg('南红玛瑙 手串')}, {t: '极品 战国红玛瑙 象形纹理', p: 12000, img: getImg('战国红玛瑙')}, {t: '盐源玛瑙 糖果色 多宝手串', p: 3500, img: getImg('盐源玛瑙 手串')}] },
  '蔷薇辉石': { base: 80, unit: '/克', trend: 'stable', items: [{t: '天然桃花玉 粉糯正圈手镯', p: 3800, img: getImg('桃花玉 手镯')}, {t: '带黑铁线 复古风 银镶嵌吊坠', p: 800, img: getImg('蔷薇辉石 吊坠')}, {t: '原矿半明料 雕刻原料标本', p: 1200, img: getImg('蔷薇辉石 原石')}] },
  '欧泊': { base: 5000, unit: '/克拉', trend: 'up', items: [{t: '澳洲闪电岭 黑欧泊 变彩裸石', p: 25000, img: getImg('黑欧泊 裸石')}, {t: '墨西哥 火欧泊 豪华镶钻戒指', p: 18000, img: getImg('火欧泊 戒指')}, {t: '埃塞俄比亚 水欧泊 极光蓝绿', p: 6800, img: getImg('水欧泊 吊坠')}] },

  // --- 印章石与其他矿物篇 ---
  '寿山石': { base: 1500, unit: '/克', trend: 'up', items: [{t: '极品 田黄石 萝卜丝纹 印章', p: 158000, img: getImg('田黄石 印章')}, {t: '寿山芙蓉石 质地凝结 山水摆件', p: 35000, img: getImg('寿山芙蓉石 摆件')}, {t: '老性 荔枝洞 随形手把件', p: 12000, img: getImg('荔枝洞 寿山石')}] },
  '青田石': { base: 600, unit: '/克', trend: 'up', items: [{t: '封门青 极品微冻 闲章印石', p: 28000, img: getImg('青田石 封门青')}, {t: '灯光冻 名家篆刻 龙纽闲章', p: 56000, img: getImg('青田石 灯光冻')}, {t: '龙蛋石 俏色 山水人物摆件', p: 15000, img: getImg('青田石 摆件')}] },
  '鸡血石': { base: 3500, unit: '/克', trend: 'up', items: [{t: '昌化 极品大红袍 全红冻地', p: 350000, img: getImg('昌化 鸡血石 大红袍')}, {t: '巴林 牛角冻 鲜红血色 摆件', p: 128000, img: getImg('巴林 鸡血石')}, {t: '刘关张三结义 俏色巧雕', p: 88000, img: getImg('鸡血石 雕件')}] },
  '水晶': { base: 150, unit: '/克', trend: 'stable', items: [{t: '乌拉圭 纯天然深紫晶 手链', p: 1200, img: getImg('紫水晶 手链')}, {t: '巴西 金发晶 超七 顺发手串', p: 2800, img: getImg('金发晶 手串')}, {t: '镇宅辟邪 天然紫晶洞 摆件', p: 8500, img: getImg('紫晶洞 摆件')}] },
  '萤石': { base: 100, unit: '/克', trend: 'stable', items: [{t: '天然绿紫双色 萤石八面体', p: 800, img: getImg('萤石 八面体')}, {t: '高冰透 蓝光夜明珠 摆件', p: 3500, img: getImg('萤石 夜明珠')}, {t: '绝美彩虹萤石 小摆件', p: 1200, img: getImg('彩虹萤石')}] },
  '天然玻璃': { base: 200, unit: '/克', trend: 'up', items: [{t: '捷克陨石 纯天然防伪 吊坠', p: 3800, img: getImg('捷克陨石 吊坠')}, {t: '利比亚 黄金陨石 雕刻把件', p: 5600, img: getImg('利比亚陨石')}, {t: '雷公墨 玻璃陨石 镇宅原石', p: 1500, img: getImg('玻璃陨石 雷公墨')}] },

  // --- 有机宝石篇 ---
  '珍珠': { base: 6000, unit: '/颗(均价)', trend: 'up', items: [{t: '澳洲白珠 15mm 极光冷白', p: 12800, img: getImg('澳白 珍珠 项链')}, {t: '大溪地 天然孔雀绿 黑珍珠', p: 8600, img: getImg('大溪地 黑珍珠 戒指')}, {t: '日本Akoya 天女级 塔链', p: 28000, img: getImg('Akoya 天女 珍珠')}] },
  '琥珀': { base: 350, unit: '/克', trend: 'stable', items: [{t: '多米尼加 顶级天空蓝珀 手串', p: 15800, img: getImg('多米尼加 蓝珀')}, {t: '波罗的海 鸡油黄 老蜜蜡', p: 8500, img: getImg('蜜蜡 吊坠')}, {t: '缅甸 远古昆虫 虫珀 原石', p: 22000, img: getImg('虫珀')}] },
  '珊瑚': { base: 1200, unit: '/克', trend: 'up', items: [{t: '日本AKA 阿卡级 牛血红', p: 25000, img: getImg('AKA 珊瑚 戒指')}, {t: 'MOMO 莫莫红 孩儿面 雕件', p: 38000, img: getImg('珊瑚 雕件')}, {t: '沙丁红珊瑚 108颗 佛珠', p: 12000, img: getImg('红珊瑚 手串')}] },
  '象牙': { base: 150, unit: '/克', trend: 'stable', items: [{t: '冰料 猛犸象牙 雕刻观音', p: 18000, img: getImg('猛犸象牙 观音')}, {t: '西伯利亚 蓝皮猛犸 无事牌', p: 4500, img: getImg('猛犸象牙 蓝皮')}, {t: '猛犸象牙 满网纹 手串把件', p: 6800, img: getImg('猛犸象牙 手串')}] },
  '煤精': { base: 60, unit: '/克', trend: 'stable', items: [{t: '辽宁抚顺 纯天然 貔貅把件', p: 2800, img: getImg('煤精 雕件')}, {t: '煤精石 108颗 高抛光念珠', p: 1500, img: getImg('煤精 手串')}, {t: '抚顺双绝 煤精配琥珀 吊坠', p: 4200, img: getImg('煤精 吊坠')}] },
  '硅化木': { base: 3000, unit: '/件(均价)', trend: 'stable', items: [{t: '缅甸 树化玉 冰种透水绿料', p: 15800, img: getImg('树化玉 摆件')}, {t: '玛瑙底 硅化木 风水镇宅', p: 6800, img: getImg('硅化木 原石')}, {t: '木变石 虎睛石 多宝手串', p: 800, img: getImg('虎睛石 手串')}] },
  '贝壳': { base: 500, unit: '/件(均价)', trend: 'stable', items: [{t: '深海 玉化砗磲 全透观音', p: 2800, img: getImg('玉化砗磲 吊坠')}, {t: '天然 粉红女王贝 18K金戒指', p: 5600, img: getImg('女王贝 戒指')}, {t: '金丝砗磲 108颗 藏式佛珠', p: 1500, img: getImg('金丝砗磲 手串')}] },
  '龟甲': { base: 400, unit: '/克', trend: 'stable', items: [{t: '中古老物件 老玳瑁 梳子', p: 18000, img: getImg('老玳瑁 梳子')}, {t: '老玳瑁 仿古圆条手镯 半透明', p: 25000, img: getImg('玳瑁 手镯')}, {t: '古董工艺 龟甲 镶金边眼镜框', p: 8500, img: getImg('玳瑁 眼镜')}] }
};
// 智能推算数据
const getMarketData = (name) => {
  if (marketDataDB[name]) return marketDataDB[name];
  const hash = name.charCodeAt(0) * name.length;
  const base = (hash % 80) * 100 + 800;
  return {
    trend: hash % 3 === 0 ? 'up' : 'stable',
    items: [
      { t: `天然精选 ${name} 裸石 (支持复检)`, p: Math.floor(base * 1.5), img: getImg(`${name} 裸石`) },
      { t: `18K金微镶 经典款 ${name} 戒指`, p: Math.floor(base * 2.8 + 1500), img: getImg(`${name} 戒指`) },
      { t: `复古风 珍藏级 ${name} 吊坠项链`, p: Math.floor(base * 2.2 + 1200), img: getImg(`${name} 项链`) }
    ]
  };
};

// 生成专属图表数据：以该商品的当前价格为衔接点！
const generateChartData = (targetPrice, trend) => {
  const xAxis = [], history = [], predict = [];
  let trendFactor = trend === 'up' ? 0.03 : (trend === 'down' ? -0.02 : 0.005);
  
  // 逆推历史价格：用目标价往回推
  let currentSimPrice = targetPrice / Math.pow((1 + trendFactor), 12); 
  for (let i = 12; i >= 1; i--) {
    xAxis.push(`${i}个月前`);
    const noise = currentSimPrice * (Math.random() * 0.08 - 0.04);
    currentSimPrice = currentSimPrice + (currentSimPrice * trendFactor) + noise;
    history.push(currentSimPrice);
    predict.push(null);
  }
  
  // 衔接点强制设为该商品实际标价
  history[11] = targetPrice;
  predict[11] = targetPrice;
  
  // 预测未来价格
  let currentPredictPrice = targetPrice;
  for (let i = 1; i <= 6; i++) {
    xAxis.push(`未来${i}个月`);
    history.push(null);
    const noise = currentPredictPrice * (Math.random() * 0.04 - 0.02);
    currentPredictPrice = currentPredictPrice + (currentPredictPrice * trendFactor) + noise;
    predict.push(currentPredictPrice);
  }
  return { xAxis, history, predict };
};

const renderChart = () => {
  if (!chartRef.value || !activeProduct.value) return;
  if (!echartInstance) echartInstance = echarts.init(chartRef.value);

  const { xAxis, history, predict } = generateChartData(activeProduct.value.p, currentTrend.value);
  const themeColor = props.gemData.color || '#3B82F6';

  const option = {
    tooltip: { trigger: 'axis', valueFormatter: (val) => '¥ ' + Math.round(val).toLocaleString() },
    legend: { data: ['历史成交价', 'AI 大模型预测趋势'], textStyle: { color: '#cbd5e1' }, top: 0 },
    grid: { left: '3%', right: '4%', bottom: '3%', top: '15%', containLabel: true },
    xAxis: { type: 'category', boundaryGap: false, data: xAxis, axisLabel: { color: '#94a3b8' } },
    yAxis: { type: 'value', axisLabel: { color: '#94a3b8' }, splitLine: { lineStyle: { color: 'rgba(255,255,255,0.05)' } }, scale: true },
    series: [
      {
        name: '历史成交价', type: 'line', data: history, smooth: true,
        itemStyle: { color: themeColor }, lineStyle: { width: 3 },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: themeColor + '90' }, { offset: 1, color: themeColor + '00' }
          ])
        }
      },
      {
        name: 'AI 大模型预测趋势', type: 'line', data: predict, smooth: true,
        itemStyle: { color: '#F59E0B' }, lineStyle: { width: 3, type: 'dashed' }
      }
    ]
  };
  echartInstance.setOption(option);
};

// 选择商品卡片
const selectProduct = (index) => {
  activeProductIndex.value = index;
  nextTick(() => renderChart());
};

watch(
  () => props.gemData,
  (newGem) => {
    if (newGem) {
      const data = getMarketData(newGem.name);
      currentTrend.value = data.trend;
      currentItems.value = data.items;
      selectProduct(0); // 默认选中第一个商品并画图
    }
  },
  { immediate: true, deep: true }
);

const handleResize = () => { if (echartInstance) echartInstance.resize(); };
onMounted(() => window.addEventListener('resize', handleResize));
onBeforeUnmount(() => { window.removeEventListener('resize', handleResize); if (echartInstance) echartInstance.dispose(); });
</script>

<style scoped>
/* src/components/shangpin/CommodityDashboard.vue 的 <style scoped> 替换为以下内容 */

/* 🔥 修改后：新增内部滚动 🔥 */
.dashboard-content { 
  display: flex; 
  flex-direction: column; 
  width: 100%; 
  height: 100%; 
  padding: 24px; 
  box-sizing: border-box;
  color: #e2e8f0; 
  overflow-y: auto; /* 允许内部上下滚动 */
  overflow-x: hidden;
}

/* 顺便美化一下这个内部滚动条，让它配得上深色大屏 */
.dashboard-content::-webkit-scrollbar {
  width: 6px;
}
.dashboard-content::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.2);
  border-radius: 3px;
}
.dashboard-content::-webkit-scrollbar-track {
  background: transparent;
}

.empty-state { 
  display: flex; 
  align-items: center; 
  justify-content: center; 
  height: 100%; 
  color: #94a3b8; 
  font-size: 1.2rem; 
}

.dashboard-header { 
  margin-bottom: 24px; 
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  padding-bottom: 16px;
}

.dashboard-header h3 { 
  font-size: 2rem; 
  margin: 0 0 8px 0; 
  color: #f8fafc; /* 最亮的白色 */
  font-weight: 700;
  letter-spacing: 1px;
}

.en-name { 
  font-size: 1.1rem; 
  color: #f59e0b; /* 强调色 */
  font-weight: normal; 
  margin-left: 12px; 
}

.header-desc { 
  font-size: 0.95rem; 
  color: #94a3b8; 
  margin: 0; 
  line-height: 1.6; 
}

.recommendations-row { 
  margin-bottom: 24px; 
}

.rec-cards { 
  display: grid; 
  grid-template-columns: repeat(3, 1fr); 
  gap: 20px; 
}

/* 🌟 卡片基础样式 🌟 */
.rec-card { 
  background: rgba(30, 41, 59, 0.6); /* 深层背景 */
  border: 1px solid rgba(255, 255, 255, 0.08); 
  border-radius: 12px; 
  overflow: hidden; 
  transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1); 
  cursor: pointer;
  position: relative;
}

.rec-card:hover { 
  transform: translateY(-4px); 
  border-color: rgba(255, 255, 255, 0.25); 
  box-shadow: 0 12px 24px rgba(0,0,0,0.5);
  background: rgba(30, 41, 59, 0.9);
}

/* 🌟 选中卡片的发光特效 🌟 */
.rec-card.active-card {
  border: 2px solid #f59e0b;
  box-shadow: 0 0 20px rgba(245, 158, 11, 0.2);
  transform: translateY(-4px);
  background: rgba(245, 158, 11, 0.1);
}

.active-badge {
  position: absolute; 
  top: 0; 
  right: 0; 
  background: #f59e0b; 
  color: #1e293b; /* 深色文字，高对比度 */
  font-size: 12px; 
  padding: 5px 12px; 
  border-bottom-left-radius: 12px; 
  font-weight: 800;
  box-shadow: -2px 2px 8px rgba(0,0,0,0.3);
}

.rec-img { 
  height: 140px; 
  background-size: cover; 
  background-position: center; 
  background-repeat: no-repeat; 
}

.rec-info { 
  padding: 16px; 
}

.rec-title { 
  margin: 0 0 12px 0; 
  font-size: 1rem; 
  color: #f1f5f9; 
  white-space: nowrap; 
  overflow: hidden; 
  text-overflow: ellipsis; 
  font-weight: 500; 
}

.rec-price { 
  margin: 0; 
  color: #fb7185; /* 明亮的红色，在深色背景上更显眼 */
  font-weight: 800; 
  font-size: 1.3rem; 
  font-family: 'Courier New', Courier, monospace;
}

/* 🌟 下方图表区域样式 🌟 */
.chart-section {
  flex: 1; 
  display: flex; 
  flex-direction: column; 
  background: rgba(15, 23, 42, 0.6); /* 更深的底色承托图表 */
  border-radius: 12px; 
  padding: 20px;
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.chart-title { 
  font-size: 1.1rem; 
  color: #cbd5e1; 
  margin-bottom: 15px; 
  text-align: center; 
}

.highlight-text { 
  color: #fbd38d; /* 柔和的亮金橙色 */
  font-weight: 700; 
  font-size: 1.2rem; 
  border-bottom: 2px dashed #fbd38d; 
  padding-bottom: 2px; 
}

.chart-container { 
  flex: 1; 
  min-height: 280px; 
}
</style>
