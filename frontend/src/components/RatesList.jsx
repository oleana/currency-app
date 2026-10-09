const FLAGS = {
  USD: '🇺🇸', EUR: '🇪🇺', CNY: '🇨🇳', RUB: '🇷🇺', GBP: '🇬🇧', JPY: '🇯🇵',
  CHF: '🇨🇭', KZT: '🇰🇿', TRY: '🇹🇷', INR: '🇮🇳', HKD: '🇭🇰', AED: '🇦🇪',
}

function Delta({ rate, previous }) {
  if (previous == null) return null
  const diff = rate - previous
  if (Math.abs(diff) < 0.0001) return <span className="delta flat">＝</span>
  const up = diff > 0
  return (
    <span className={`delta ${up ? 'up' : 'down'}`}>
      {up ? '▲' : '▼'} {Math.abs(diff).toFixed(4)}
    </span>
  )
}

export default function RatesList({ rates, base }) {
  return (
    <ul className="rates">
      {rates.map((r) => (
        <li key={r.code} className="rate-card">
          <div className="rate-left">
            <span className="rate-flag">{FLAGS[r.code] || '💱'}</span>
            <div>
              <div className="rate-code">{r.code}</div>
              <div className="rate-name">{r.name}</div>
            </div>
          </div>
          <div className="rate-right">
            <div className="rate-value">
              {r.rate.toLocaleString('ru-RU', { maximumFractionDigits: 4 })}
              <span className="rate-base"> {base}</span>
            </div>
            <Delta rate={r.rate} previous={r.previous} />
          </div>
        </li>
      ))}
    </ul>
  )
}
