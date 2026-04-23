<template>
  <div class="space-y-8">
    <section v-if="isLoading && !localSettings" class="ui-panel text-sm text-muted-foreground">
      正在加载设置...
    </section>

    <section v-else class="ui-panel">
      <div class="flex items-center justify-between gap-4">
        <div>
          <p class="ui-section-title">配置面板</p>
          <p class="mt-1 text-xs text-muted-foreground">
            保留原来的邮箱与注册配置方式，刷新服务需要的参数也继续在这里统一维护。
          </p>
        </div>

        <Button
          size="xs"
          variant="primary"
          root-class="min-w-14 justify-center"
          :disabled="isSaving || !localSettings"
          @click="handleSave"
        >
          {{ isSaving ? '保存中...' : '保存设置' }}
        </Button>
      </div>

      <div
        v-if="errorMessage"
        class="mt-4 rounded-2xl bg-destructive/10 px-4 py-3 text-sm text-destructive"
      >
        {{ errorMessage }}
      </div>

      <div v-if="localSettings" class="mt-6 space-y-8">
        <div class="grid gap-4 lg:grid-cols-3">
          <div class="space-y-4">
            <div class="ui-card">
              <p class="ui-section-kicker">基础</p>
              <div class="mt-4 space-y-3">
                <div class="flex items-center justify-between gap-2 text-xs text-muted-foreground">
                  <label class="block">API 密钥</label>
                  <HelpTip text="支持多个密钥，用逗号分隔。例如：key1,key2,key3" />
                </div>
                <Input
                  v-model="localSettings.basic.api_key"
                  type="text"
                  block
                  placeholder="可选，多个密钥用逗号分隔"
                />

                <label class="block text-xs text-muted-foreground">基础地址</label>
                <Input
                  v-model="localSettings.basic.base_url"
                  type="text"
                  block
                  placeholder="自动检测或手动填写"
                />

                <div class="flex items-center justify-between gap-2 text-xs text-muted-foreground">
                  <span>聊天代理</span>
                  <HelpTip text="用于 JWT、会话和消息请求；留空表示直连。" />
                </div>
                <Input
                  v-model="localSettings.basic.proxy_for_chat"
                  type="text"
                  block
                  placeholder="http://127.0.0.1:7890"
                />
              </div>
            </div>

            <div class="ui-card">
              <p class="ui-section-kicker">重试</p>
              <div class="mt-4 grid grid-cols-2 gap-3">
                <label class="col-span-2 text-xs text-muted-foreground">账户切换次数</label>
                <Input
                  v-model="maxAccountSwitchTriesInput"
                  type="number"
                  block
                  root-class="col-span-2"
                />

                <label class="col-span-2 text-xs text-muted-foreground">对话冷却（小时）</label>
                <Input
                  v-model="textCooldownHoursInput"
                  type="number"
                  block
                  root-class="col-span-2"
                />

                <label class="col-span-2 text-xs text-muted-foreground">绘图冷却（小时）</label>
                <Input
                  v-model="imagesCooldownHoursInput"
                  type="number"
                  block
                  root-class="col-span-2"
                />

                <label class="col-span-2 text-xs text-muted-foreground">视频冷却（小时）</label>
                <Input
                  v-model="videosCooldownHoursInput"
                  type="number"
                  block
                  root-class="col-span-2"
                />

                <label class="col-span-2 text-xs text-muted-foreground">会话缓存秒数</label>
                <Input
                  v-model="sessionCacheTtlInput"
                  type="number"
                  block
                  root-class="col-span-2"
                />
              </div>
            </div>
          </div>

          <div class="space-y-4">
            <div class="ui-card">
              <div class="flex items-center justify-between gap-2">
                <p class="ui-section-kicker">邮箱与注册</p>
                <HelpTip text="这里继续保留原来的邮箱下拉和按服务商分段配置，便于独立刷新服务直接复用。" />
              </div>

              <div class="mt-4 space-y-3">
                <div class="flex items-center justify-between gap-2 text-xs text-muted-foreground">
                  <span>账户操作代理</span>
                  <HelpTip text="用于注册、登录、刷新流程；临时邮箱开启代理时也会走这个地址。" />
                </div>
                <Input
                  v-model="localSettings.refresh_settings.proxy_for_auth"
                  type="text"
                  block
                  placeholder="http://127.0.0.1:7890"
                />

                <div class="flex items-center justify-between gap-2 text-xs text-muted-foreground">
                  <span>浏览器模式</span>
                  <HelpTip text="normal 为正常窗口；silent 为静默窗口；headless 为无头。" />
                </div>
                <SelectMenu
                  v-model="localSettings.refresh_settings.browser_mode"
                  :options="browserModeOptions"
                  class="w-full"
                />

                <div class="flex items-center justify-between gap-2 text-xs text-muted-foreground">
                  <span>临时邮箱服务</span>
                  <HelpTip text="恢复为下拉选择，不同服务商展示各自配置项。" />
                </div>
                <SelectMenu
                  v-model="localSettings.refresh_settings.temp_mail_provider"
                  :options="tempMailProviderOptions"
                  class="w-full"
                />

                <Checkbox v-model="localSettings.refresh_settings.mail_proxy_enabled">
                  启用邮箱代理（使用账户操作代理）
                </Checkbox>

                <template v-if="localSettings.refresh_settings.temp_mail_provider === 'duckmail'">
                  <Checkbox v-model="localSettings.refresh_settings.duckmail.verify_ssl">
                    DuckMail SSL 校验
                  </Checkbox>

                  <label class="block text-xs text-muted-foreground">DuckMail API 地址</label>
                  <Input
                    v-model="localSettings.refresh_settings.duckmail.base_url"
                    type="text"
                    block
                    placeholder="https://api.duckmail.sbs"
                  />

                  <label class="block text-xs text-muted-foreground">DuckMail API 密钥</label>
                  <Input
                    v-model="localSettings.refresh_settings.duckmail.api_key"
                    type="text"
                    block
                    placeholder="dk_xxx"
                  />

                  <label class="block text-xs text-muted-foreground">DuckMail 域名（推荐）</label>
                  <Input
                    v-model="localSettings.refresh_settings.register_domain"
                    type="text"
                    block
                    placeholder="留空则自动选择"
                  />
                </template>

                <template v-if="localSettings.refresh_settings.temp_mail_provider === 'moemail'">
                  <label class="block text-xs text-muted-foreground">Moemail API 地址</label>
                  <Input
                    v-model="localSettings.refresh_settings.moemail.base_url"
                    type="text"
                    block
                    placeholder="https://moemail.nanohajimi.mom"
                  />

                  <label class="block text-xs text-muted-foreground">Moemail API 密钥</label>
                  <Input
                    v-model="localSettings.refresh_settings.moemail.api_key"
                    type="text"
                    block
                    placeholder="X-API-Key"
                  />

                  <label class="block text-xs text-muted-foreground">Moemail 域名（可选）</label>
                  <Input
                    v-model="localSettings.refresh_settings.moemail.domain"
                    type="text"
                    block
                    placeholder="留空则随机"
                  />
                </template>

                <template v-if="localSettings.refresh_settings.temp_mail_provider === 'freemail'">
                  <Checkbox v-model="localSettings.refresh_settings.freemail.verify_ssl">
                    Freemail SSL 校验
                  </Checkbox>

                  <label class="block text-xs text-muted-foreground">Freemail API 地址</label>
                  <Input
                    v-model="localSettings.refresh_settings.freemail.base_url"
                    type="text"
                    block
                    placeholder="http://your-freemail-server.com"
                  />

                  <label class="block text-xs text-muted-foreground">Freemail JWT Token</label>
                  <Input
                    v-model="localSettings.refresh_settings.freemail.jwt_token"
                    type="text"
                    block
                    placeholder="eyJ..."
                  />

                  <label class="block text-xs text-muted-foreground">Freemail 域名（可选）</label>
                  <Input
                    v-model="localSettings.refresh_settings.freemail.domain"
                    type="text"
                    block
                    placeholder="留空则随机"
                  />
                </template>

                <template v-if="localSettings.refresh_settings.temp_mail_provider === 'gptmail'">
                  <Checkbox v-model="localSettings.refresh_settings.gptmail.verify_ssl">
                    GPTMail SSL 校验
                  </Checkbox>

                  <label class="block text-xs text-muted-foreground">GPTMail API 地址</label>
                  <Input
                    v-model="localSettings.refresh_settings.gptmail.base_url"
                    type="text"
                    block
                    placeholder="https://mail.chatgpt.org.uk"
                  />

                  <label class="block text-xs text-muted-foreground">GPTMail API 密钥</label>
                  <Input
                    v-model="localSettings.refresh_settings.gptmail.api_key"
                    type="text"
                    block
                    placeholder="X-API-Key"
                  />

                  <label class="block text-xs text-muted-foreground">GPTMail 域名（可选）</label>
                  <Input
                    v-model="localSettings.refresh_settings.gptmail.domain"
                    type="text"
                    block
                    placeholder="留空则随机"
                  />
                </template>

                <template v-if="localSettings.refresh_settings.temp_mail_provider === 'cfmail'">
                  <Checkbox v-model="localSettings.refresh_settings.cfmail.verify_ssl">
                    Cloudflare Mail SSL 校验
                  </Checkbox>

                  <label class="block text-xs text-muted-foreground">Cloudflare Mail API 地址</label>
                  <Input
                    v-model="localSettings.refresh_settings.cfmail.base_url"
                    type="text"
                    block
                    placeholder="https://your-cfmail-instance.example.com"
                  />

                  <label class="block text-xs text-muted-foreground">访问密码（可选）</label>
                  <Input
                    v-model="localSettings.refresh_settings.cfmail.api_key"
                    type="text"
                    block
                    placeholder="留空则不使用密码"
                  />

                  <label class="block text-xs text-muted-foreground">邮箱域名（可选）</label>
                  <Input
                    v-model="localSettings.refresh_settings.cfmail.domain"
                    type="text"
                    block
                    placeholder="留空则随机"
                  />
                </template>

                <label class="block text-xs text-muted-foreground">默认注册数量</label>
                <Input
                  v-model="registerDefaultCountInput"
                  type="number"
                  block
                />
              </div>
            </div>

            <div class="ui-card">
              <p class="ui-section-kicker">刷新调度</p>
              <div class="mt-4 space-y-3">
                <Checkbox v-model="localSettings.refresh_settings.auto_register_enabled">
                  启用自动补量
                </Checkbox>

                <Checkbox v-model="localSettings.refresh_settings.delete_expired_accounts">
                  自动删除过期账号
                </Checkbox>

                <label class="block text-xs text-muted-foreground">最低账号数量</label>
                <Input
                  v-model="minAccountCountInput"
                  type="number"
                  block
                />

                <label class="block text-xs text-muted-foreground">刷新窗口（小时）</label>
                <Input
                  v-model="refreshWindowHoursInput"
                  type="number"
                  block
                />

                <label class="block text-xs text-muted-foreground">账号列表重载间隔（秒）</label>
                <Input
                  v-model="autoRefreshAccountsSecondsInput"
                  type="number"
                  block
                />

                <Checkbox v-model="localSettings.refresh_settings.scheduled_refresh_enabled">
                  启用定时刷新
                </Checkbox>

                <label class="block text-xs text-muted-foreground">定时轮询间隔（分钟）</label>
                <Input
                  v-model="scheduledRefreshIntervalMinutesInput"
                  type="number"
                  block
                />

                <label class="block text-xs text-muted-foreground">定时表达式</label>
                <Input
                  v-model="localSettings.refresh_settings.scheduled_refresh_cron"
                  type="text"
                  block
                  placeholder="08:00,20:00 或 */120"
                />

                <label class="block text-xs text-muted-foreground">验证码重发次数</label>
                <Input
                  v-model="verificationCodeResendCountInput"
                  type="number"
                  block
                />

                <label class="block text-xs text-muted-foreground">单批刷新数量</label>
                <Input
                  v-model="refreshBatchSizeInput"
                  type="number"
                  block
                />

                <label class="block text-xs text-muted-foreground">批次间隔（分钟）</label>
                <Input
                  v-model="refreshBatchIntervalMinutesInput"
                  type="number"
                  block
                />

                <label class="block text-xs text-muted-foreground">刷新冷却（小时）</label>
                <Input
                  v-model="refreshCooldownHoursInput"
                  type="number"
                  block
                />
              </div>
            </div>
          </div>

          <div class="space-y-4">
            <div class="ui-card">
              <div class="flex items-center justify-between gap-2">
                <p class="ui-section-kicker">图像生成</p>
                <HelpTip text="不建议默认开启图像生成，若要稳定出图更推荐专门的图像模型。" />
              </div>
              <div class="mt-4 space-y-3">
                <Checkbox v-model="localSettings.image_generation.enabled">
                  启用图像生成
                </Checkbox>

                <label class="block text-xs text-muted-foreground">输出格式</label>
                <SelectMenu
                  v-model="localSettings.image_generation.output_format"
                  :options="imageOutputOptions"
                  placement="up"
                  class="w-full"
                />

                <label class="block text-xs text-muted-foreground">支持模型</label>
                <SelectMenu
                  v-model="localSettings.image_generation.supported_models"
                  :options="imageModelOptions"
                  placeholder="选择模型"
                  placement="up"
                  multiple
                  class="w-full"
                />
              </div>
            </div>

            <div class="ui-card">
              <p class="ui-section-kicker">视频生成</p>
              <div class="mt-4 space-y-3">
                <label class="block text-xs text-muted-foreground">输出格式</label>
                <SelectMenu
                  v-model="localSettings.video_generation.output_format"
                  :options="videoOutputOptions"
                  placement="up"
                  class="w-full"
                />
              </div>
            </div>

            <div class="ui-card">
              <div class="flex items-center justify-between gap-2">
                <p class="ui-section-kicker">每日配额</p>
                <HelpTip text="达到上限后会自动切换账号。0 表示不限制该类型。" />
              </div>
              <div class="mt-4 space-y-3">
                <Checkbox v-model="localSettings.quota_limits.enabled">
                  启用主动配额计数
                </Checkbox>

                <label class="block text-xs text-muted-foreground">对话每日上限</label>
                <Input
                  v-model="quotaTextDailyLimitInput"
                  type="number"
                  block
                  placeholder="120"
                />

                <label class="block text-xs text-muted-foreground">绘图每日上限</label>
                <Input
                  v-model="quotaImagesDailyLimitInput"
                  type="number"
                  block
                  placeholder="2"
                />

                <label class="block text-xs text-muted-foreground">视频每日上限</label>
                <Input
                  v-model="quotaVideosDailyLimitInput"
                  type="number"
                  block
                  placeholder="1"
                />
              </div>
            </div>

            <div class="ui-card">
              <p class="ui-section-kicker">公开展示</p>
              <div class="mt-4 space-y-3">
                <label class="block text-xs text-muted-foreground">Logo 地址</label>
                <Input
                  v-model="localSettings.public_display.logo_url"
                  type="text"
                  block
                  placeholder="logo 地址"
                />

                <label class="block text-xs text-muted-foreground">聊天入口</label>
                <Input
                  v-model="localSettings.public_display.chat_url"
                  type="text"
                  block
                  placeholder="聊天入口地址"
                />

                <label class="block text-xs text-muted-foreground">会话有效时长（小时）</label>
                <Input
                  v-model="sessionExpireHoursInput"
                  type="number"
                  block
                />
              </div>
            </div>

            <div class="ui-card">
              <p class="ui-section-kicker">说明</p>
              <div class="mt-4 space-y-3 text-sm text-muted-foreground">
                <p>设置页已经恢复成旧版交互思路：邮箱提供商下拉选择，按服务商分别填写。</p>
                <p>保存时会同时同步 `basic / retry / refresh_settings`，避免旧值把新改动覆盖掉。</p>
                <p>没有重新加回当前后端未支持的 `browser_engine` 和 `samplemail` 专属字段，避免再次出现保存错乱。</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { Button, Checkbox, HelpTip, Input, SelectMenu } from 'nanocat-ui'
