import { createContext, useContext, useState } from 'react';
import api from '../api/axios';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(localStorage.getItem('access_token'));
  const [user, setUser] = useState(null);

  const login = async (email, password) => {
    const response = await api.post('/auth/login', { email, password });
    const accessToken = response.data.access_token;
    localStorage.setItem('access_token', accessToken);
    setToken(accessToken);
    return accessToken;
  };

  const register = async (name, email, password, target_role) => {
    await api.post('/auth/register', { name, email, password, target_role });
  };

  const logout = () => {
    localStorage.removeItem('access_token');
    setToken(null);
    setUser(null);
  };

  const fetchCurrentUser = async () => {
    const response = await api.get('/users/me');
    setUser(response.data);
    return response.data;
  };


  const value = {
    token,
    user,
    isAuthenticated: !!token,
    login,
    register,
    logout,
    fetchCurrentUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}