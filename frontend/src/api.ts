export type User = { id: number; login: string; email: string | null; clearance_level: number; is_music_account: boolean }
export type Session = { user: User; csrf_token: string }
export const levels: Record<number, string> = { 1: 'Public', 2: 'Confidential', 3: 'Secret' }

export class ApiError extends Error {
  status: number
  constructor(status: number, message: string) { super(message); this.status = status }
}

export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(`/api${path}`, {
    ...init, credentials: 'same-origin',
    headers: { 'Content-Type': 'application/json', 'X-MusicAccess': '1', ...init.headers },
  })
  if (!response.ok) {
    const data = await response.json().catch(() => ({}))
    const detail = data.detail
    const message = typeof detail === 'string' ? detail : Array.isArray(detail)
      ? detail.map((e: { loc: string[]; msg: string }) => `${e.loc.at(-1)}: ${e.msg}`).join('; ')
      : 'Сервис временно недоступен'
    throw new ApiError(response.status, message)
  }
  return response.status === 204 ? undefined as T : response.json()
}

export function errorMessage(error: unknown): string {
  return error instanceof ApiError ? error.message : 'Не удалось связаться с сервером. Попробуйте ещё раз.'
}
