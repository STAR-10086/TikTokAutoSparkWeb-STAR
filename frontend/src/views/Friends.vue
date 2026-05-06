<template>
  <div class="page-container">
    <div class="page-header">
      <div>
        <h1 class="section-title">好友列表</h1>
        <p class="section-description">查看抖音好友及火花状态</p>
      </div>
      <el-button type="primary" :icon="Refresh" @click="refreshFriends" :loading="loading">
        刷新列表
      </el-button>
    </div>

    <div class="card">
      <el-table :data="friends" v-loading="loading" empty-text="暂无好友数据，请先初始化浏览器并登录">
        <el-table-column label="头像" width="80">
          <template #default="{ row }">
            <el-avatar :size="40" :src="row.avatar">
              {{ row.name?.charAt(0) }}
            </el-avatar>
          </template>
        </el-table-column>

        <el-table-column prop="name" label="好友昵称" min-width="200">
          <template #default="{ row }">
            <span class="friend-name">{{ row.name }}</span>
          </template>
        </el-table-column>

        <el-table-column label="火花状态" width="120">
          <template #default="{ row }">
            <span v-if="row.fire" class="fire-badge">
              <el-icon color="#f59e0b"><Sunny /></el-icon>
              {{ row.fire }}
            </span>
            <span v-else class="no-fire">-</span>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="160">
          <template #default="{ row }">
            <el-button
              type="primary"
              size="small"
              text
              @click="openSendDialog(row)"
            >
              发送消息
            </el-button>
            <el-button
              type="warning"
              size="small"
              text
              @click="openTaskDialog(row)"
            >
              定时任务
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- Send Message Dialog -->
    <el-dialog v-model="sendDialogVisible" title="发送消息" width="400px">
      <el-form :model="sendForm">
        <el-form-item label="好友">
          <el-input :model-value="sendForm.friend" disabled />
        </el-form-item>
        <el-form-item label="消息内容">
          <el-input
            v-model="sendForm.message"
            type="textarea"
            :rows="3"
            placeholder="输入要发送的消息..."
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="sendDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="sendMessage" :loading="sending">
          发送
        </el-button>
      </template>
    </el-dialog>

    <!-- Add Task Dialog -->
    <el-dialog v-model="taskDialogVisible" title="添加定时任务" width="400px">
      <el-form :model="taskForm">
        <el-form-item label="好友">
          <el-input :model-value="taskForm.friend" disabled />
        </el-form-item>
        <el-form-item label="发送时间">
          <el-time-picker
            v-model="taskForm.time"
            format="HH:mm"
            placeholder="选择时间"
            style="width: 100%"
          />
        </el-form-item>
        <el-form-item label="消息内容（可选）">
          <el-input
            v-model="taskForm.message"
            type="textarea"
            :rows="2"
            placeholder="留空则使用每日名言"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="taskDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="addTask" :loading="addingTask">
          添加
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh, Sunny } from '@element-plus/icons-vue'
import { useAppStore } from '../stores/app'

const appStore = useAppStore()
const loading = computed(() => appStore.loading)
const friends = computed(() => appStore.friends)

const sendDialogVisible = ref(false)
const taskDialogVisible = ref(false)
const sending = ref(false)
const addingTask = ref(false)

const sendForm = ref({
  friend: '',
  message: ''
})

const taskForm = ref({
  friend: '',
  time: null,
  message: ''
})

onMounted(() => {
  appStore.fetchFriends()
})

function refreshFriends() {
  appStore.fetchFriends()
}

function openSendDialog(row) {
  sendForm.value = { friend: row.name, message: '' }
  sendDialogVisible.value = true
}

function openTaskDialog(row) {
  taskForm.value = { friend: row.name, time: null, message: '' }
  taskDialogVisible.value = true
}

async function sendMessage() {
  if (!sendForm.value.message) {
    ElMessage.warning('请输入消息内容')
    return
  }
  sending.value = true
  // TODO: Call API to send message
  ElMessage.success('消息已发送')
  sending.value = false
  sendDialogVisible.value = false
}

async function addTask() {
  if (!taskForm.value.time) {
    ElMessage.warning('请选择发送时间')
    return
  }

  addingTask.value = true
  const hours = taskForm.value.time.getHours().toString().padStart(2, '0')
  const minutes = taskForm.value.time.getMinutes().toString().padStart(2, '0')
  const timeStr = `${hours}:${minutes}`

  const result = await appStore.addTask(timeStr, taskForm.value.friend, taskForm.value.message || null)
  addingTask.value = false

  if (result.code === 200) {
    ElMessage.success('定时任务已添加')
    taskDialogVisible.value = false
  } else {
    ElMessage.error(result.data)
  }
}
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: var(--space-6);
}

.friend-name {
  font-weight: 500;
  color: var(--text-primary);
}

.fire-badge {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  color: #f59e0b;
  font-weight: 500;
}

.no-fire {
  color: var(--text-tertiary);
}
</style>
