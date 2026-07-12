<script setup lang="ts">
const currentBanner = {
  title: '欢迎来到职业培训课堂',
}

const featureCards = [
  {
    title: '系统化课程内容',
    description: '从入门基础到岗位进阶，学习节奏更清晰。',
  },
  {
    title: '多主题学习方向',
    description: '围绕热门技能领域持续更新课程内容。',
  },
  {
    title: '更适合长期学习',
    description: '兼顾知识积累、实操训练与能力成长。',
  },
]
</script>

<template>
  <div class="banner-carousel" role="region" aria-label="首页展示图">
    <section class="banner-item" :aria-label="currentBanner.title">
      <div class="banner-backdrop" aria-hidden="true">
        <span class="backdrop-orb orb-left"></span>
        <span class="backdrop-orb orb-right"></span>
        <span class="backdrop-grid"></span>
      </div>

      <div class="banner-copy">
        <h2 class="banner-title">{{ currentBanner.title }}</h2>
      </div>

      <div class="banner-visual" aria-hidden="true">
        <article class="visual-card visual-card--feature visual-card--primary">
          <div class="card-window">
            <span class="window-chip">WELCOME</span>
            <div class="window-lines">
              <span class="line line--strong"></span>
              <span class="line"></span>
              <span class="line line--short"></span>
            </div>
            <div class="window-bars">
              <span class="bar bar--tall"></span>
              <span class="bar"></span>
              <span class="bar bar--mid"></span>
            </div>
          </div>
          <strong>{{ featureCards[0].title }}</strong>
          <span>{{ featureCards[0].description }}</span>
        </article>

        <div class="visual-stack">
          <article
            v-for="card in featureCards.slice(1)"
            :key="card.title"
            class="visual-card visual-card--mini"
          >
            <strong>{{ card.title }}</strong>
            <span>{{ card.description }}</span>
          </article>
        </div>
      </div>
    </section>
  </div>
</template>

<style lang="scss" scoped>
.banner-carousel {
  margin-bottom: 24px;
}

.banner-item {
  position: relative;
  display: grid;
  grid-template-columns: minmax(0, 1.12fr) minmax(360px, 0.88fr);
  align-items: center;
  gap: 28px;
  min-height: 400px;
  overflow: hidden;
  border: 1px solid rgba(191, 219, 254, 0.9);
  border-radius: 30px;
  padding: 40px 38px;
  background:
    linear-gradient(135deg, rgba(30, 64, 175, 0.96) 0%, rgba(59, 130, 246, 0.94) 52%, rgba(125, 211, 252, 0.92) 100%);
  box-shadow: 0 22px 52px rgba(37, 99, 235, 0.16);
  isolation: isolate;
}

.banner-backdrop {
  position: absolute;
  inset: 0;
  overflow: hidden;
  pointer-events: none;
}

.backdrop-orb {
  position: absolute;
  border-radius: 999px;
  filter: blur(4px);
  opacity: 0.72;
}

.orb-left {
  width: 320px;
  height: 320px;
  left: -96px;
  top: 38px;
  background: radial-gradient(circle, rgba(255, 255, 255, 0.2) 0%, rgba(96, 165, 250, 0.04) 72%, transparent 100%);
}

.orb-right {
  width: 360px;
  height: 360px;
  right: -120px;
  bottom: -120px;
  background: radial-gradient(circle, rgba(15, 23, 42, 0.34) 0%, rgba(15, 23, 42, 0.02) 70%, transparent 100%);
}

.backdrop-grid {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(255, 255, 255, 0.12) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.12) 1px, transparent 1px);
  background-size: 54px 54px;
  mask-image: linear-gradient(135deg, rgba(0, 0, 0, 0.36), transparent 72%);
  opacity: 0.24;
}

.banner-copy {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-width: 640px;
  color: #eff6ff;
}

.banner-title {
  margin: 0;
  font-size: clamp(34px, 4.2vw, 52px);
  line-height: 1.12;
  font-weight: 800;
  letter-spacing: 0.02em;
  text-shadow: 0 10px 24px rgba(15, 23, 42, 0.2);
}