import { useToast } from '@/composables/useToast'
import { useSettingsStore } from '@/stores/settings'
import type { RefreshSettings, Settings } from '@/types/api'

const settingsStore = useSettingsStore()
const { settings, isLoading } = storeToRefs(settingsStore)
const toast = useToast()

const localSettings = ref<Settings | null>(null)
const isSaving = ref(false)
const errorMessage = ref('')

const DEFAULT_COOLDOWN_HOURS = {
  text: 2,
  images: 4,
  videos: 4,
} as const

const browserModeOptions = [
  { label: 'normal - 正常窗口', value: 'normal' },
  { label: 'silent - 静默窗口', value: 'silent' },
  { label: 'headless - 无头', value: 'headless' },
]

const tempMailProviderOptions = [
  { label: 'DuckMail', value: 'duckmail' },
  { label: 'Moemail', value: 'moemail' },
  { label: 'Freemail', value: 'freemail' },
  { label: 'GPTMail', value: 'gptmail' },
  { label: 'Cloudflare Mail', value: 'cfmail' },
]

const imageOutputOptions = [
  { label: 'Base64 编码', value: 'base64' },
  { label: 'URL 链接', value: 'url' },
]

const videoOutputOptions = [
  { label: 'HTML 视频标签', value: 'html' },
  { label: 'URL 链接', value: 'url' },
  { label: 'Markdown 格式', value: 'markdown' },
]

