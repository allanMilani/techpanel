<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'

import AppCheckbox from '../components/inputs/AppCheckbox.vue'
import AppSelect from '../components/inputs/AppSelect.vue'
import AppTextarea from '../components/inputs/AppTextarea.vue'
import AppTextField from '../components/inputs/AppTextField.vue'
import { CONNECTION_KINDS } from '../constants/formOptions'
import { ApiError, apiJson, fetchAllPaged } from '../composables/useApi'
import { useToast } from '../composables/useToast'

interface Server {
  id: string
  name: string
  host: string
  port: number
  ssh_user: string
  connection_kind: string
  docker_container_name: string | null
  ssh_strict_host_key_checking?: boolean
  project_directory?: string | null
}

const route = useRoute()
const router = useRouter()
const isEdit = computed(() => route.name === 'servers-edit')

const name = ref('')
const host = ref('')
const port = ref('22')
const sshUser = ref('')
const privateKey = ref('')
const connectionKind = ref('ssh')
const dockerName = ref('')
const projectDirectory = ref('')
const sshStrictHostKeyChecking = ref(false)
const { showToast } = useToast()

const kindOptions = CONNECTION_KINDS.map((k) => ({ value: k.value, label: k.label }))

const isDocker = computed(() => connectionKind.value === 'local_docker')
const isSsh = computed(() => connectionKind.value === 'ssh')

function buildPayload(): Record<string, unknown> {
  if (isDocker.value) {
    return {
      name: name.value,
      host: 'localhost',
      port: 22,
      ssh_user: '',
      private_key_plain: '',
      connection_kind: 'local_docker',
      docker_container_name: dockerName.value.trim() || null,
      ssh_strict_host_key_checking: false,
      project_directory: projectDirectory.value.trim() || null,
    }
  }
  return {
    name: name.value,
    host: host.value,
    port: Number.parseInt(String(port.value), 10),
    ssh_user: sshUser.value,
    private_key_plain: privateKey.value.trim(),
    connection_kind: 'ssh',
    docker_container_name: null,
    ssh_strict_host_key_checking: sshStrictHostKeyChecking.value,
    project_directory: projectDirectory.value.trim() || null,
  }
}

onMounted(async () => {
  if (!isEdit.value) return
  const list = await fetchAllPaged<Server>('/api/servers/')
  const id = route.params.id as string
  const s = list.find((x) => x.id === id)
  if (!s) {
    showToast('Servidor não encontrado.', 'error')
    return
  }
  name.value = s.name
  host.value = s.host
  port.value = String(s.port)
  sshUser.value = s.ssh_user
  connectionKind.value = s.connection_kind
  dockerName.value = s.docker_container_name ?? ''
  projectDirectory.value = s.project_directory?.trim() ?? ''
  sshStrictHostKeyChecking.value = Boolean(s.ssh_strict_host_key_checking)
})

async function save() {
  const body = buildPayload()
  try {
    if (isEdit.value) {
      const id = route.params.id as string
      const putBody =
        isSsh.value
          ? { ...body, private_key_plain: privateKey.value.trim() || null }
          : { ...body }
      await apiJson(`/api/servers/${id}`, {
        method: 'PUT',
        body: JSON.stringify(putBody),
      })
    } else {
      await apiJson('/api/servers/', {
        method: 'POST',
        body: JSON.stringify(body),
      })
    }
    showToast(isEdit.value ? 'Servidor atualizado.' : 'Servidor criado.', 'success')
    await router.push('/servers')
  } catch (e) {
    const msg = e instanceof ApiError ? e.detail ?? e.message : 'Erro ao salvar o servidor.'
    showToast(msg, 'error')
  }
}
</script>

<template>
  <div>
    <RouterLink to="/servers" class="mb-4 inline-flex items-center gap-1 text-sm text-sky-600 hover:underline">
      <font-awesome-icon :icon="['fas', 'arrow-left']" />
      Voltar
    </RouterLink>
    <h1 class="mb-6 text-2xl font-semibold text-slate-800">
      {{ isEdit ? 'Editar servidor' : 'Novo servidor' }}
    </h1>
    <form class="w-full rounded-lg border border-slate-200 bg-white p-6 shadow-sm" @submit.prevent="save">
      <AppTextField id="name" v-model="name" label="Nome" required />
      <AppSelect
        id="connection_kind"
        v-model="connectionKind"
        label="Tipo de conexão"
        :options="kindOptions"
        hint="SSH acessa host remoto; Docker local usa apenas o container nesta máquina"
        doc-href="/ajuda#tipo-conexao"
        doc-aria-label="Documentação sobre tipo de conexão SSH ou Docker"
      />

      <AppTextField
        id="project_directory"
        v-model="projectDirectory"
        label="Diretório do projeto no servidor (opcional)"
        hint="Caminho absoluto do clone Git no servidor ou no container. Usado para sincronização Git opcional na pipeline e para o ficheiro .env remoto; se vazio, usa o diretório de trabalho do ambiente."
        doc-href="/ajuda"
        doc-aria-label="Ajuda sobre diretório do projeto"
      />

      <template v-if="isDocker">
        <AppTextField
          id="docker"
          v-model="dockerName"
          label="Nome ou ID do container"
          hint="como em docker ps"
          required
          doc-href="/ajuda#docker-container"
          doc-aria-label="Documentação sobre container Docker"
        />
      </template>

      <template v-if="isSsh">
        <AppTextField
          id="host"
          v-model="host"
          label="Host"
          required
          doc-href="/ajuda#ssh-servidor"
          doc-aria-label="Documentação sobre host, porta e SSH"
        />
        <AppTextField
          id="port"
          v-model="port"
          label="Porta"
          type="number"
          required
          doc-href="/ajuda#ssh-servidor"
          doc-aria-label="Documentação sobre host, porta e SSH"
        />
        <AppTextField
          id="ssh_user"
          v-model="sshUser"
          label="Usuário SSH"
          required
          doc-href="/ajuda#ssh-servidor"
          doc-aria-label="Documentação sobre host, porta e SSH"
        />
        <AppCheckbox
          id="ssh_strict_host"
          v-model="sshStrictHostKeyChecking"
          label="Verificação estrita da chave do host SSH (known_hosts no servidor do TechPanel)"
        />
        <p class="-mt-2 mb-4 text-xs text-slate-500">
          Desligado: aceita o host na primeira ligação (útil com chaves OpenSSH / novo servidor). Ligado: só conecta se
          o host já estiver conhecido nesta máquina —
          <RouterLink to="/ajuda#ssh-host-key-policy" class="text-sky-600 underline hover:text-sky-800">ajuda</RouterLink
          >.
        </p>
        <AppTextarea
          id="pk"
          v-model="privateKey"
          :rows="10"
          :label="isEdit ? 'Chave privada (deixe em branco para manter)' : 'Chave privada (PEM / OpenSSH)'"
          hint="Use várias linhas como no ficheiro (não use campo tipo password — apaga quebras de linha). Opcional: colar com Ctrl+Shift+V para texto sem formatação."
          :required="!isEdit"
          doc-href="/ajuda#ssh-chave-privada"
          doc-aria-label="Documentação sobre chave privada SSH"
        />
      </template>

      <button
        type="submit"
        class="mt-2 rounded-md bg-sky-600 px-4 py-2 text-sm font-medium text-white hover:bg-sky-700"
      >
        Salvar
      </button>
    </form>
  </div>
</template>