.banner-visual {
  position: relative;
  z-index: 1;
  display: grid;
  gap: 16px;
  justify-items: stretch;
}

.visual-stack {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.visual-card {
  position: relative;
  overflow: hidden;
  border: 1px solid rgba(219, 234, 254, 0.34);
  border-radius: 24px;
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.24) 0%, rgba(255, 255, 255, 0.1) 100%);
  box-shadow:
    0 18px 32px rgba(15, 23, 42, 0.18),
    inset 0 1px 0 rgba(255, 255, 255, 0.16);
  backdrop-filter: blur(18px);
}

.visual-card::after {
  content: '';
  position: absolute;
  inset: auto -20% -42% auto;
  width: 120px;
  height: 120px;
  border-radius: 999px;
  background: radial-gradient(circle, rgba(255, 255, 255, 0.24), transparent 68%);
}

.visual-card--feature {
  padding: 22px;
  animation: float-card 6s ease-in-out infinite;
}

.visual-card--primary {
  transform: translateX(6px);
}

.card-window {
  position: relative;
  margin-bottom: 18px;
  border-radius: 20px;
  padding: 16px;
  background: linear-gradient(180deg, rgba(7, 12, 25, 0.22) 0%, rgba(7, 12, 25, 0.08) 100%);
  border: 1px solid rgba(219, 234, 254, 0.24);
}

.window-chip {
  display: inline-flex;
  margin-bottom: 12px;
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(96, 165, 250, 0.18);
  color: #dbeafe;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.16em;
}

.window-lines {
  display: grid;
  gap: 8px;
  margin-bottom: 14px;
}

.line {
  display: block;
  height: 8px;
  border-radius: 999px;
  background: rgba(219, 234, 254, 0.38);
}

.line--strong {
  width: 82%;
  background: rgba(255, 255, 255, 0.72);
}

.line--short {
  width: 56%;
}

.window-bars {
  display: flex;
  align-items: flex-end;
  gap: 10px;
  height: 60px;
}

.bar {
  width: 22px;
  height: 32px;
  border-radius: 999px 999px 8px 8px;
  background: linear-gradient(180deg, rgba(191, 219, 254, 0.92), rgba(59, 130, 246, 0.56));
}

.bar--mid {
  height: 44px;
}

.bar--tall {
  height: 60px;
}

.visual-card strong,
.visual-card span {
  position: relative;
  z-index: 1;
  display: block;
  color: #eff6ff;
}

.visual-card strong {
  font-size: 17px;
  font-weight: 800;
  line-height: 1.45;
}

.visual-card span {
  margin-top: 6px;
  font-size: 13px;
  line-height: 1.7;
  color: rgba(239, 246, 255, 0.84);
}

.visual-card--mini {
  min-height: 132px;
  padding: 18px 18px 16px;
}

.visual-card--mini:nth-child(1) {
  animation: float-card 7s ease-in-out infinite;
}

.visual-card--mini:nth-child(2) {
  animation: float-card 8s ease-in-out infinite reverse;
}

@keyframes float-card {
  0%,
  100% {
    transform: translateY(0);
  }

  50% {
    transform: translateY(-8px);
  }
}

@media (max-width: 1024px) {
  .banner-item {
    grid-template-columns: 1fr;
    gap: 24px;
    padding: 34px 28px;
  }

  .banner-copy {
    max-width: none;
  }

  .banner-visual {
    max-width: 100%;
  }
}

@media (max-width: 768px) {
  .banner-item {
    min-height: 0;
    border-radius: 22px;
    padding: 26px 18px 20px;
  }

  .banner-title {
    font-size: 28px;
  }

  .visual-stack {
    grid-template-columns: 1fr;
  }

  .visual-card--feature,
  .visual-card--mini {
    padding: 16px;
  }

  .visual-card strong {
    font-size: 15px;
  }

  .visual-card span {
    font-size: 12px;
  }
}
</style>
