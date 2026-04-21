import React from 'react'
import ReactDOM from 'react-dom/client'
import { HashRouter, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import './index.css'

import Layout from './components/Layout'
import Overview from './pages/Overview'
import ADLine from './pages/ADLine'
import NewHighLow from './pages/NewHighLow'
import VolumeBreadth from './pages/VolumeBreadth'
import AboveMA from './pages/AboveMA'
import Signals from './pages/Signals'
import Sectors from './pages/Sectors'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { staleTime: 5 * 60 * 1000, retry: 2 },
  },
})

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <HashRouter>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<Overview />} />
            <Route path="ad" element={<ADLine />} />
            <Route path="nh-nl" element={<NewHighLow />} />
            <Route path="volume" element={<VolumeBreadth />} />
            <Route path="above-ma" element={<AboveMA />} />
            <Route path="sectors" element={<Sectors />} />
            <Route path="signals" element={<Signals />} />
          </Route>
        </Routes>
      </HashRouter>
    </QueryClientProvider>
  </React.StrictMode>,
)
