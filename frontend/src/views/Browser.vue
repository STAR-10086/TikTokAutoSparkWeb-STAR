<template>
  <div class="page-container">
    <h1 class="section-title">浏览器控制</h1>
    <p class="section-description">管理浏览器实例、登录抖音、查看截图</p>

    <!-- Status Section -->
    <div class="status-grid">
      <div class="card">
        <div class="status-header">
          <span class="status-label">浏览器状态</span>
          <span v-if="systemInfo.browser_initialized" class="badge badge-success">已初始化</span>
          <span v-else class="badge badge-warning">未初始化</span>
        </div>
        <div class="status-actions">
          <el-button
            type="primary"
            :icon="Monitor"
            @click="handleInit"
            :loading="initLoading"
            :disabled="systemInfo.browser_initialized"
          >
            初始化浏览器
          </el-button>
        </div>
      </div>

      <div class="card">
        <div class="status-header">
          <span class="status-label">登录状态</span>
          <span v-if="systemInfo.user_logged_in" class="badge badge-success">已登录</span>
          <span v-else class="badge badge-warning">未登录</span>
        </div>
        <div class="status-actions">
          <el-button
            type="success"
            :icon="Iphone"
            @click="showQrcode"
            :loading="qrcodeLoading"
            :disabled="!systemInfo.browser_initialized"
          >
            扫码登录
          </el-button>
          <el-button
            :icon="Switch"
            @click="checkLogin"
            :disabled="!systemInfo.browser_initialized"
          >
            检查状态
          </el-button>
        </div>
      </div>
    </div>

    <!-- Actions Section -->
    <div class="section-header">
      <h2 class="section-subtitle">操作</h2>
    </div>

    <div class="actions-grid">
      <div class="card action-card" @click="takeScreenshot" :class="{ disabled: !systemInfo.browser_initialized }">
        <el-icon :size="24" color="var(--color-primary)"><Camera /></el-icon>
        <span class="action-label">截图</span>
        <span class="action-desc">获取浏览器截图</span>
      </div>

      <div class="card action-card" @click="handleLogoutBrowser" :class="{ disabled: !systemInfo.browser_initialized }">
        <el-icon :size="24" color="var(--color-error)"><SwitchButton /></el-icon>
        <span class="action-label">退出登录</span>
        <span class="action-desc">清除 Cookie</span>
      </div>
    </div>

    <!-- QR Code Dialog -->
    <el-dialog v-model="qrcodeVisible" title="扫码登录" width="350px">
      <div class="qrcode-container">
        <img v-if="qrcodeSrc" :src="qrcodeSrc" class="qrcode-image" />
        <div v-else class="qrcode-placeholder">
          <el-icon :size="48" color="var(--text-tertiary)"><Loading /></el-icon>
          <span>正在获取二维码...</span>
        </div>
        <p class="qrcode-hint">请使用抖音 APP 扫描二维码登录</p>
      </div>
      <template #footer>
        <el-button @click="qrcodeVisible = false">关闭</el-button>
        <el-button type="primary" @click="showQrcode">刷新二维码</el-button>
      </template>
    </el-dialog>

    <!-- Screenshot Dialog -->
    <el-dialog v-model="screenshotVisible" title="浏览器截图" width="800px">
      <div class="screenshot-container">
        <img v-if="screenshotSrc" :src="screenshotSrc" class="screenshot-image" />
        <div v-else class="screenshot-placeholder">
          <el-icon :size="48" color="var(--text-tertiary)"><Loading /></el-icon>
          <span>正在截图...</span>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Monitor, Iphone, Switch, Camera, SwitchButton, Loading } from '@element-plus/icons-vue'
import { useAppStore } from '../stores/app'

const appStore = useAppStore()
const systemInfo = computed(() => appStore.systemInfo)

const initLoading = ref(false)
const qrcodeLoading = ref(false)
const qrcodeVisible = ref(false)
const qrcodeSrc = ref('')
const screenshotVisible = ref(false)
const screenshotSrc = ref('')

onMounted(() => {
  appStore.fetchSystemInfo()
})

async function handleInit() {
  initLoading.value = true
  const result = await appStore.initBrowser()
  initLoading.value = false

  if (result.code === 200) {
    ElMessage.success('浏览器初始化成功')
    appStore.fetchSystemInfo()
  } else {
    ElMessage.error(result.data)
  }
}

async function showQrcode() {
  qrcodeLoading.value = true
  qrcodeVisible.value = true
  qrcodeSrc.value = ''

  try {
    const res = await fetch('/api/browser/qrcode', {
      headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
    })
    const data = await res.json()

    if (data.code === 200) {
      qrcodeSrc.value = data.data
    } else {
      ElMessage.error(data.data)
    }
  } catch (err) {
    ElMessage.error('获取二维码失败')
  }

  qrcodeLoading.value = false
}

async function checkLogin() {
  await appStore.fetchSystemInfo()
  if (systemInfo.value.user_logged_in) {
    ElMessage.success('已登录')
  } else {
    ElMessage.warning('未登录')
  }
}

async function takeScreenshot() {
  if (!systemInfo.value.browser_initialized) return

  screenshotVisible.value = true
  screenshotSrc.value = ''

  const result = await appStore.getScreenshot()
  if (result.code === 200) {
    screenshotSrc.value = `data:image/png;base64,${result.data}`
  } else {
    ElMessage.error(result.data)
    screenshotVisible.value = false
  }
}

async function handleLogoutBrowser() {
  try {
    const res = await fetch('/api/browser/logout', {
      method: 'POST',
      headers: { Authorization: `Bearer ${localStorage.getItem('token')}` }
    })
    const data = await res.json()

    if (data.code === 200) {
      ElMessage.success('已退出登录')
      appStore.fetchSystemInfo()
    } else {
      ElMessage.error(data.data)
    }
  } catch {
    ElMessage.error('操作失败')
  }
}
</script>

<style scoped>
.status-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--space-4);
  margin-bottom: var(--space-8);
}

.status-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-4);
}

.status-label {
  font-size: var(--text-base);
  font-weight: 500;
  color: var(--text-primary);
}

.status-actions {
  display: flex;
  gap: var(--space-3);
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

.action-card:hover:not(.disabled) {
  box-shadow: var(--shadow-md);
  border-color: var(--color-primary);
}

.action-card.disabled {
  opacity: 0.5;
  cursor: not-allowed;
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

.qrcode-container {
  text-align: center;
  padding: var(--space-4);
}

.qrcode-image {
  max-width: 256px;
  margin-bottom: var(--space-4);
}

.qrcode-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-8);
  color: var(--text-tertiary);
}

.qrcode-hint {
  font-size: var(--text-sm);
  color: var(--text-secondary);
}

.screenshot-container {
  text-align: center;
}

.screenshot-image {
  max-width: 100%;
  border: var(--border);
  border-radius: var(--radius-sm);
}

.screenshot-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-12);
  color: var(--text-tertiary);
}
</style>
