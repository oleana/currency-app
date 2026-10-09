// Клиент для обращения к бекенду
const BASE = import.meta.env.VITE_API_URL || ''

async function get(path) {
  const resp = await fetch(`${BASE}${path}`)
  if (!resp.ok) {
    const body = await resp.json().catch(() => ({}))
    throw new Error(body.detail || `Ошибка запроса: ${resp.status}`)
  }
  return resp.json()
}

export const fetchRates = (country) => get(`/api/rates/${country}`)
export const convert = (amount, frm, to) =>
  get(`/api/convert?amount=${encodeURIComponent(amount)}&frm=${frm}&to=${to}`)
