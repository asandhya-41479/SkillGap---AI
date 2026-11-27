import { createContext, useContext, useState } from 'react';
import api from '../api/axios';
import { getToken, saveToken, clearToken } from '../api/token';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [token, setToken] = useState(getToken());
  const [user, setUser] = useState(null);

  const login = async (email, password, remember = true) => {
    const response = await api.post('/auth/login', { email, password });
    const accessToken = response.data.access_token;
    saveToken(accessToken, remember);
    setToken(accessToken);
    return accessToken;
  };

  const register = async (name, email, password, target_role) => {
    await api.post('/auth/register', { name, email, password, target_role });
  };

  const logout = () => {
    clearToken();
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