import { useState } from 'react'
import { convert } from '../api.js'

const CODES = ['USD', 'EUR', 'CNY', 'RUB', 'GBP', 'JPY', 'CHF', 'KZT', 'TRY', 'INR', 'HKD', 'AED']

export default function Converter({ defaultFrom = 'USD', defaultTo = 'RUB' }) {
  const [amount, setAmount] = useState('100')
  const [frm, setFrm] = useState(defaultFrom)
  const [to, setTo] = useState(defaultTo)
  const [result, setResult] = useState(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)

  const run = async () => {
    const num = parseFloat(amount)
    if (!num || num <= 0) return
    setBusy(true)
    setError(null)
    try {
      setResult(await convert(num, frm, to))
    } catch (e) {
      setError(e.message)
      setResult(null)
    } finally {
      setBusy(false)
    }
  }

  const swap = () => {
    setFrm(to)
    setTo(frm)
    setResult(null)
  }

  return (
    <section className="converter">
      <h2>Конвертер</h2>
      <div className="conv-row">
        <input
          type="number"
          inputMode="decimal"
          min="0"
          value={amount}
          onChange={(e) => setAmount(e.target.value)}
          aria-label="Сумма"
        />
        <select value={frm} onChange={(e) => { setFrm(e.target.value); setResult(null) }} aria-label="Из валюты">
          {CODES.map((c) => <option key={c}>{c}</option>)}
        </select>
        <button className="swap" onClick={swap} title="Поменять местами">⇄</button>
        <select value={to} onChange={(e) => { setTo(e.target.value); setResult(null) }} aria-label="В валюту">
          {CODES.map((c) => <option key={c}>{c}</option>)}
        </select>
      </div>
      <button className="btn wide" onClick={run} disabled={busy}>
        {busy ? 'Считаем…' : 'Конвертировать'}
      </button>
      {error && <p className="conv-error">⚠️ {error}</p>}
      {result && (
        <p className="conv-result">
          {result.amount.toLocaleString('ru-RU')} {result.from} ={' '}
          <strong>{result.result.toLocaleString('ru-RU', { maximumFractionDigits: 2 })} {result.to}</strong>
          <span className="conv-rate"> (курс {result.rate.toLocaleString('ru-RU', { maximumFractionDigits: 4 })})</span>
        </p>
      )}
    </section>
  )
}
