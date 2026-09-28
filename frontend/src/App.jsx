import { Routes, Route, Navigate } from 'react-router-dom';
import Register from './pages/Register';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import SkillProfile from './pages/SkillProfile';
import JobIntelligence from './pages/JobIntelligence';
import ProtectedRoute from './components/ProtectedRoute';
import SkillGapAnalysis from './pages/SkillGapAnalysis';

function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/login" replace />} />
      <Route path="/register" element={<Register />} />
      <Route path="/login" element={<Login />} />
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <Dashboard />
          </ProtectedRoute>
        }
      />

      <Route
        path="/skills"
        element={
          <ProtectedRoute>
            <SkillProfile />
          </ProtectedRoute>
        }
      />

      <Route
        path="/jobs"
        element={
          <ProtectedRoute>
            <JobIntelligence />
          </ProtectedRoute>
        }
      />
      <Route
        path="/skill-gap"
        element={
          <ProtectedRoute>
            <SkillGapAnalysis />
          </ProtectedRoute>
        }
      />
    </Routes>
  );
}

export default App;