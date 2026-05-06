/** Resposta paginada padrão da API (`page` / `per_page`, default 20 por página). */
export type Paged<T> = {
  items: T[]
  total: number
  page: number
  per_page: number
  total_pages: number
}

export const DEFAULT_PAGE_SIZE = 20

export function withPagination(path: string, page = 1, perPage = DEFAULT_PAGE_SIZE): string {
  const sep = path.includes('?') ? '&' : '?'
  return `${path}${sep}page=${page}&per_page=${perPage}`
}

export class ApiError extends Error {
  readonly status: number
  readonly detail: string | null
  /** Corpo JSON da API em erro (ex.: `blocking_execution_id` em 409). */
  readonly body: Record<string, unknown> | null

  constructor(
    status: number,
    message: string,
    detail: string | null = null,
    body: Record<string, unknown> | null = null,
  ) {
    super(message)
    this.status = status
    this.detail = detail
    this.body = body
  }
}

async function parseErrorResponse(r: Response): Promise<{
  message: string
  detail: string | null
  body: Record<string, unknown> | null
}> {
  const ct = r.headers.get('content-type') ?? ''
  if (!ct.includes('application/json')) {
    const text = await r.text()
    return { message: text || r.statusText, detail: text || null, body: null }
  }
  try {
    const j = (await r.json()) as Record<string, unknown>
    const message =
      (typeof j.message === 'string' ? j.message : null) ??
      (typeof j.detail === 'string' ? j.detail : null) ??
      r.statusText
    const detail =
      (typeof j.detail === 'string' ? j.detail : null) ??
      (typeof j.message === 'string' ? j.message : null)
    return { message, detail, body: j }
  } catch {
    return { message: r.statusText, detail: null, body: null }
  }
}

function withJsonHeaders(init: RequestInit): RequestInit {
  if (init.body === undefined) {
    return init
  }
  const headers = new Headers(init.headers as HeadersInit | undefined)
  if (!headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json')
  }
  return { ...init, headers }
}

export async function apiFetch(
  path: string,
  init: RequestInit = {},
): Promise<Response> {
  return fetch(path, {
    credentials: 'include',
    ...withJsonHeaders(init),
  })
}

export async function apiJson<T>(path: string, init: RequestInit = {}): Promise<T> {
  const r = await apiFetch(path, init)
  if (r.status === 204) {
    return undefined as T
  }
  if (!r.ok) {
    const { message, detail, body } = await parseErrorResponse(r)
    throw new ApiError(r.status, message, detail, body)
  }
  return (await r.json()) as T
}

export async function apiJsonNoBody(path: string, init: RequestInit = {}): Promise<void> {
  const r = await apiFetch(path, withJsonHeaders(init))
  if (!r.ok) {
    const { message, detail, body } = await parseErrorResponse(r)
    throw new ApiError(r.status, message, detail, body)
  }
}

/** Carrega todas as páginas (útil para selects / reorder que precisam da lista completa). */
export async function fetchAllPaged<T>(path: string, perChunk = 100): Promise<T[]> {
  const acc: T[] = []
  let page = 1
  while (true) {
    const data = await apiJson<Paged<T>>(withPagination(path, page, perChunk))
    acc.push(...data.items)
    if (page >= data.total_pages) break
    page += 1
  }
  return acc
}
