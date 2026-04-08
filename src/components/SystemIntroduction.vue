<!-- src/components/SystemIntroduction.vue -->
<template>
  <div v-if="showIntroduction && showOverlay" class="system-introduction-overlay">
    <div class="container" id="scene">
      <div class="layer bg-layer" data-speed="-2"></div>
      <div class="layer glow-layer" data-speed="1"></div>
      <div class="layer spotlight-layer" data-speed="2" ref="spotlightRef"></div>
      <div class="layer floating-particles" data-speed="3"></div>

      <div class="layer floating-cards" data-speed="4">
        <div class="card c1" data-gem="amethyst">
          <div class="gem-glow"></div>
          <div class="card-inner">
            <img src="../assets/enter/矿物标本.png" alt="紫水晶" />
            <span>矿物标本</span>
          </div>
        </div>
        <div class="card c2" data-gem="quartz">
          <div class="gem-glow"></div>
          <div class="card-inner">
            <img src="../assets/enter/岩石标本.png" alt="石英晶体" />
            <span>岩石标本</span>
          </div>
        </div>
        <div class="card c3" data-gem="pyrite">
          <div class="gem-glow"></div>
          <div class="card-inner">
            <img src="../assets/enter/宝玉石.png" alt="黄铁矿" />
            <span>宝玉石</span>
          </div>
        </div>
        <div class="card c4" data-gem="malachite">
          <div class="gem-glow"></div>
          <div class="card-inner">
            <img src="../assets/enter/矿石标本.png" alt="孔雀石" />
            <span>矿石标本</span>
          </div>
        </div>
        <div class="card c5" data-gem="tourmaline">
          <div class="gem-glow"></div>
          <div class="card-inner">
            <img src="../assets/enter/铀矿物.png" alt="碧玺" />
            <span>铀矿物</span>
          </div>
        </div>
        <div class="card c6" data-gem="fluorite">
          <div class="gem-glow"></div>
          <div class="card-inner">
            <img src="../assets/enter/构造标本.png" alt="萤石" />
            <span>构造标本</span>
          </div>
        </div>
      </div>

      <div class="layer content-layer" data-speed="2">
        <div class="center-content">
          <div class="title-wrap">
            <p class="eyebrow">MINERAL INFORMATION GRAPH SYSTEM</p>
            <h1>
              <TextType 
                :text="['浩矿宸图']"
                :typingSpeed="130"
                :pauseDuration="3000"
                :deleteSpeed="130"
                :showCursor="true"
                cursorCharacter="|"
              />
            </h1>
            <p class="subtitle">更恢弘的视角，关联全球矿物脉络</p>
          </div>

          <div class="cta-row">
            <button class="enter-btn" @click="enterSystem">
              <svg viewBox="0 0 24 24" class="arr arr-2" xmlns="http://www.w3.org/2000/svg">
                <path
                  d="M16.1716 10.9999L10.8076 5.63589L12.2218 4.22168L20 11.9999L12.2218 19.778L10.8076 18.3638L16.1716 12.9999H4V10.9999H16.1716Z"
                />
              </svg>
              <span class="btn-text">进入系统</span>
              <span class="btn-circle"></span>
              <svg viewBox="0 0 24 24" class="arr arr-1" xmlns="http://www.w3.org/2000/svg">
                <path
                  d="M16.1716 10.9999L10.8076 5.63589L12.2218 4.22168L20 11.9999L12.2218 19.778L10.8076 18.3638L16.1716 12.9999H4V10.9999H16.1716Z"
                />
              </svg>
            </button>
          </div>
        </div>

        <div class="stats-row">
          <div
            class="stat-card"
            v-for="stat in metrics"
            :key="stat.label"
            :class="animateReady ? 'animate__animated animate__bounceIn' : ''">
            <span class="stat-label">{{ stat.label }}</span>
            <div class="stat-number" :data-value="stat.value">0</div>
            <p class="stat-desc">{{ stat.desc }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>

  <div v-else-if="!hideHomeButton" class="floating-icon" @click="handleFloatingIconClick" title="回到首页">
    <img src="@/assets/首页.png" alt="回到首页" />
  </div>
</template>

<script setup>
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import gsap from 'gsap'
import TextType from './TextType.vue'

/* 定义 props */
const props = defineProps({
  hasEnteredSystem: {
    type: Boolean,
    default: false
  },
  // 是否允许显示全屏介绍遮罩层（用于避免在非首页刷新时出现“一闪而过”的介绍页）
  showOverlay: {
    type: Boolean,
    default: true
  },
  /** 为 true 时不显示“返回首页”浮动按钮（如智能回答页面） */
  hideHomeButton: {
    type: Boolean,
    default: false
  }
})

/* 定义 emit 事件 */
// enter-system：通知父组件用户点击了“进入系统”
// open-home：通知父组件用户点击右下角书本按钮，返回首页
const emit = defineEmits(['enter-system', 'open-home'])

/* 响应式数据 */
// 默认：如果父组件说明已经进入系统（hasEnteredSystem=true），就直接隐藏大封面，只显示右下角图标
const showIntroduction = ref(!props.hasEnteredSystem)
const animateReady = ref(false)
const spotlightRef = ref(null)
const spotlightPos = ref({ x: 50, y: 50 })
const metrics = ref([
  { label: '矿物名', value: 557, desc: '覆盖全库矿物名称' },
  { label: '颜色', value: 271, desc: '矿物颜色节点数' },
  { label: '发现地区', value: 117, desc: '已记录的矿物产地' }
])
const counterTweens = []

/* 方法 */
function enterSystem() {
  showIntroduction.value = false
  // 通知父组件用户已进入系统
  emit('enter-system')
}

function handleFloatingIconClick() {
  // 重新展示系统介绍
  showIntroduction.value = true
  // 通知父组件：用户希望回到首页（/）
  emit('open-home')
}

/* 视差 + 聚光灯效果 */
const handleParallax = (e) => {
  const layers = document.querySelectorAll('.system-introduction-overlay .layer')
  layers.forEach((layer) => {
    const speed = Number(layer.getAttribute('data-speed') || 0)
    const x = (window.innerWidth - e.pageX * speed) / 100
    const y = (window.innerHeight - e.pageY * speed) / 100
    layer.style.transform = `translateX(${x}px) translateY(${y}px)`
  })

  // spotlight follows mouse within scene bounds
  const sceneEl = document.getElementById('scene')
  if (!sceneEl || !spotlightRef.value) return
  const rect = sceneEl.getBoundingClientRect()
  const relX = ((e.clientX - rect.left) / rect.width) * 100
  const relY = ((e.clientY - rect.top) / rect.height) * 100
  spotlightPos.value = { x: Math.max(0, Math.min(100, relX)), y: Math.max(0, Math.min(100, relY)) }
  spotlightRef.value.style.setProperty('--spot-x', `${spotlightPos.value.x}%`)
  spotlightRef.value.style.setProperty('--spot-y', `${spotlightPos.value.y}%`)
}

/* GSAP 动画 */
function animateCounters() {
  counterTweens.forEach((tween) => tween.kill())
  counterTweens.length = 0

  nextTick(() => {
    const numbers = document.querySelectorAll('.stat-number')
    numbers.forEach((el) => {
      const target = Number(el.dataset.value || 0)
      const obj = { val: 0 }
      const tween = gsap.to(obj, {
        val: target,
        duration: 1.8,
        ease: 'power1.out',
        onUpdate: () => {
          const value = Math.floor(obj.val)
          el.textContent = `${value.toLocaleString()}+`
        }
      })
      counterTweens.push(tween)
    })
  })
}

function animateScene() {
  nextTick(() => {
    animateReady.value = false
    gsap.from('.title-wrap .eyebrow', { y: -10, opacity: 0, duration: 0.6, ease: 'power2.out' })
    gsap.from('.title-wrap h1', { y: 20, opacity: 0, duration: 0.8, ease: 'power3.out', delay: 0.1 })
    gsap.from('.title-wrap .subtitle', { y: 20, opacity: 0, duration: 0.8, ease: 'power3.out', delay: 0.2 })
    gsap.from('.cta-row', { y: 20, opacity: 0, duration: 0.8, ease: 'power3.out', delay: 0.3 })
    gsap.from('.stat-card', { y: 40, opacity: 0, duration: 0.9, ease: 'power3.out', stagger: 0.08, delay: 0.35 })
    gsap.from('.floating-cards .card', { scale: 0.9, opacity: 0, duration: 1, ease: 'power3.out', stagger: 0.05, delay: 0.15 })
    setTimeout(() => {
      animateReady.value = true
    }, 150)
    animateCounters()
  })
}

// 开启/关闭介绍层时的通用入口
function startIntroductionScene() {
  window.addEventListener('mousemove', handleParallax)
  nextTick(() => {
    if (spotlightRef.value) {
      spotlightRef.value.style.setProperty('--spot-x', `${spotlightPos.value.x}%`)
      spotlightRef.value.style.setProperty('--spot-y', `${spotlightPos.value.y}%`)
    }
  })
  animateScene()
}

function stopIntroductionScene() {
  window.removeEventListener('mousemove', handleParallax)
  counterTweens.forEach((tween) => tween.kill())
}

onMounted(() => {
  if (showIntroduction.value && props.showOverlay) {
    startIntroductionScene()
  }
})

onBeforeUnmount(() => {
  stopIntroductionScene()
})

watch(showIntroduction, (val) => {
  if (val) {
    if (props.showOverlay) {
      startIntroductionScene()
    }
  } else {
    stopIntroductionScene()
  }
})

// 监听父组件控制的遮罩层显示状态：从其他页面回到首页时重新启动动画
watch(
  () => props.showOverlay,
  (val) => {
    if (val && showIntroduction.value) {
      startIntroductionScene()
    } else if (!val) {
      stopIntroductionScene()
    }
  }
)

// 监听是否已经进入系统：
// - 当外层标记为「已进入系统」(true) 时，确保介绍层关闭
// - 当外层标记为「未进入系统」(false) 且在首页时，重新展示介绍层
watch(
  () => props.hasEnteredSystem,
  (val) => {
    showIntroduction.value = !val
  },
  { immediate: true }
)
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Cinzel:wght@600;800&family=Noto+Sans+SC:wght@400;700&display=swap');
@import url('https://cdn.jsdelivr.net/npm/animate.css@4.1.1/animate.min.css');

.system-introduction-overlay {
  position: fixed;
  inset: 0;
  width: 100vw;
  height: 100vh;
  overflow: hidden;
  --deep: #7b542f;
  --earth: #b6771d;
  --accent: #d48800;
  --highlight: #d4b85a;
  --bg-glow: rgba(212, 184, 90, 0.12);
  background: radial-gradient(circle at 20% 20%, rgba(212, 184, 90, 0.08), transparent 35%),
    radial-gradient(circle at 80% 10%, rgba(212, 136, 0, 0.12), transparent 40%),
    #0d0a07;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  font-family: 'Cinzel', 'Noto Sans SC', sans-serif;
  color: #f7f1e8;
  filter: saturate(0.85);
}

.container {
  position: relative;
  width: 100%;
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  /* overflow: hidden; */
}

.layer {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  pointer-events: none;
}

.bg-layer {
  background:
    linear-gradient(to bottom, rgba(0, 0, 0, 0.35), rgba(0, 0, 0, 0.85)),
    url('https://pic.vjshi.com/2024-12-24/c83e7a41e29b42f496fa8cb889e14ef0/online/601e0ff067804fb184f1166d3a047d45.jpg?x-oss-process=style/video_cover_20231101')
      no-repeat left center;
  background-size: cover;
  width: 120%;
  height: 110%;
  left: -10%;
  top: -5%;
  filter: brightness(0.55) contrast(1.1) saturate(0.6);
  z-index: 0;
}

.glow-layer {
  z-index: 1;
  width: 100%;
  height: 100%;
  background: radial-gradient(circle at center, var(--bg-glow) 0%, transparent 70%);
}

.spotlight-layer {
  z-index: 3;
  width: 110%;
  height: 110%;
  pointer-events: none;
  background: radial-gradient(
    circle at var(--spot-x, 50%) var(--spot-y, 50%),
    rgba(255, 255, 255, 0.2) 0%,
    rgba(255, 255, 255, 0.1) 20%,
    rgba(0, 0, 0, 0) 40%
  );
  mix-blend-mode: screen;
  transition: background-position 0.15s ease-out;
}

.content-layer {
  z-index: 10;
  text-align: center;
  color: white;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-start;
  padding: clamp(60px, 8vh, 120px) clamp(16px, 6vw, 48px) clamp(20px, 4vh, 48px);
  pointer-events: auto;
  min-height: 100vh;
  height: 100vh;
  position: relative;
}

.center-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: clamp(12px, 2vh, 24px);
  flex: 1;
}

