import { useState } from 'react'
import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import HomePage from './pages/HomePage'
import PredictionsPage from './pages/PredictionsPage'
import TeamAnalysisPage from './pages/TeamAnalysisPage'
import TablePage from './pages/TablePage'
import QualityPage from './pages/QualityPage'
import UpdatePage from './pages/UpdatePage'
import AboutPage from './pages/AboutPage'
import ApiDebugPage from './pages/ApiDebugPage'

function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<HomePage />} />
        <Route path="predictions" element={<PredictionsPage />} />
        <Route path="team-analysis" element={<TeamAnalysisPage />} />
        <Route path="table" element={<TablePage />} />
        <Route path="quality" element={<QualityPage />} />
        <Route path="update" element={<UpdatePage />} />
        <Route path="about" element={<AboutPage />} />
        <Route path="api-debug" element={<ApiDebugPage />} />
      </Route>
    </Routes>
  )
}

export default App
