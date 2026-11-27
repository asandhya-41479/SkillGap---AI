import { Routes, Route, Navigate } from 'react-router-dom';
import Register from './pages/Register';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import SkillProfile from './pages/SkillProfile';
import JobIntelligence from './pages/JobIntelligence';
import ProtectedRoute from './components/ProtectedRoute';
import AppLayout from './components/layout/AppLayout';
import SkillGapAnalysis from './pages/SkillGapAnalysis';
import Roadmap from './pages/Roadmap';
import CareerReadiness from './pages/CareerReadiness';
import CareerIntelligence from './pages/CareerIntelligence';
import Settings from './pages/Settings';
import ForgotPassword from './pages/ForgotPassword';
import ResetPassword from './pages/ResetPassword';

function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/login" replace />} />
      <Route path="/register" element={<Register />} />
      <Route path="/login" element={<Login />} />
      <Route path="/forgot-password" element={<ForgotPassword />} />
      <Route path="/reset-password" element={<ResetPassword />} />

      {/* Every logged-in page shares the sidebar layout. */}
      <Route
        element={
          <ProtectedRoute>
            <AppLayout />
          </ProtectedRoute>
        }
      >
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/skills" element={<SkillProfile />} />
        <Route path="/jobs" element={<JobIntelligence />} />
        <Route path="/skill-gap" element={<SkillGapAnalysis />} />
        <Route path="/roadmap" element={<Roadmap />} />
        <Route path="/readiness" element={<CareerReadiness />} />
        <Route path="/career" element={<CareerIntelligence />} />
        <Route path="/settings" element={<Settings />} />
      </Route>

      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  );
}

export default App;
