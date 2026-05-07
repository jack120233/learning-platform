<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'

interface BannerItem {
  id: number
  image_url: string
  title: string
  link_url: string
  link_type: 'course' | 'announcement' | 'external'
}

const router = useRouter()

// Banner数据（实际项目从API获取）
const bannerList = ref<BannerItem[]>([
  {
    id: 1,
    image_url: 'https://via.placeholder.com/1200x400/1890ff/ffffff?text=Banner+1',
    title: '欢迎来到职业培训课堂',
    link_url: '/courses',
    link_type: 'course',
  },
  {
    id: 2,
    image_url: 'https://via.placeholder.com/1200x400/52c41a/ffffff?text=Banner+2',
    title: '精品课程推荐',
    link_url: '/courses?category=1',
    link_type: 'course',
  },
  {
    id: 3,
    image_url: 'https://via.placeholder.com/1200x400/faad14/ffffff?text=Banner+3',
    title: '新用户专享福利',
    link_url: '/register',
    link_type: 'external',
  },
])

// 当前激活的轮播索引
const activeIndex = ref(0)

// 处理Banner点击
const handleBannerClick = (banner: BannerItem) => {
  if (banner.link_type === 'course' || banner.link_type === 'announcement') {
    router.push(banner.link_url)
  } else if (banner.link_type === 'external') {
    window.open(banner.link_url, '_blank')
  }
}
</script>

<template>
  <div class="banner-carousel" role="region" aria-label="轮播图">
    <el-carousel
      height="400px"
      :autoplay="true"
      :interval="5000"
      indicator-position="outside"
      aria-roledescription="carousel"
      @change="(index: number) => activeIndex = index"
    >
      <el-carousel-item
        v-for="banner in bannerList"
        :key="banner.id"
        :aria-label="banner.title"
      >
        <div
          class="banner-item"
          role="button"
          tabindex="0"
          :aria-label="`查看：${banner.title}`"
          @click="handleBannerClick(banner)"
          @keyup.enter="handleBannerClick(banner)"
        >
          <el-image
            :src="banner.image_url"
            fit="cover"
            class="banner-image"
            :alt="banner.title"
          >
            <template #error>
              <div class="banner-placeholder">
                <el-icon :size="64" color="#ccc"><Picture /></el-icon>
                <span>{{ banner.title }}</span>
              </div>
            </template>
          </el-image>
          <div class="banner-overlay">
            <h2 class="banner-title">{{ banner.title }}</h2>
          </div>
        </div>
      </el-carousel-item>
    </el-carousel>
  </div>
</template>

<style lang="scss" scoped>
.banner-carousel {
  margin-bottom: 24px;
  overflow: hidden;

  :deep(.el-carousel__indicators) {
    .el-carousel__indicator {
      .el-carousel__button {
        width: 32px;
        height: 4px;
        border-radius: 2px;
        background-color: rgba(0, 0, 0, 0.2);
      }

      &.is-active .el-carousel__button {
        background-color: #1890ff;
      }
    }
  }
}

.banner-item {
  position: relative;
  width: 100%;
  height: 100%;
  cursor: pointer;
  outline: none;

  &:focus-visible {
    outline: 2px solid #1890ff;
    outline-offset: 2px;
  }

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
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: #fff;
    gap: 16px;

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
    padding: 40px 24px 24px;
    background: linear-gradient(to top, rgba(15, 23, 42, 0.72), rgba(37, 99, 235, 0.12), transparent);

    .banner-title {
      width: fit-content;
      margin: 0;
      padding: 8px 14px;
      color: #fff;
      background: rgba(24, 144, 255, 0.24);
      border: 1px solid rgba(219, 234, 254, 0.42);
      border-radius: 999px;
      font-size: 28px;
      font-weight: 800;
      letter-spacing: 0.5px;
      text-shadow: 0 2px 8px rgba(15, 23, 42, 0.28);
      backdrop-filter: blur(8px);
    }
  }
}

@media (max-width: 768px) {
  .banner-carousel {
    :deep(.el-carousel) {
      height: 200px;
    }
  }

  .banner-item .banner-overlay .banner-title {
    font-size: 18px;
  }
}
</style>