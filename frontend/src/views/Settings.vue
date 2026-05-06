<template>
  <div class="page-container">
    <h1 class="section-title">系统设置</h1>

    <!-- Change Password -->
    <div class="card settings-card">
      <h2 class="card-title">修改密码</h2>
      <p class="card-description">修改管理员登录密码</p>

      <el-form
        ref="passwordFormRef"
        :model="passwordForm"
        :rules="passwordRules"
        label-width="100px"
        style="max-width: 400px"
      >
        <el-form-item label="原密码" prop="oldPassword">
          <el-input
            v-model="passwordForm.oldPassword"
            type="password"
            show-password
          />
        </el-form-item>

        <el-form-item label="新密码" prop="newPassword">
          <el-input
            v-model="passwordForm.newPassword"
            type="password"
            show-password
          />
        </el-form-item>

        <el-form-item label="确认密码" prop="confirmPassword">
          <el-input
            v-model="passwordForm.confirmPassword"
            type="password"
            show-password
          />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="changePassword" :loading="changingPassword">
            保存
          </el-button>
        </el-form-item>
      </el-form>
    </div>

    <!-- System Info -->
    <div class="card settings-card">
      <h2 class="card-title">系统信息</h2>
      <p class="card-description">查看系统运行状态</p>

      <el-descriptions :column="1" border>
        <el-descriptions-item label="版本">{{ systemInfo.version }}</el-descriptions-item>
        <el-descriptions-item label="运行时间">{{ systemInfo.uptime }}</el-descriptions-item>
        <el-descriptions-item label="浏览器状态">
          <span v-if="systemInfo.browser_initialized" class="badge badge-success">已初始化</span>
          <span v-else class="badge badge-warning">未初始化</span>
        </el-descriptions-item>
        <el-descriptions-item label="登录状态">
          <span v-if="systemInfo.user_logged_in" class="badge badge-success">已登录</span>
          <span v-else class="badge badge-warning">未登录</span>
        </el-descriptions-item>
        <el-descriptions-item label="定时任务数">{{ systemInfo.scheduled_tasks }}</el-descriptions-item>
        <el-descriptions-item label="最后登录 IP">{{ systemInfo.last_login_ip }}</el-descriptions-item>
      </el-descriptions>

      <el-button style="margin-top: var(--space-4)" @click="refreshInfo">
        刷新信息
      </el-button>
    </div>

    <!-- About -->
    <div class="card settings-card">
      <h2 class="card-title">关于</h2>
      <p class="card-description">TikTok Auto Spark - 抖音自动续火花管理系统</p>

      <div class="about-info">
        <p>版本: 2.0.0</p>
        <p>基于 Vue 3 + FastAPI + Selenium 构建</p>
        <p>支持 Docker 容器化部署</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useAppStore } from '../stores/app'
import api from '../api'

const appStore = useAppStore()
const systemInfo = computed(() => appStore.systemInfo)

const passwordFormRef = ref(null)
const changingPassword = ref(false)

const passwordForm = ref({
  oldPassword: '',
  newPassword: '',
  confirmPassword: ''
})

const validateConfirmPassword = (rule, value, callback) => {
  if (value !== passwordForm.value.newPassword) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const passwordRules = {
  oldPassword: [{ required: true, message: '请输入原密码', trigger: 'blur' }],
  newPassword: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 4, message: '密码长度不能少于 4 位', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' }
  ]
}

onMounted(() => {
  appStore.fetchSystemInfo()
})

async function changePassword() {
  const valid = await passwordFormRef.value.validate().catch(() => false)
  if (!valid) return

  changingPassword.value = true
  try {
    const res = await api.post('/api/auth/change-password', {
      old_password: passwordForm.value.oldPassword,
      new_password: passwordForm.value.newPassword
    })

    if (res.data.code === 200) {
      ElMessage.success('密码修改成功')
      passwordForm.value = { oldPassword: '', newPassword: '', confirmPassword: '' }
    } else {
      ElMessage.error(res.data.data)
    }
  } catch (err) {
    ElMessage.error('修改失败')
  }
  changingPassword.value = false
}

function refreshInfo() {
  appStore.fetchSystemInfo()
  ElMessage.success('已刷新')
}
</script>

<style scoped>
.settings-card {
  margin-bottom: var(--space-6);
}

.card-title {
  font-size: var(--text-lg);
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: var(--space-1);
}

.card-description {
  font-size: var(--text-sm);
  color: var(--text-secondary);
  margin-bottom: var(--space-6);
}

.about-info {
  color: var(--text-secondary);
  font-size: var(--text-sm);
  line-height: 2;
}
</style>
