<template>
  <div class="page-container">
    <div class="page-header">
      <div>
        <h1 class="section-title">远程桌面</h1>
        <p class="section-description">通过 noVNC 在浏览器中查看和控制容器桌面</p>
      </div>
      <div class="header-actions">
        <el-button :icon="Refresh" @click="reconnect">重新连接</el-button>
        <el-button :icon="FullScreen" @click="toggleFullscreen">全屏</el-button>
      </div>
    </div>

    <div class="vnc-card card">
      <div class="vnc-toolbar">
        <div class="toolbar-left">
          <span class="connection-status" :class="{ connected: isConnected }">
            <el-icon><Connection /></el-icon>
            {{ isConnected ? '已连接' : '未连接' }}
          </span>
        </div>
        <div class="toolbar-right">
          <el-button size="small" text @click="sendCtrlAltDel">Ctrl+Alt+Del</el-button>
        </div>
      </div>

      <div class="vnc-container" ref="vncContainer">
        <div v-if="!isConnected && !isConnecting" class="vnc-placeholder">
          <el-icon :size="48" color="var(--text-tertiary)"><Monitor /></el-icon>
          <p>正在连接到远程桌面...</p>
          <el-button type="primary" @click="connect">手动连接</el-button>
        </div>
        <div v-if="isConnecting" class="vnc-placeholder">
          <el-icon :size="48" class="loading-icon"><Loading /></el-icon>
          <p>正在建立连接...</p>
        </div>
        <div id="vnc-display" ref="vncDisplay"></div>
      </div>
    </div>

    <div class="vnc-info card">
      <h3>连接信息</h3>
      <el-descriptions :column="2" border>
        <el-descriptions-item label="noVNC 地址">
          {{ vncUrl }}
        </el-descriptions-item>
        <el-descriptions-item label="VNC 端口">5900</el-descriptions-item>
        <el-descriptions-item label="noVNC 端口">6080</el-descriptions-item>
        <el-descriptions-item label="VNC 密码">123456</el-descriptions-item>
      </el-descriptions>
      <p class="info-hint">提示：也可以使用 VNC Viewer 直接连接 {{ serverIp }}:5900</p>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh, FullScreen, Monitor, Connection, Loading } from '@element-plus/icons-vue'

const vncContainer = ref(null)
const vncDisplay = ref(null)
const isConnected = ref(false)
const isConnecting = ref(false)

let rfb = null

const serverIp = computed(() => {
  return window.location.hostname
})

const vncUrl = computed(() => {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
  return `${protocol}//${window.location.host}/websockify`
})

async function loadNoVNC() {
  return new Promise((resolve, reject) => {
    if (window.RFB) {
      resolve()
      return
    }

    const script = document.createElement('script')
    script.src = '/novnc/core/rfb.js'
    script.onload = () => resolve()
    script.onerror = () => reject(new Error('Failed to load noVNC'))
    document.head.appendChild(script)
  })
}

async function connect() {
  try {
    isConnecting.value = true
    await loadNoVNC()

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const url = `${protocol}//${window.location.host}/websockify`

    if (rfb) {
      rfb.disconnect()
    }

    rfb = new window.RFB(vncDisplay.value, url, {
      credentials: { password: '123456' }
    })

    rfb.addEventListener('connect', () => {
      isConnected.value = true
      isConnecting.value = false
      ElMessage.success('已连接到远程桌面')
    })

    rfb.addEventListener('disconnect', () => {
      isConnected.value = false
      isConnecting.value = false
    })

    rfb.addEventListener('credentials', (e) => {
      e.detail.credentials.password = '123456'
    })

    rfb.scaleViewport = true
    rfb.resizeSession = true
  } catch (err) {
    isConnecting.value = false
    ElMessage.error('连接失败: ' + err.message)
  }
}

function disconnect() {
  if (rfb) {
    rfb.disconnect()
    rfb = null
  }
  isConnected.value = false
}

function reconnect() {
  disconnect()
  setTimeout(connect, 500)
}

function toggleFullscreen() {
  if (vncContainer.value) {
    if (document.fullscreenElement) {
      document.exitFullscreen()
    } else {
      vncContainer.value.requestFullscreen()
    }
  }
}

function sendCtrlAltDel() {
  if (rfb) {
    rfb.sendCtrlAltDel()
  }
}

onMounted(() => {
  connect()
})

onUnmounted(() => {
  disconnect()
})
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: var(--space-6);
}

.header-actions {
  display: flex;
  gap: var(--space-3);
}

.vnc-card {
  padding: 0;
  overflow: hidden;
  margin-bottom: var(--space-6);
}

.vnc-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-3) var(--space-4);
  background: var(--color-neutral-50);
  border-bottom: var(--border);
}

.toolbar-left, .toolbar-right {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.connection-status {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--text-sm);
  color: var(--color-error);
}

.connection-status.connected {
  color: var(--color-success);
}

.vnc-container {
  position: relative;
  width: 100%;
  height: 600px;
  background: #1a1a1a;
  display: flex;
  align-items: center;
  justify-content: center;
}

.vnc-container:fullscreen {
  height: 100vh;
}

.vnc-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-4);
  color: var(--text-tertiary);
}

.loading-icon {
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

#vnc-display {
  width: 100%;
  height: 100%;
}

#vnc-display :deep(canvas) {
  width: 100% !important;
  height: 100% !important;
  object-fit: contain;
}

.vnc-info {
  margin-bottom: var(--space-6);
}

.vnc-info h3 {
  font-size: var(--text-base);
  font-weight: 600;
  margin-bottom: var(--space-4);
}

.info-hint {
  margin-top: var(--space-4);
  font-size: var(--text-sm);
  color: var(--text-secondary);
}
</style>