const clampInteger = (
  value: number,
  min: number,
  max: number = Number.MAX_SAFE_INTEGER,
) => Math.max(min, Math.min(max, Math.round(value)))

const clampDecimal = (value: number, min: number, max: number) =>
  Number(Math.max(min, Math.min(max, value)).toFixed(1))

const pickString = (fallback: string, ...values: Array<string | undefined>) => {
  for (const value of values) {
    if (typeof value === 'string') return value
  }
  return fallback
}

const pickNumber = (fallback: number, ...values: Array<number | undefined>) => {
  for (const value of values) {
    if (Number.isFinite(value)) return Number(value)
  }
  return fallback
}

const pickBoolean = (fallback: boolean, ...values: Array<boolean | undefined>) => {
  for (const value of values) {
    if (typeof value === 'boolean') return value
  }
  return fallback
}

const normalizeBrowserMode = (
  mode: string | undefined,
  headless: boolean | undefined,
): RefreshSettings['browser_mode'] => {
  if (mode === 'normal' || mode === 'silent' || mode === 'headless') {
    return mode
  }
  return headless ? 'headless' : 'normal'
}

const normalizeTempMailProvider = (
  value: string | undefined,
): RefreshSettings['temp_mail_provider'] => {
  if (
    value === 'duckmail'
    || value === 'moemail'
    || value === 'freemail'
    || value === 'gptmail'
    || value === 'cfmail'
  ) {
    return value
  }
  return 'duckmail'
}

