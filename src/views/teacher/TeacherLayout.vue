<template>
  <div class="teacher-layout">
    <main class="main-content">
      <router-view />
    </main>
  </div>
</template>

<style lang="scss" scoped>

.teacher-layout {
  min-height: calc(100vh - 64px);
}

.main-content {
  background: $bg-color;
  padding: 24px;
  flex: 1;

  @media (max-width: $breakpoint-lg) {
    padding: 16px;
  }
}

</style>
