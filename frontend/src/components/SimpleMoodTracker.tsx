export function SimpleMoodTracker() {
  return (
    <div style={{ 
      height: '100%', 
      background: '#F5F7FA', 
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '20px'
    }}>
      <div style={{
        background: 'white',
        borderRadius: '16px',
        padding: '40px',
        textAlign: 'center',
        boxShadow: '0 4px 20px rgba(0,0,0,0.1)',
        maxWidth: '400px',
        width: '100%'
      }}>
        <div style={{ fontSize: '48px', marginBottom: '20px' }}>💪</div>
        <h2 style={{ 
          fontSize: '24px', 
          fontWeight: '700',
          color: '#262626',
          margin: '0 0 16px 0',
          lineHeight: '1.2'
        }}>
          Fuck Your Mood,<br />Get to Work
        </h2>
        <p style={{ 
          fontSize: '16px', 
          color: '#8C8C8C',
          margin: 0,
          lineHeight: '1.5'
        }}>
          Your feelings don't determine your actions.<br />
          Action creates momentum.
        </p>
      </div>
    </div>
  );
}