const toCooldownHours = (seconds: number | undefined, fallbackHours: number) => {
  if (!seconds) return fallbackHours
  return Math.max(1, Math.round(seconds / 3600))
}

const createNumberInputBinding = (
  getter: () => number | undefined,
  setter: (value: number) => void,
  normalize: (value: number) => number = (value) => value,
) => computed({
  get: () => {
    const value = getter()
    return Number.isFinite(value) ? String(value) : ''
  },
  set: (raw: string | number) => {
    const parsed = typeof raw === 'number' ? raw : Number(String(raw).trim())
    if (Number.isFinite(parsed)) {
      setter(normalize(parsed))
    }
  },
})

const createCooldownHoursBinding = (
  key: 'text_rate_limit_cooldown_seconds' | 'images_rate_limit_cooldown_seconds' | 'videos_rate_limit_cooldown_seconds',
  fallbackHours: number,
  maxHours = 24,
) => createNumberInputBinding(
  () => toCooldownHours(localSettings.value?.retry?.[key], fallbackHours),
  (value) => {
    if (localSettings.value?.retry) {
      localSettings.value.retry[key] = value * 3600
    }
  },
  (value) => clampInteger(value, 1, maxHours),
)

const createRefreshNumberBinding = (
  getter: () => number | undefined,
  setter: (value: number) => void,
  min: number,
  max: number,
) => createNumberInputBinding(getter, setter, (value) => clampInteger(value, min, max))

const maxAccountSwitchTriesInput = createNumberInputBinding(
  () => localSettings.value?.retry?.max_account_switch_tries,
  (value) => {
    if (localSettings.value?.retry) {
      localSettings.value.retry.max_account_switch_tries = value
    }
  },
  (value) => clampInteger(value, 1, 20),
)

const textCooldownHoursInput = createCooldownHoursBinding(
  'text_rate_limit_cooldown_seconds',
  DEFAULT_COOLDOWN_HOURS.text,
)

const imagesCooldownHoursInput = createCooldownHoursBinding(
  'images_rate_limit_cooldown_seconds',
  DEFAULT_COOLDOWN_HOURS.images,
)

