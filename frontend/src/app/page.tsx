export default function Home() {
  return (
    <main style={{ padding: '2rem', fontFamily: 'sans-serif', maxWidth: '800px', margin: '0 auto' }}>
      <h1>Карта Офиса 🗺️</h1>
      <p style={{ color: '#4b5563', fontSize: '1.2rem' }}>
        Панель администратора для мониторинга принтеров и уровня тонера в офисе.
      </p>

      <div style={{ marginTop: '2rem', padding: '1.5rem', backgroundColor: '#ffffff', borderRadius: '8px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
        <h2 style={{ marginTop: 0 }}>Статус сервисов</h2>
        <p>✅ Фронтенд на Next.js успешно запущен!</p>
        <p>🔗 Проверить FastAPI API Swagger документацию: <a href="/docs" target="_blank" style={{ color: '#2563eb', textDecoration: 'underline' }}>/docs</a></p>
      </div>
    </main>
  );
}
