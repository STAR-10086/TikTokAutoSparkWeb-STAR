<template>
  <div class="layout">
    <!-- Sidebar -->
    <aside class="sidebar">
      <div class="sidebar-header">
        <div class="sidebar-logo">
          <el-icon :size="24" color="var(--color-primary)">
            <Connection />
          </el-icon>
        </div>
        <span class="sidebar-title">TikTok Spark</span>
      </div>

      <nav class="sidebar-nav">
        <router-link
          v-for="item in menuItems"
          :key="item.path"
          :to="item.path"
          class="nav-item"
          :class="{ active: currentPath === item.path }"
        >
          <el-icon :size="20">
            <component :is="item.icon" />
          </el-icon>
          <span class="nav-label">{{ item.label }}</span>
          <span v-if="item.badge" class="nav-badge">{{ item.badge }}</span>
        </router-link>
      </nav>

      <div class="sidebar-footer">
        <div class="user-info">
          <el-icon :size="16"><User /></el-icon>
          <span>admin</span>
        </div>
        <button class="logout-btn" @click="handleLogout">
          <el-icon :size="16"><SwitchButton /></el-icon>
        </button>
      </div>
    </aside>

    <!-- Main Content -->
    <main class="main-content">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { useAppStore } from '../stores/app'
import {
  Connection,
  Odometer,
  User,
  ChatDotRound,
  Timer,
  Monitor,
  Setting,
  SwitchButton
} from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const appStore = useAppStore()

const currentPath = computed(() => route.path)

const menuItems = computed(() => [
  { path: '/dashboard', label: '仪表盘', icon: 'Odometer' },
  { path: '/friends', label: '好友列表', icon: 'User', badge: appStore.friends.length || null },
  { path: '/tasks', label: '定时任务', icon: 'Timer', badge: appStore.tasks.length || null },
  { path: '/browser', label: '浏览器', icon: 'Monitor' },
  { path: '/settings', label: '设置', icon: 'Setting' }
])

async function handleLogout() {
  await authStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.layout {
  display: flex;
  min-height: 100vh;
}

/* Sidebar */
.sidebar {
  width: 240px;
  background: #ffffff;
  border-right: var(--border);
  display: flex;
  flex-direction: column;
  position: fixed;
  top: 0;
  left: 0;
  bottom: 0;
  z-index: 100;
}

.sidebar-header {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-6);
  border-bottom: var(--border);
}

.sidebar-logo {
  width: 36px;
  height: 36px;
  border-radius: var(--radius-sm);
  background-color: #dbeafe;
  display: flex;
  align-items: center;
  justify-content: center;
}

.sidebar-title {
  font-size: var(--text-lg);
  font-weight: 600;
  color: var(--text-primary);
}

.sidebar-nav {
  flex: 1;
  padding: var(--space-4);
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.nav-item {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  border-radius: var(--radius-sm);
  color: var(--text-secondary);
  text-decoration: none;
  font-size: var(--text-sm);
  transition: all 0.15s ease;
}

.nav-item:hover {
  background-color: var(--color-neutral-100);
  color: var(--text-primary);
}

.nav-item.active {
  background-color: #dbeafe;
  color: var(--color-primary);
  font-weight: 500;
}

.nav-label {
  flex: 1;
}

.nav-badge {
  background-color: var(--color-primary);
  color: #ffffff;
  font-size: var(--text-xs);
  padding: 1px 8px;
  border-radius: 9999px;
  min-width: 20px;
  text-align: center;
}

.sidebar-footer {
  padding: var(--space-4) var(--space-6);
  border-top: var(--border);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.user-info {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--text-sm);
  color: var(--text-secondary);
}

.logout-btn {
  background: none;
  border: none;
  color: var(--text-tertiary);
  cursor: pointer;
  padding: var(--space-2);
  border-radius: var(--radius-sm);
  display: flex;
  align-items: center;
  justify-content: center;
}

.logout-btn:hover {
  background-color: var(--color-neutral-100);
  color: var(--color-error);
}

/* Main Content */
.main-content {
  flex: 1;
  margin-left: 240px;
  background-color: var(--color-neutral-50);
  min-height: 100vh;
}
</style>
