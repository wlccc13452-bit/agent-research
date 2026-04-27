import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'
import { ThemeProvider } from './contexts/ThemeContext'
import ErrorBoundary from './components/ErrorBoundary'
import AsyncErrorBoundary from './components/AsyncErrorBoundary'

createRoot(document.getElementById('root')!).render(
  <ErrorBoundary>
    <AsyncErrorBoundary>
      <ThemeProvider>
        <App />
      </ThemeProvider>
    </AsyncErrorBoundary>
  </ErrorBoundary>
)
