<template>
  <div class="page-container">
    <h1 class="section-title">仪表盘</h1>

    <!-- Status Cards -->
    <div class="stats-grid">
      <div class="card stat-card">
        <div class="stat-icon" style="background-color: #dbeafe">
          <el-icon :size="20" color="var(--color-primary)"><Monitor /></el-icon>
        </div>
        <div class="stat-content">
          <span class="stat-label">浏览器状态</span>
          <span class="stat-value">
            <span v-if="systemInfo.browser_initialized" class="badge badge-success">已初始化</span>
            <span v-else class="badge badge-warning">未初始化</span>
          </span>
        </div>
      </div>

      <div class="card stat-card">
        <div class="stat-icon" style="background-color: #dcfce7">
          <el-icon :size="20" color="var(--color-success)"><User /></el-icon>
        </div>
        <div class="stat-content">
          <span class="stat-label">登录状态</span>
          <span class="stat-value">
            <span v-if="systemInfo.user_logged_in" class="badge badge-success">已登录</span>
            <span v-else class="badge badge-warning">未登录</span>
          </span>
        </div>
      </div>

      <div class="card stat-card">
        <div class="stat-icon" style="background-color: #fef3c7">
          <el-icon :size="20" color="var(--color-warning)"><Timer /></el-icon>
        </div>
        <div class="stat-content">
          <span class="stat-label">定时任务</span>
          <span class="stat-value">{{ systemInfo.scheduled_tasks }}</span>
        </div>
      </div>

      <div class="card stat-card">
        <div class="stat-icon" style="background-color: #f3e8ff">
          <el-icon :size="20" color="#9333ea"><ChatDotRound /></el-icon>
        </div>
        <div class="stat-content">
          <span class="stat-label">好友数量</span>
          <span class="stat-value">{{ friends.length }}</span>
        </div>
      </div>
    </div>

    <!-- Quick Actions -->
    <div class="section-header">
      <h2 class="section-subtitle">快速操作</h2>
    </div>

    <div class="actions-grid">
      <div class="card action-card" @click="$router.push('/browser')">
        <el-icon :size="24" color="var(--color-primary)"><Monitor /></el-icon>
        <span class="action-label">浏览器控制</span>
        <span class="action-desc">初始化、登录、截图</span>
      </div>

      <div class="card action-card" @click="$router.push('/friends')">
        <el-icon :size="24" color="var(--color-success)"><User /></el-icon>
        <span class="action-label">好友管理</span>
        <span class="action-desc">查看好友列表</span>
      </div>

      <div class="card action-card" @click="$router.push('/tasks')">
        <el-icon :size="24" color="var(--color-warning)"><Timer /></el-icon>
        <span class="action-label">定时任务</span>
        <span class="action-desc">管理定时发送</span>
      </div>

      <div class="card action-card" @click="$router.push('/settings')">
        <el-icon :size="24" color="#64748b"><Setting /></el-icon>
        <span class="action-label">系统设置</span>
        <span class="action-desc">修改密码、查看信息</span>
      </div>
    </div>

    <!-- System Info -->
    <div class="section-header">
      <h2 class="section-subtitle">系统信息</h2>
    </div>

    <div class="card">
      <el-descriptions :column="2" border>
        <el-descriptions-item label="版本">{{ systemInfo.version }}</el-descriptions-item>
        <el-descriptions-item label="运行时间">{{ systemInfo.uptime }}</el-descriptions-item>
        <el-descriptions-item label="最后登录 IP">{{ systemInfo.last_login_ip }}</el-descriptions-item>
        <el-descriptions-item label="定时任务数">{{ systemInfo.scheduled_tasks }}</el-descriptions-item>
      </el-descriptions>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useAppStore } from '../stores/app'
import {
  Monitor,
  User,
  Timer,
  ChatDotRound,
  Setting
} from '@element-plus/icons-vue'

const appStore = useAppStore()

const systemInfo = computed(() => appStore.systemInfo)
const friends = computed(() => appStore.friends)

onMounted(() => {
  appStore.fetchSystemInfo()
  appStore.fetchFriends()
  appStore.fetchTasks()
})
</script>

<style scoped>
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--space-4);
  margin-bottom: var(--space-8);
}

.stat-card {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  padding: var(--space-5);
}

.stat-icon {
  width: 44px;
  height: 44px;
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
}

.stat-content {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.stat-label {
  font-size: var(--text-sm);
  color: var(--text-secondary);
}

.stat-value {
  font-size: var(--text-lg);
  font-weight: 600;
  color: var(--text-primary);
}

.section-header {
  margin-bottom: var(--space-4);
}

.section-subtitle {
  font-size: var(--text-lg);
  font-weight: 600;
  color: var(--text-primary);
}

.actions-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: var(--space-4);
  margin-bottom: var(--space-8);
}

.action-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-6);
  cursor: pointer;
  transition: all 0.15s ease;
  text-align: center;
}

.action-card:hover {
  box-shadow: var(--shadow-md);
  border-color: var(--color-primary);
}

.action-label {
  font-size: var(--text-base);
  font-weight: 500;
  color: var(--text-primary);
}

.action-desc {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
}
</style>