const videosCooldownHoursInput = createCooldownHoursBinding(
  'videos_rate_limit_cooldown_seconds',
  DEFAULT_COOLDOWN_HOURS.videos,
)

const sessionCacheTtlInput = createNumberInputBinding(
  () => localSettings.value?.retry?.session_cache_ttl_seconds,
  (value) => {
    if (localSettings.value?.retry) {
      localSettings.value.retry.session_cache_ttl_seconds = value
    }
  },
  (value) => clampInteger(value, 0, 86400),
)

const registerDefaultCountInput = createRefreshNumberBinding(
  () => localSettings.value?.refresh_settings?.register_default_count,
  (value) => {
    if (localSettings.value?.refresh_settings) {
      localSettings.value.refresh_settings.register_default_count = value
    }
  },
  1,
  200,
)

const refreshWindowHoursInput = createRefreshNumberBinding(
  () => localSettings.value?.refresh_settings?.refresh_window_hours,
  (value) => {
    if (localSettings.value?.refresh_settings) {
      localSettings.value.refresh_settings.refresh_window_hours = value
    }
  },
  0,
  24,
)

const autoRefreshAccountsSecondsInput = createRefreshNumberBinding(
  () => localSettings.value?.refresh_settings?.auto_refresh_accounts_seconds,
  (value) => {
    if (localSettings.value?.refresh_settings) {
      localSettings.value.refresh_settings.auto_refresh_accounts_seconds = value
    }
  },
  0,
  86400,
)

const scheduledRefreshIntervalMinutesInput = createRefreshNumberBinding(
  () => localSettings.value?.refresh_settings?.scheduled_refresh_interval_minutes,
  (value) => {
    if (localSettings.value?.refresh_settings) {
      localSettings.value.refresh_settings.scheduled_refresh_interval_minutes = value
    }
  },
  0,
  720,
)

const verificationCodeResendCountInput = createRefreshNumberBinding(
  () => localSettings.value?.refresh_settings?.verification_code_resend_count,
  (value) => {
    if (localSettings.value?.refresh_settings) {
      localSettings.value.refresh_settings.verification_code_resend_count = value
    }
  },
  0,
  5,
)

const refreshBatchSizeInput = createRefreshNumberBinding(
  () => localSettings.value?.refresh_settings?.refresh_batch_size,
  (value) => {
    if (localSettings.value?.refresh_settings) {
      localSettings.value.refresh_settings.refresh_batch_size = value
    }
  },
  1,
  50,
)

const refreshBatchIntervalMinutesInput = createRefreshNumberBinding(
  () => localSettings.value?.refresh_settings?.refresh_batch_interval_minutes,
  (value) => {
    if (localSettings.value?.refresh_settings) {
      localSettings.value.refresh_settings.refresh_batch_interval_minutes = value
    }
  },
  0,
  720,
)

const refreshCooldownHoursInput = createNumberInputBinding(
  () => localSettings.value?.refresh_settings?.refresh_cooldown_hours,
  (value) => {
    if (localSettings.value?.refresh_settings) {
      localSettings.value.refresh_settings.refresh_cooldown_hours = value
    }
  },
  (value) => clampDecimal(value, 0, 168),
)

const minAccountCountInput = createRefreshNumberBinding(
  () => localSettings.value?.refresh_settings?.min_account_count,
  (value) => {
    if (localSettings.value?.refresh_settings) {
      localSettings.value.refresh_settings.min_account_count = value
    }
  },
  0,
  1000,
)

const quotaTextDailyLimitInput = createNumberInputBinding(
  () => localSettings.value?.quota_limits?.text_daily_limit,
  (value) => {
    if (localSettings.value?.quota_limits) {
      localSettings.value.quota_limits.text_daily_limit = value
    }
  },
  (value) => clampInteger(value, 0, 999999),
)

const quotaImagesDailyLimitInput = createNumberInputBinding(
  () => localSettings.value?.quota_limits?.images_daily_limit,
  (value) => {
    if (localSettings.value?.quota_limits) {
      localSettings.value.quota_limits.images_daily_limit = value
    }
  },
  (value) => clampInteger(value, 0, 999999),
)

const quotaVideosDailyLimitInput = createNumberInputBinding(
  () => localSettings.value?.quota_limits?.videos_daily_limit,
  (value) => {
    if (localSettings.value?.quota_limits) {
      localSettings.value.quota_limits.videos_daily_limit = value
    }
  },
  (value) => clampInteger(value, 0, 999999),
)

const sessionExpireHoursInput = createNumberInputBinding(
  () => localSettings.value?.session?.expire_hours,
  (value) => {
    if (localSettings.value?.session) {
      localSettings.value.session.expire_hours = value
    }
  },
  (value) => clampInteger(value, 1, 168),
)

const imageModelOptions = computed(() => {
  const options = [
    { label: 'Gemini 3 Pro Preview', value: 'gemini-3-pro-preview' },
    { label: 'Gemini 3.1 Pro Preview', value: 'gemini-3.1-pro-preview' },
    { label: 'Gemini 3 Flash Preview', value: 'gemini-3-flash-preview' },
    { label: 'Gemini 2.5 Pro', value: 'gemini-2.5-pro' },
    { label: 'Gemini 2.5 Flash', value: 'gemini-2.5-flash' },
    { label: 'Gemini Auto', value: 'gemini-auto' },
  ]

  const selected = localSettings.value?.image_generation.supported_models || []
  for (const value of selected) {
    if (!options.some((option) => option.value === value)) {
      options.push({ label: value, value })
    }
  }

  return options
})

