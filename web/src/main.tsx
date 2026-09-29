import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import '@fontsource/anton/400.css' // slogan face (mobile banner)
import '@fontsource/montserrat/600.css' // wordmark: PROJECT
import '@fontsource/montserrat/900.css' // wordmark: DURGA
import './index.css'
import App from './App.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
