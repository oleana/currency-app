export default function CountryTabs({ countries, active, onSelect }) {
  return (
    <nav className="tabs" role="tablist">
      {countries.map((c) => (
        <button
          key={c.id}
          role="tab"
          aria-selected={active === c.id}
          className={`tab ${active === c.id ? 'active' : ''}`}
          onClick={() => onSelect(c.id)}
        >
          <span className="flag">{c.flag}</span>
          <span>{c.label}</span>
        </button>
      ))}
    </nav>
  )
}
