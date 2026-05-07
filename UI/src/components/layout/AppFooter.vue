<script setup lang="ts">
const currentYear = new Date().getFullYear()
</script>

<template>
  <footer class="app-footer" role="contentinfo">
    <div class="footer-content">
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
  padding: 24px 0;
}

.footer-content {
  max-width: 1440px;
  margin: 0 auto;
  padding: 0 24px;
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
  .footer-bottom {
    flex-direction: column;
    text-align: center;
  }
}
</style>
