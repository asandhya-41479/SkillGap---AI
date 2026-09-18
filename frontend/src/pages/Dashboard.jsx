import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

function Dashboard() {
  const { user, fetchCurrentUser, logout } = useAuth();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetchCurrentUser()
      .catch(() => {
        setError('Session expired. Please log in again.');
        logout();
        navigate('/login');
      })
      .finally(() => setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p>Loading...</p>
      </div>
    );

  }

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <div className="max-w-md mx-auto bg-white rounded-lg shadow-md p-6">
        {error && <p className="text-red-600 mb-4">{error}</p>}
        {user && (
          <>
            <h1 className="text-2xl font-bold mb-2">Welcome, {user.name}</h1>
            <p className="text-gray-600 mb-1">Email: {user.email}</p>
            <p className="text-gray-600 mb-4">
              Target Role: {user.target_role || 'Not set'}
            </p>
          </>
        )}
        <div className="flex gap-3">
          <button
            onClick={() => navigate('/jobs')}
            className="bg-purple-600 text-white px-4 py-2 rounded hover:bg-purple-700"
          >
            Job Market Intelligence
          </button>
          <button
            onClick={handleLogout}
            className="bg-red-600 text-white px-4 py-2 rounded hover:bg-red-700"
          >
            Logout
          </button>
        </div>
      </div>
    </div>
  );

}

export default Dashboard;