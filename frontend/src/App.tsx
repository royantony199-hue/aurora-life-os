import { AuthProvider } from './contexts/AuthContext';
import { UltimateMobileApp } from './components/UltimateMobileApp';

export default function App() {
  return (
    <AuthProvider>
      <UltimateMobileApp />
    </AuthProvider>
  );
}