.title-wrap {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: clamp(6px, 1vh, 12px);
  text-transform: uppercase;
  flex-shrink: 0;
}

.eyebrow {
  letter-spacing: 6px;
  font-size: clamp(0.8rem, 1.4vw, 0.95rem);
  color: rgba(255, 255, 255, 0.6);
}

h1 {
  font-size: clamp(2.8rem, 5.6vw, 4.6rem);
  letter-spacing: 6px;
  margin: 0;
  text-shadow: 0 12px 30px rgba(0, 0, 0, 0.45);
  background: linear-gradient(120deg, #e8dcc8, #d4b85a, #d48800);
  background-clip: text;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.subtitle {
  font-size: clamp(1rem, 2.2vw, 1.3rem);
  color: rgba(255, 255, 255, 0.76);
  letter-spacing: 3px;
  margin: 6px 0 16px;
}

.floating-cards {
  position: absolute;
  width: 100%;
  height: 100%;
  z-index: 6;
  pointer-events: none;
  perspective: 1200px;
}

.floating-particles {
  z-index: 2;
  pointer-events: none;
  background-image: radial-gradient(circle at 20% 30%, rgba(212, 184, 90, 0.3) 0, transparent 14%),
    radial-gradient(circle at 80% 20%, rgba(212, 136, 0, 0.25) 0, transparent 16%),
    radial-gradient(circle at 60% 70%, rgba(255, 255, 255, 0.18) 0, transparent 12%);
  background-size: 140% 140%;
  animation: driftGlow 12s ease-in-out infinite alternate;
}

.card {
  position: absolute;
  width: 140px;
  height: 180px;
  transform-style: preserve-3d;
  transition: transform 0.4s cubic-bezier(0.23, 1, 0.32, 1);
  animation: floatRotate 8s ease-in-out infinite;
  pointer-events: auto;
}

.card-inner {
  position: relative;
  width: 100%;
  height: 100%;
  background: rgba(25, 18, 12, 0.75);
  border: 1.5px solid rgba(212, 184, 90, 0.4);
  backdrop-filter: blur(12px) saturate(100%);
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 
    0 20px 40px rgba(0, 0, 0, 0.6),
    0 0 0 1px rgba(212, 136, 0, 0.1),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
  transition: all 0.4s cubic-bezier(0.23, 1, 0.32, 1);
  transform-style: preserve-3d;
}

.card img {
  width: 100%;
  height: 80%;
  object-fit: cover;
  opacity: 0.95;
  transition: transform 0.4s ease, opacity 0.4s ease;
  filter: brightness(1.05) contrast(1.1) saturate(0.7);
}

.card span {
  display: flex;
  height: 20%;
  color: #d4b85a;
  font-size: 12px;
  align-items: center;
  justify-content: center;
  background: linear-gradient(to top, rgba(0, 0, 0, 0.6), rgba(0, 0, 0, 0.4));
  text-transform: uppercase;
  letter-spacing: 1.5px;
  font-weight: 600;
  text-shadow: 0 2px 8px rgba(0, 0, 0, 0.5);
  transition: color 0.3s ease;
}

/* 宝石光晕效果 */
.gem-glow {
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  border-radius: 50%;
  opacity: 0;
  transition: opacity 0.4s ease;
  pointer-events: none;
  z-index: -1;
}

.card[data-gem="amethyst"] .gem-glow {
  background: radial-gradient(circle, rgba(138, 43, 226, 0.4) 0%, transparent 70%);
}

.card[data-gem="quartz"] .gem-glow {
  background: radial-gradient(circle, rgba(255, 255, 255, 0.35) 0%, transparent 70%);
}

.card[data-gem="pyrite"] .gem-glow {
  background: radial-gradient(circle, rgba(255, 215, 0, 0.4) 0%, transparent 70%);
}

.card[data-gem="malachite"] .gem-glow {
  background: radial-gradient(circle, rgba(0, 191, 165, 0.4) 0%, transparent 70%);
}

.card[data-gem="tourmaline"] .gem-glow {
  background: radial-gradient(circle, rgba(255, 20, 147, 0.35) 0%, transparent 70%);
}

.card[data-gem="fluorite"] .gem-glow {
  background: radial-gradient(circle, rgba(64, 224, 208, 0.4) 0%, transparent 70%);
}


.card:hover .card-inner {
  transform: translateZ(20px) scale(1.05);
  border-color: var(--highlight);
  box-shadow: 
    0 30px 60px rgba(0, 0, 0, 0.7),
    0 0 30px rgba(212, 184, 90, 0.4),
    inset 0 1px 0 rgba(255, 255, 255, 0.2);
}

.card:hover .gem-glow {
  opacity: 1;
}

.card:hover img {
  transform: scale(1.1);
  opacity: 1;
}

.card:hover span {
  color: #fff;
}


/* 鼠标交互时的3D倾斜效果 */
.card:hover {
  transform: rotateY(5deg) rotateX(-5deg) scale(1.1);
  z-index: 20;
  cursor: pointer;
}

/* 优化后的圆形布局 - 围绕中心呈椭圆形分布 */
.c1 {
  top: 12%;
  left: 18%;
  animation-delay: 0s;
}

.c2 {
  top: 10%;
  right: 15%;
  animation-delay: 1.2s;
}

.c3 {
  bottom: 18%;
  left: 22%;
  animation-delay: 2.4s;
}

.c4 {
  bottom: 15%;
  right: 20%;
  animation-delay: 0.8s;
}

.c5 {
  top: 45%;
  left: 8%;
  transform: translateY(-50%);
  animation-delay: 1.8s;
  scale: 0.85;
}

.c6 {
  top: 45%;
  right: 8%;
  transform: translateY(-50%);
  animation-delay: 3s;
  scale: 0.85;
}

.cta-row {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  justify-content: center;
  flex-shrink: 0;
  margin: clamp(16px, 3vh, 32px) 0;
}

.enter-btn {
  --enter-accent: #d4b85a;
  position: relative;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 14px 32px;
  font-size: 1.2rem;
  font-weight: 700;
  color: var(--enter-accent);
  background-color: transparent;
  border: 3px solid transparent;
  border-radius: 999px;
  box-shadow: 0 0 0 2px var(--enter-accent);
  cursor: pointer;
  overflow: hidden;
  transition: all 0.6s cubic-bezier(0.23, 1, 0.32, 1);
  pointer-events: auto;
  letter-spacing: 2px;
}

.enter-btn svg {
  position: absolute;
  width: 22px;
  fill: var(--enter-accent);
  z-index: 2;
  transition: all 0.8s cubic-bezier(0.23, 1, 0.32, 1);
}

.enter-btn .arr {
  top: 50%;
  transform: translateY(-50%);
}

.enter-btn .arr-1 {
  right: 18px;
}

.enter-btn .arr-2 {
  left: -28%;
}

.enter-btn .btn-circle {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 20px;
  height: 20px;
  background-color: var(--enter-accent);
  border-radius: 50%;
  opacity: 0;
  transition: all 0.8s cubic-bezier(0.23, 1, 0.32, 1);
}

.enter-btn .btn-text {
  position: relative;
  z-index: 3;
  transform: translateX(-10px);
  transition: all 0.8s cubic-bezier(0.23, 1, 0.32, 1);
}

.enter-btn:hover {
  box-shadow: 0 0 0 12px transparent;
  color: #20130b;
  border-radius: 16px;
}

.enter-btn:hover .arr-1 {
  right: -28%;
}

.enter-btn:hover .arr-2 {
  left: 18px;
}

.enter-btn:hover .btn-text {
  transform: translateX(12px);
}

.enter-btn:hover svg {
  fill: #20130b;
}

.enter-btn:active {
  transform: scale(0.96);
  box-shadow: 0 0 0 4px var(--enter-accent);
}

.enter-btn:hover .btn-circle {
  width: 240px;
  height: 240px;
  opacity: 1;
}

.ghost-btn {
  padding: 14px 28px;
  border-radius: 999px;
  border: 1.5px solid rgba(255, 255, 255, 0.35);
  background: rgba(255, 255, 255, 0.04);
  color: #f4e7d3;
  letter-spacing: 1px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.ghost-btn:hover {
  background: rgba(212, 184, 90, 0.16);
  border-color: rgba(212, 184, 90, 0.55);
}

.ghost-btn.pill {
  padding: 14px 34px;
}

.stats-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: clamp(40px, 8vw, 100px);
  width: min(1080px, 90vw);
  position: absolute;
  bottom: 10px;
  left: 50%;
  transform: translateX(-50%);
  flex-shrink: 0;
}

.stat-card {
  background: rgba(20, 14, 10, 0.5);
  border: 1px solid rgba(212, 184, 90, 0.18);
  border-radius: 16px;
  padding: 16px 18px;
  box-shadow: 0 14px 28px rgba(0, 0, 0, 0.2);
  text-align: left;
}

.stat-label {
  font-size: 0.95rem;
  color: rgba(255, 255, 255, 0.55);
}

.stat-number {
  font-size: 2rem;
  font-weight: 800;
  letter-spacing: 1px;
  color: rgba(212, 184, 90, 0.7);
  margin: 6px 0;
}

.stat-desc {
  font-size: 0.9rem;
  color: rgba(255, 255, 255, 0.5);
  margin: 0;
}

@keyframes floatRotate {
  0%, 100% {
    transform: translateY(0) rotateY(0deg) rotateX(0deg);
  }
  25% {
    transform: translateY(-15px) rotateY(5deg) rotateX(2deg);
  }
  50% {
    transform: translateY(-25px) rotateY(0deg) rotateX(0deg);
  }
  75% {
    transform: translateY(-15px) rotateY(-5deg) rotateX(-2deg);
  }
}


@keyframes fadeInDown {
  from {
    opacity: 0;
    transform: translateY(-50px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(50px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes driftGlow {
  from {
    transform: translate3d(-10px, -6px, 0) scale(1);
  }
  to {
    transform: translate3d(12px, 10px, 0) scale(1.05);
  }
}

.floating-icon {
  position: fixed;
  bottom: clamp(10px, 4vh, 20px);
  right: clamp(20px, 4vw, 30px);
  width: clamp(35px, 8vw, 40px);
  height: clamp(35px, 8vw, 40px);
  background: linear-gradient(135deg, #0b1f2f, #0f3b52);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: 0 8px 25px rgba(0, 195, 255, 0.25);
  transition: all 0.3s ease;
  z-index: 1000;
  color: white;
}

.floating-icon:hover {
  transform: scale(1.1);
  box-shadow: 0 12px 35px rgba(0, 195, 255, 0.35);
}

.floating-icon img {
  width: clamp(20px, 4vw, 28px);
  height: clamp(20px, 4vw, 28px);
  object-fit: contain;
}

@media (max-width: 720px) {
  .stat-number {
    font-size: 1.6rem;
  }

  .stat-card {
    text-align: center;
  }
}
</style>
