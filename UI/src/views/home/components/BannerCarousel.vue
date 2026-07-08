<script setup lang="ts">
import { computed, ref } from 'vue'

interface BannerItem {
  id: number
  image_url: string
  title: string
}

// Banner数据（实际项目从API获取）
const bannerList = ref<BannerItem[]>([
  {
    id: 1,
    image_url: 'https://via.placeholder.com/1200x400/1890ff/ffffff?text=Banner+1',
    title: '欢迎来到职业培训课堂',
  },
  {
    id: 2,
    image_url: 'https://via.placeholder.com/1200x400/52c41a/ffffff?text=Banner+2',
    title: '精品课程推荐',
  },
  {
    id: 3,
    image_url: 'https://via.placeholder.com/1200x400/faad14/ffffff?text=Banner+3',
    title: '新用户专享福利',
  },
])

const currentBanner = computed(() => bannerList.value[0] ?? null)
</script>

<template>
  <div v-if="currentBanner" class="banner-carousel" role="region" aria-label="首页展示图">
    <div class="banner-item" :aria-label="currentBanner.title">
      <el-image
        :src="currentBanner.image_url"
        fit="cover"
        class="banner-image"
        :alt="currentBanner.title"
      >
        <template #error>
          <div class="banner-placeholder">
            <el-icon :size="64" color="#dbeafe"><Picture /></el-icon>
            <span>{{ currentBanner.title }}</span>
          </div>
        </template>
      </el-image>
      <div class="banner-overlay">
        <h2 class="banner-title">{{ currentBanner.title }}</h2>
      </div>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.banner-carousel {
  margin-bottom: 24px;
}

.banner-item {
  position: relative;
  width: 100%;
  min-height: 400px;
  aspect-ratio: 3 / 1;
  overflow: hidden;
  border: 1px solid rgba(219, 234, 254, 0.9);
  border-radius: 28px;
  background: linear-gradient(135deg, #dbeafe 0%, #eff6ff 100%);
  box-shadow: 0 18px 42px rgba(37, 99, 235, 0.14);

  .banner-image {
    width: 100%;
    height: 100%;
  }

  .banner-placeholder {
    width: 100%;
    height: 100%;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 24px;
    background: linear-gradient(135deg, #1d4ed8 0%, #60a5fa 100%);
    color: #eff6ff;
    gap: 16px;
    text-align: center;

    span {
      font-size: 24px;
      font-weight: 800;
      letter-spacing: 0.4px;
    }
  }

  .banner-overlay {
    position: absolute;
    bottom: 0;
    left: 0;
    right: 0;
    display: flex;
    align-items: flex-end;
    padding: 48px 28px 28px;
    background: linear-gradient(to top, rgba(15, 23, 42, 0.72), rgba(37, 99, 235, 0.12), transparent);

    .banner-title {
      margin: 0;
      max-width: min(100%, 720px);
      padding: 10px 16px;
      color: #fff;
      background: rgba(24, 144, 255, 0.24);
      border: 1px solid rgba(219, 234, 254, 0.42);
      border-radius: 20px;
      font-size: 28px;
      font-weight: 800;
      letter-spacing: 0.5px;
      line-height: 1.35;
      white-space: normal;
      word-break: break-word;
      text-shadow: 0 2px 8px rgba(15, 23, 42, 0.28);
      backdrop-filter: blur(8px);
    }
  }
}

@media (max-width: 768px) {
  .banner-item {
    min-height: 220px;
    aspect-ratio: 16 / 9;
    border-radius: 20px;

    .banner-placeholder {
      padding: 20px;
      gap: 12px;

      span {
        font-size: 18px;
      }
    }

    .banner-overlay {
      padding: 28px 16px 16px;

      .banner-title {
        max-width: 100%;
        padding: 8px 12px;
        font-size: 18px;
        border-radius: 16px;
        line-height: 1.4;
      }
    }
  }
}

@media (max-width: 480px) {
  .banner-item {
    min-height: 196px;

    .banner-overlay {
      padding: 24px 14px 14px;
    }

    .banner-placeholder span {
      font-size: 16px;
    }
  }
}
</style>