const createDefaultRefreshSettings = (): RefreshSettings => ({
  proxy_for_auth: '',
  duckmail: {
    base_url: 'https://api.duckmail.sbs',
    api_key: '',
    verify_ssl: true,
  },
  temp_mail_provider: 'duckmail',
  moemail: {
    base_url: 'https://moemail.nanohajimi.mom',
    api_key: '',
    domain: '',
  },
  freemail: {
    base_url: 'http://your-freemail-server.com',
    jwt_token: '',
    verify_ssl: true,
    domain: '',
  },
  mail_proxy_enabled: false,
  gptmail: {
    base_url: 'https://mail.chatgpt.org.uk',
    api_key: '',
    verify_ssl: true,
    domain: '',
  },
  cfmail: {
    base_url: '',
    api_key: '',
    verify_ssl: true,
    domain: '',
  },
  browser_mode: 'normal',
  browser_headless: false,
  refresh_window_hours: 1,
  register_domain: '',
  register_default_count: 20,
  auto_refresh_accounts_seconds: 60,
  scheduled_refresh_enabled: false,
  scheduled_refresh_interval_minutes: 30,
  scheduled_refresh_cron: '',
  verification_code_resend_count: 2,
  refresh_batch_size: 5,
  refresh_batch_interval_minutes: 30,
  refresh_cooldown_hours: 12,
  delete_expired_accounts: false,
  auto_register_enabled: false,
  min_account_count: 0,
})

const hydrateRefreshSettings = (source: Settings): RefreshSettings => {
  const defaults = createDefaultRefreshSettings()
  const current = source.refresh_settings || defaults
  const browserMode = normalizeBrowserMode(
    current.browser_mode ?? source.basic?.browser_mode,
    current.browser_headless ?? source.basic?.browser_headless,
  )

  return {
    ...defaults,
    ...current,
    proxy_for_auth: pickString(
      defaults.proxy_for_auth || '',
      current.proxy_for_auth,
      source.basic?.proxy_for_auth,
    ),
    temp_mail_provider: normalizeTempMailProvider(
      current.temp_mail_provider ?? source.basic?.temp_mail_provider,
    ),
    mail_proxy_enabled: pickBoolean(
      defaults.mail_proxy_enabled || false,
      current.mail_proxy_enabled,
      source.basic?.mail_proxy_enabled,
    ),
    browser_mode: browserMode,
    browser_headless: browserMode === 'headless',
    refresh_window_hours: pickNumber(
      defaults.refresh_window_hours || 1,
      current.refresh_window_hours,
      source.basic?.refresh_window_hours,
    ),
    register_domain: pickString(
      defaults.register_domain || '',
      current.register_domain,
      source.basic?.register_domain,
    ),
    register_default_count: pickNumber(
      defaults.register_default_count || 20,
      current.register_default_count,
      source.basic?.register_default_count,
    ),
    auto_refresh_accounts_seconds: pickNumber(
      defaults.auto_refresh_accounts_seconds || 60,
      current.auto_refresh_accounts_seconds,
      source.retry?.auto_refresh_accounts_seconds,
    ),
    scheduled_refresh_enabled: pickBoolean(
      defaults.scheduled_refresh_enabled || false,
      current.scheduled_refresh_enabled,
      source.retry?.scheduled_refresh_enabled,
    ),
    scheduled_refresh_interval_minutes: pickNumber(
      defaults.scheduled_refresh_interval_minutes || 30,
      current.scheduled_refresh_interval_minutes,
      source.retry?.scheduled_refresh_interval_minutes,
    ),
    scheduled_refresh_cron: pickString(
      defaults.scheduled_refresh_cron || '',
      current.scheduled_refresh_cron,
      source.retry?.scheduled_refresh_cron,
    ),
    verification_code_resend_count: pickNumber(
      defaults.verification_code_resend_count || 2,
      current.verification_code_resend_count,
      source.retry?.verification_code_resend_count,
    ),
    refresh_batch_size: pickNumber(
      defaults.refresh_batch_size || 5,
      current.refresh_batch_size,
      source.retry?.refresh_batch_size,
    ),
    refresh_batch_interval_minutes: pickNumber(
      defaults.refresh_batch_interval_minutes || 30,
      current.refresh_batch_interval_minutes,
      source.retry?.refresh_batch_interval_minutes,
    ),
    refresh_cooldown_hours: pickNumber(
      defaults.refresh_cooldown_hours || 12,
      current.refresh_cooldown_hours,
      source.retry?.refresh_cooldown_hours,
    ),
    delete_expired_accounts: pickBoolean(
      defaults.delete_expired_accounts || false,
      current.delete_expired_accounts,
      source.retry?.delete_expired_accounts,
    ),
    auto_register_enabled: pickBoolean(
      defaults.auto_register_enabled || false,
      current.auto_register_enabled,
      source.retry?.auto_register_enabled,
    ),
    min_account_count: pickNumber(
      defaults.min_account_count || 0,
      current.min_account_count,
      source.retry?.min_account_count,
    ),
    duckmail: {
      ...defaults.duckmail,
      ...current.duckmail,
      base_url: pickString(
        defaults.duckmail.base_url || '',
        current.duckmail?.base_url,
        source.basic?.duckmail_base_url,
      ),
      api_key: pickString(
        defaults.duckmail.api_key || '',
        current.duckmail?.api_key,
        source.basic?.duckmail_api_key,
      ),
      verify_ssl: pickBoolean(
        defaults.duckmail.verify_ssl || false,
        current.duckmail?.verify_ssl,
        source.basic?.duckmail_verify_ssl,
      ),
    },
    moemail: {
      ...defaults.moemail,
      ...current.moemail,
      base_url: pickString(
        defaults.moemail.base_url || '',
        current.moemail?.base_url,
        source.basic?.moemail_base_url,
      ),
      api_key: pickString(
        defaults.moemail.api_key || '',
        current.moemail?.api_key,
        source.basic?.moemail_api_key,
      ),
      domain: pickString(
        defaults.moemail.domain || '',
        current.moemail?.domain,
        source.basic?.moemail_domain,
      ),
    },
    freemail: {
      ...defaults.freemail,
      ...current.freemail,
      base_url: pickString(
        defaults.freemail.base_url || '',
        current.freemail?.base_url,
        source.basic?.freemail_base_url,
      ),
      jwt_token: pickString(
        defaults.freemail.jwt_token || '',
        current.freemail?.jwt_token,
        source.basic?.freemail_jwt_token,
      ),
      verify_ssl: pickBoolean(
        defaults.freemail.verify_ssl || false,
        current.freemail?.verify_ssl,
        source.basic?.freemail_verify_ssl,
      ),
      domain: pickString(
        defaults.freemail.domain || '',
        current.freemail?.domain,
        source.basic?.freemail_domain,
      ),
    },
    gptmail: {
      ...defaults.gptmail,
      ...current.gptmail,
      base_url: pickString(
        defaults.gptmail.base_url || '',
        current.gptmail?.base_url,
        source.basic?.gptmail_base_url,
      ),
      api_key: pickString(
        defaults.gptmail.api_key || '',
        current.gptmail?.api_key,
        source.basic?.gptmail_api_key,
      ),
      verify_ssl: pickBoolean(
        defaults.gptmail.verify_ssl || false,
        current.gptmail?.verify_ssl,
        source.basic?.gptmail_verify_ssl,
      ),
      domain: pickString(
        defaults.gptmail.domain || '',
        current.gptmail?.domain,
        source.basic?.gptmail_domain,
      ),
    },
    cfmail: {
      ...defaults.cfmail,
      ...current.cfmail,
      base_url: pickString(
        defaults.cfmail.base_url || '',
        current.cfmail?.base_url,
        source.basic?.cfmail_base_url,
      ),
      api_key: pickString(
        defaults.cfmail.api_key || '',
        current.cfmail?.api_key,
        source.basic?.cfmail_api_key,
      ),
      verify_ssl: pickBoolean(
        defaults.cfmail.verify_ssl || false,
        current.cfmail?.verify_ssl,
        source.basic?.cfmail_verify_ssl,
      ),
      domain: pickString(
        defaults.cfmail.domain || '',
        current.cfmail?.domain,
        source.basic?.cfmail_domain,
      ),
    },
  }
}

