import authClient from './authClient';
import type { TokenResponse, User } from '../types';

export async function signup(email: string, phone: string, password: string): Promise<TokenResponse> {
  const { data } = await authClient.post<TokenResponse>('/auth/signup', {
    email,
    phone,
    password,
  });
  return data;
}

export async function signin(email: string, password: string): Promise<TokenResponse> {
  const { data } = await authClient.post<TokenResponse>('/auth/signin', {
    email,
    password,
  });
  return data;
}

export async function signout(token: string): Promise<void> {
  await authClient.post(
    '/auth/exit',
    {},
    {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    },
  );
}

export interface UpdateProfilePayload {
  email?: string;
  phone?: string;
  password?: string;
  currentPassword: string;
}

export async function updateProfile(payload: UpdateProfilePayload, token: string): Promise<User> {
  const { data } = await authClient.put<User>(
    '/auth/profile',
    {
      email: payload.email,
      phone: payload.phone,
      password: payload.password,
      current_password: payload.currentPassword,
    },
    {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    },
  );
  return data;
}
