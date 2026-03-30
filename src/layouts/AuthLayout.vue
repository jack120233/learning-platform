<script setup lang="ts">
defineProps<{
  title?: string
  subTitle?: string
}>()
</script>

<template>
  <div class="auth-layout">
    <!-- 左侧品牌区 -->
    <div class="brand-side">
      <div class="brand-content">
        <router-link to="/" class="logo">
          <el-icon :size="48" color="#fff"><School /></el-icon>
          <span class="logo-text">职业培训课堂</span>
        </router-link>
        <h1 class="slogan">{{ title || '开启您的学习之旅' }}</h1>
        <p class="description">{{ subTitle || '海量优质课程，助您提升职业技能' }}</p>
        <div class="illustration" aria-hidden="true">
          <el-icon :size="120" color="rgba(255,255,255,0.3"><Reading /></el-icon>
        </div>
      </div>
    </div>

    <!-- 右侧表单区 -->
    <div class="form-side">
      <div class="form-container">
        <slot></slot>
      </div>
    </div>
  </div>
</template>

<style lang="scss" scoped>
@use '@/assets/styles/variables' as *;

.auth-layout {
  display: flex;
  min-height: 100vh;
  background-color: $bg-color;
}

.brand-side {
  width: 40%;
  background: linear-gradient(135deg, $primary-color 0%, #096dd9 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 48px;

  @media (max-width: $breakpoint-lg) {
    display: none;
  }
}

.brand-content {
  color: #fff;
  text-align: center;
  max-width: 400px;
}

.logo {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  margin-bottom: 32px;
  cursor: pointer;
  text-decoration: none;

  .logo-text {
    font-size: 24px;
    font-weight: 600;
    color: #fff;
  }
}

.slogan {
  font-size: 28px;
  font-weight: 600;
  margin-bottom: 16px;
  line-height: 1.4;
}

.description {
  font-size: 16px;
  opacity: 0.9;
  margin-bottom: 48px;
  line-height: 1.6;
}

.illustration {
  display: flex;
  justify-content: center;
}

.form-side {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 48px 24px;
  background-color: $bg-white;
}

.form-container {
  width: 100%;
  max-width: 420px;
}

@media (max-width: $breakpoint-sm) {
  .form-side {
    padding: 24px 16px;
  }

  .form-container {
    max-width: 100%;
  }
}
</style>