const syncRefreshMirrors = (payload: Settings) => {
  const refreshSettings = hydrateRefreshSettings(payload)
  const browserMode = normalizeBrowserMode(
    refreshSettings.browser_mode,
    refreshSettings.browser_headless,
  )

  refreshSettings.browser_mode = browserMode
  refreshSettings.browser_headless = browserMode === 'headless'
  payload.refresh_settings = refreshSettings

  payload.basic.proxy_for_auth = refreshSettings.proxy_for_auth
  payload.basic.duckmail_base_url = refreshSettings.duckmail.base_url
  payload.basic.duckmail_api_key = refreshSettings.duckmail.api_key
  payload.basic.duckmail_verify_ssl = refreshSettings.duckmail.verify_ssl
  payload.basic.temp_mail_provider = refreshSettings.temp_mail_provider
  payload.basic.moemail_base_url = refreshSettings.moemail.base_url
  payload.basic.moemail_api_key = refreshSettings.moemail.api_key
  payload.basic.moemail_domain = refreshSettings.moemail.domain
  payload.basic.freemail_base_url = refreshSettings.freemail.base_url
  payload.basic.freemail_jwt_token = refreshSettings.freemail.jwt_token
  payload.basic.freemail_verify_ssl = refreshSettings.freemail.verify_ssl
  payload.basic.freemail_domain = refreshSettings.freemail.domain
  payload.basic.mail_proxy_enabled = refreshSettings.mail_proxy_enabled
  payload.basic.gptmail_base_url = refreshSettings.gptmail.base_url
  payload.basic.gptmail_api_key = refreshSettings.gptmail.api_key
  payload.basic.gptmail_verify_ssl = refreshSettings.gptmail.verify_ssl
  payload.basic.gptmail_domain = refreshSettings.gptmail.domain
  payload.basic.cfmail_base_url = refreshSettings.cfmail.base_url
  payload.basic.cfmail_api_key = refreshSettings.cfmail.api_key
  payload.basic.cfmail_verify_ssl = refreshSettings.cfmail.verify_ssl
  payload.basic.cfmail_domain = refreshSettings.cfmail.domain
  payload.basic.browser_mode = refreshSettings.browser_mode
  payload.basic.browser_headless = refreshSettings.browser_headless
  payload.basic.refresh_window_hours = refreshSettings.refresh_window_hours
  payload.basic.register_domain = refreshSettings.register_domain
  payload.basic.register_default_count = refreshSettings.register_default_count

  payload.retry.auto_refresh_accounts_seconds = refreshSettings.auto_refresh_accounts_seconds
  payload.retry.scheduled_refresh_enabled = refreshSettings.scheduled_refresh_enabled
  payload.retry.scheduled_refresh_interval_minutes = refreshSettings.scheduled_refresh_interval_minutes
  payload.retry.scheduled_refresh_cron = refreshSettings.scheduled_refresh_cron
  payload.retry.verification_code_resend_count = refreshSettings.verification_code_resend_count
  payload.retry.refresh_batch_size = refreshSettings.refresh_batch_size
  payload.retry.refresh_batch_interval_minutes = refreshSettings.refresh_batch_interval_minutes
  payload.retry.refresh_cooldown_hours = refreshSettings.refresh_cooldown_hours
  payload.retry.delete_expired_accounts = refreshSettings.delete_expired_accounts
  payload.retry.auto_register_enabled = refreshSettings.auto_register_enabled
  payload.retry.min_account_count = refreshSettings.min_account_count
}

