export const ENVIRONMENT_TYPES = ['production', 'staging', 'custom'] as const

export const STEP_TYPES = [
  'ssh_command',
  'http_healthcheck',
  'notify_webhook',
] as const

export const ON_FAILURE_POLICIES = ['stop', 'continue', 'notify_and_stop'] as const

export const CONNECTION_KINDS = [
  { value: 'ssh', label: 'SSH' },
  { value: 'local_docker', label: 'Docker local' },
] as const
