import React, { createContext, useState, useEffect, useCallback } from 'react';
import type { User, TokenResponse } from '../types';
import { signin as apiSignin,
         signup as apiSignup, 
         signout as apiSignout,
         updateProfile as updateProfileApi
        } from '../api/authApi';

interface AuthContextType {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, phone: string, password: string) => Promise<void>;
  logout: () => void;
  updateProfile: (email: string, phone: string, newPassword: string, 
    currentPassword: string) => Promise<void>;
}

export const AuthContext = createContext<AuthContextType>(null!);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(localStorage.getItem('token'));
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (token) {
      // Здесь будет запрос /auth/me для верификации токена, когда будет готов
      const savedUser = localStorage.getItem('user');
      if (savedUser) setUser(JSON.parse(savedUser));
      setIsLoading(false);
    } else {
      setIsLoading(false);
    }
  }, [token]);

  const updateAuth = useCallback((data: TokenResponse) => {
    setToken(data.access_token);
    setUser(data.user);
    localStorage.setItem('token', data.access_token);
    localStorage.setItem('user', JSON.stringify(data.user));
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const data = await apiSignin(email, password);
    updateAuth(data);
  }, [updateAuth]);

  const register = useCallback(async (email: string, phone: string, password: string) => {
    const data = await apiSignup(email, phone, password);
    updateAuth(data);
  }, [updateAuth]);

  const logout = useCallback(() => {
    setToken(null);
    setUser(null);
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    apiSignout(token!);
  }, [token]);

  const updateProfile = useCallback(async (email: string, phone: string, newPassword: string, currentPassword: string) => {
  if (!token) throw new Error('No token');
  const updatedUser = await updateProfileApi(
    { email, phone, password: newPassword || undefined, currentPassword },
    token
  );
  setUser(updatedUser);
  localStorage.setItem('user', JSON.stringify(updatedUser));
}, [token]);

  return (
    <AuthContext.Provider value={{ user, token, isLoading, login, register, logout, updateProfile }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => React.useContext(AuthContext);