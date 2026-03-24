<script setup lang="ts">
const footerLinks = [
  {
    title: '关于我们',
    items: [
      { label: '平台介绍', path: '/about' },
      { label: '联系我们', path: '/contact' },
      { label: '加入我们', path: '/join' },
    ],
  },
  {
    title: '帮助中心',
    items: [
      { label: '使用指南', path: '/help/guide' },
      { label: '常见问题', path: '/help/faq' },
      { label: '意见反馈', path: '/feedback' },
    ],
  },
  {
    title: '合作伙伴',
    items: [
      { label: '企业合作', path: '/cooperation' },
      { label: '院校合作', path: '/school' },
      { label: '讲师入驻', path: '/teacher-join' },
    ],
  },
]

const currentYear = new Date().getFullYear()
</script>

<template>
  <footer class="app-footer" role="contentinfo">
    <div class="footer-content">
      <!-- 链接区域 -->
      <nav class="footer-links" aria-label="底部导航">
        <div v-for="group in footerLinks" :key="group.title" class="link-group">
          <h4>{{ group.title }}</h4>
          <ul>
            <li v-for="item in group.items" :key="item.path">
              <router-link :to="item.path">{{ item.label }}</router-link>
            </li>
          </ul>
        </div>
      </nav>

      <!-- 分隔线 -->
      <el-divider />

      <!-- 底部信息 -->
      <div class="footer-bottom">
        <div class="copyright">
          <p>© {{ currentYear }} 职业培训课堂 版权所有</p>
          <p class="icp">京ICP备XXXXXXXX号-1</p>
        </div>
        <div class="contact-info">
          <span>客服电话：400-XXX-XXXX</span>
          <span>工作时间：周一至周五 9:00-18:00</span>
        </div>
      </div>
    </div>
  </footer>
</template>

<style lang="scss" scoped>
.app-footer {
  background-color: #2a2a2a;
  color: #fff;
  padding: 40px 0 24px;
}

.footer-content {
  max-width: 1440px;
  margin: 0 auto;
  padding: 0 24px;
}

.footer-links {
  display: flex;
  justify-content: space-around;
  gap: 40px;

  .link-group {
    h4 {
      font-size: 16px;
      font-weight: 500;
      margin-bottom: 16px;
      color: #fff;
    }

    ul {
      li {
        margin-bottom: 8px;

        a {
          color: #bbb; // 提高对比度，符合 WCAG AA 标准
          font-size: 14px;
          transition: color 0.2s;

          &:hover,
          &:focus {
            color: #1890ff;
          }
        }
      }
    }
  }
}

.el-divider {
  margin: 32px 0;
  border-color: #444;
}

.footer-bottom {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 16px;

  .copyright {
    p {
      font-size: 13px;
      color: #aaa; // 提高对比度
      margin-bottom: 4px;

      &:last-child {
        margin-bottom: 0;
      }
    }

    .icp {
      font-size: 12px;
    }
  }

  .contact-info {
    display: flex;
    gap: 24px;

    span {
      font-size: 13px;
      color: #aaa; // 提高对比度
    }
  }
}

@media (max-width: 768px) {
  .footer-links {
    flex-direction: column;
    gap: 24px;

    .link-group {
      text-align: center;
    }
  }

  .footer-bottom {
    flex-direction: column;
    text-align: center;
  }
}
</style>