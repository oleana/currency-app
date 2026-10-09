import { useEffect, useState, useCallback } from 'react'
import CountryTabs from './components/CountryTabs.jsx'
import RatesList from './components/RatesList.jsx'
import Converter from './components/Converter.jsx'
import { fetchRates } from './api.js'

const COUNTRIES = [
  { id: 'ru', flag: '🇷🇺', label: 'Россия' },
  { id: 'us', flag: '🇺🇸', label: 'США' },
  { id: 'cn', flag: '🇨🇳', label: 'Китай' },
]

export default function App() {
  const [country, setCountry] = useState('ru')
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const load = useCallback(async (c) => {
    setLoading(true)
    setError(null)
    try {
      setData(await fetchRates(c))
    } catch (e) {
      setError(e.message)
      setData(null)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load(country)
  }, [country, load])

  return (
    <div className="app">
      <header className="header">
        <h1>Курсы валют</h1>
        <p className="subtitle">Реальные данные банков России, США и Китая</p>
      </header>

      <CountryTabs countries={COUNTRIES} active={country} onSelect={setCountry} />

      <main className="content">
        {loading && (
          <div className="state">
            <div className="spinner" />
            <p>Загружаем курсы…</p>
          </div>
        )}

        {error && !loading && (
          <div className="state error">
            <p>⚠️ {error}</p>
            <button className="btn" onClick={() => load(country)}>Повторить</button>
          </div>
        )}

        {data && !loading && (
          <>
            <div className="meta">
              <span className="bank">{data.bank}</span>
              <span className="date">
                {data.date} · базовая валюта {data.base}
                <button className="refresh" onClick={() => load(country)} title="Обновить">⟳</button>
              </span>
            </div>
            <RatesList rates={data.rates} base={data.base} />
            <Converter defaultFrom={data.base === 'RUB' ? 'USD' : data.base} defaultTo={data.base === 'RUB' ? 'RUB' : 'RUB'} />
            <p className="source">
              Источник: <a href={data.source} target="_blank" rel="noreferrer">{data.source}</a>
            </p>
          </>
        )}
      </main>
    </div>
  )
}