watch(settings, (value) => {
  if (!value) return

  const next = JSON.parse(JSON.stringify(value)) as Settings

  next.basic = next.basic || {}
  next.basic.api_key = pickString('', next.basic.api_key)
  next.basic.base_url = pickString('', next.basic.base_url)
  next.basic.proxy_for_chat = pickString('', next.basic.proxy_for_chat)
  next.basic.image_expire_hours = pickNumber(12, next.basic.image_expire_hours)

  next.retry = next.retry || {
    max_account_switch_tries: 5,
    text_rate_limit_cooldown_seconds: 7200,
    images_rate_limit_cooldown_seconds: 14400,
    videos_rate_limit_cooldown_seconds: 14400,
    session_cache_ttl_seconds: 3600,
  }
  next.retry.max_account_switch_tries = pickNumber(5, next.retry.max_account_switch_tries)
  next.retry.rate_limit_cooldown_seconds = pickNumber(
    next.retry.text_rate_limit_cooldown_seconds,
    next.retry.rate_limit_cooldown_seconds,
  )
  next.retry.text_rate_limit_cooldown_seconds = pickNumber(
    7200,
    next.retry.text_rate_limit_cooldown_seconds,
  )
  next.retry.images_rate_limit_cooldown_seconds = pickNumber(
    14400,
    next.retry.images_rate_limit_cooldown_seconds,
  )
  next.retry.videos_rate_limit_cooldown_seconds = pickNumber(
    14400,
    next.retry.videos_rate_limit_cooldown_seconds,
  )
  next.retry.session_cache_ttl_seconds = pickNumber(
    3600,
    next.retry.session_cache_ttl_seconds,
  )

  next.image_generation = next.image_generation || {
    enabled: false,
    supported_models: [],
    output_format: 'base64',
  }
  next.image_generation.enabled = next.image_generation.enabled ?? false
  next.image_generation.supported_models = Array.isArray(next.image_generation.supported_models)
    ? next.image_generation.supported_models
    : []
  next.image_generation.output_format =
    next.image_generation.output_format === 'url' ? 'url' : 'base64'

  next.video_generation = next.video_generation || { output_format: 'html' }
  next.video_generation.output_format = next.video_generation.output_format === 'url'
    ? 'url'
    : next.video_generation.output_format === 'markdown'
      ? 'markdown'
      : 'html'

  next.quota_limits = next.quota_limits || {
    enabled: true,
    text_daily_limit: 120,
    images_daily_limit: 2,
    videos_daily_limit: 1,
  }
  next.quota_limits.enabled = next.quota_limits.enabled ?? true
  next.quota_limits.text_daily_limit = pickNumber(120, next.quota_limits.text_daily_limit)
  next.quota_limits.images_daily_limit = pickNumber(2, next.quota_limits.images_daily_limit)
  next.quota_limits.videos_daily_limit = pickNumber(1, next.quota_limits.videos_daily_limit)

  next.public_display = next.public_display || {}
  next.public_display.logo_url = pickString('', next.public_display.logo_url)
  next.public_display.chat_url = pickString('', next.public_display.chat_url)

  next.session = next.session || { expire_hours: 24 }
  next.session.expire_hours = pickNumber(24, next.session.expire_hours)

  next.refresh_settings = hydrateRefreshSettings(next)
  localSettings.value = next
}, { immediate: true })

onMounted(async () => {
  if (!settings.value) {
    await settingsStore.loadSettings()
  }
})

const handleSave = async () => {
  if (!localSettings.value) return

  errorMessage.value = ''
  isSaving.value = true

  try {
    const payload = JSON.parse(JSON.stringify(localSettings.value)) as Settings
    syncRefreshMirrors(payload)
    await settingsStore.updateSettings(payload)
    toast.success('设置保存成功')
  } catch (error: any) {
    errorMessage.value = error.message || '保存失败'
    toast.error(error.message || '保存失败')
  } finally {
    isSaving.value = false
  }
}
</script>
