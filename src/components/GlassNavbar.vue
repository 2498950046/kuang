<template>
  <nav class="glass-nav">
    <div class="nav-shell">
      <div class="brand">
        <span class="logo">
        </span>
        <div class="brand-text">
          <span class="title">{{ brandTitle }}</span>
          <span v-if="brandSubtitle" class="subtitle">{{ brandSubtitle }}</span>
        </div>
      </div>

      <div class="links">
        <a
          v-for="item in links"
          :key="item.label"
          :href="item.href"
        >
          {{ item.label }}
        </a>
      </div>
    </div>
  </nav>
</template>

<script setup lang="ts">
type LinkItem = {
  label: string
  href: string
}

withDefaults(defineProps<{
  brandTitle?: string
  brandSubtitle?: string
  links?: LinkItem[]
}>(), {
  brandTitle: 'Hawk Mine Chentu',
  brandSubtitle: '',
  links: () => ([
    { label: 'Home', href: '#' },
    { label: 'Docs', href: '#' }
  ])
})
</script>

<style scoped>
.glass-nav {
  width: 100%;
  display: flex;
  justify-content: center;
  padding: 18px 20px;
  pointer-events: none;
}

.nav-shell {
  width: min(1180px, 100%);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  padding: 14px 24px;
  border-radius: 999px;
  background: linear-gradient(135deg, rgba(72, 80, 86, 0.1), rgba(22, 24, 26, 0.1));
  border: 1px solid rgba(255, 255, 255, 0.25);
  box-shadow:
    0 24px 60px rgba(0, 0, 0, 0.35),
    inset 0 1px 0 rgba(255, 255, 255, 0.12);
  backdrop-filter: blur(18px) saturate(140%);
  color: #f4f6f9;
  pointer-events: auto;
  font-family: 'Raleway', sans-serif;
}

.brand {
  display: flex;
  align-items: center;
  gap: 12px;
}

.logo {
  position: relative;
  width: 42px;
  height: 42px;
  border-radius: 14px;
  display: grid;
  place-items: center;
  overflow: hidden;
}

.logo .arm {
  position: absolute;
  width: 60%;
  height: 10%;
  background: linear-gradient(90deg, #ffffff, #cfd8dc);
  top: 52%;
  border-radius: 8px;
  transform-origin: center;
}

.logo .arm.left {
  transform: translateY(-6%) rotate(-55deg);
  left: 10%;
}

.logo .arm.right {
  transform: translateY(-6%) rotate(55deg);
  right: 10%;
}

.logo .dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #ffffff;
  position: absolute;
  top: 22%;
}

.brand-text {
  display: flex;
  flex-direction: column;
  line-height: 1.05;
}

.brand-text .title {
  font-size: 1.35rem;
  font-weight: 700;
  letter-spacing: 0.4px;
}

.brand-text .subtitle {
  font-size: 0.75rem;
  color: rgba(244, 246, 249, 0.72);
  letter-spacing: 0.2px;
}

.links {
  display: flex;
  align-items: center;
  gap: 22px;
  font-weight: 650;
  letter-spacing: 0.2px;
}

.links a {
  color: #f5f7fb;
  text-decoration: none;
  padding: 6px 4px;
  transition: color 0.2s ease, transform 0.2s ease;
}

.links a:hover {
  color: #ffffff;
  transform: translateY(-1px);
}

@media (max-width: 768px) {
  .nav-shell {
    gap: 12px;
    padding: 12px 18px;
  }

  .brand-text .title {
    font-size: 1.1rem;
  }

  .links {
    gap: 14px;
  }
}
</style>

