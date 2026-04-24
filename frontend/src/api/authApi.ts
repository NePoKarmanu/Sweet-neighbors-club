import type { TokenResponse, User } from '../types';


const MOCK_MODE = true;
const mockDelay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));
const generateFakeToken = (userId: number) => `fake-jwt-for-user-${userId}`;

// Ключ для хранения в localStorage
const USERS_STORAGE_KEY = 'mock_users';

interface MockUser {
  id: number;
  email: string;
  phone: string;
  password: string;
}

const getUsers = (): Record<string, MockUser> => {
  const data = localStorage.getItem(USERS_STORAGE_KEY);
  return data ? JSON.parse(data) : {};
};

const saveUsers = (users: Record<string, MockUser>) => {
  localStorage.setItem(USERS_STORAGE_KEY, JSON.stringify(users));
};

export async function signup(email: string, phone: string, password: string): Promise<TokenResponse> {
  if (MOCK_MODE) {
    await mockDelay(500);
    const users = getUsers();
    if (Object.values(users).some(u => u.email === email)) {
      throw { response: { data: { detail: 'User with this email already exists' } } };
    }
    if (Object.values(users).some(u => u.phone === phone)) {
      throw { response: { data: { detail: 'User with this phone already exists' } } };
    }
    const maxId = Object.values(users).reduce((max, u) => Math.max(max, u.id), 0);
    const newUser: MockUser = { id: maxId + 1, email, phone, password };
    users[email] = newUser;
    saveUsers(users);
    const response: TokenResponse = {
      access_token: generateFakeToken(newUser.id),
      token_type: 'bearer',
      user: {
        id: newUser.id,
        email: newUser.email,
        phone: newUser.phone,
        is_staff: false,
      }
    };
    return response;
  }
  throw new Error('Not implemented');
}

export async function signin(email: string, password: string): Promise<TokenResponse> {
  if (MOCK_MODE) {
    await mockDelay(500);
    const users = getUsers();
    const user = users[email];
    if (!user || user.password !== password) {
      throw { response: { data: { detail: 'Invalid email or password' } } };
    }
    const response: TokenResponse = {
      access_token: generateFakeToken(user.id),
      token_type: 'bearer',
      user: {
        id: user.id,
        email: user.email,
        phone: user.phone,
        is_staff: false,
      }
    };
    return response;
  }
  throw new Error('Not implemented');
}

export async function signout(_token: string): Promise<void> {
  // в моке ничего не делаем
}

export interface UpdateProfilePayload {
  email?: string;
  phone?: string;
  password?: string;
  currentPassword: string;
}

export async function updateProfile(payload: UpdateProfilePayload, token: string): Promise<User> {
  if (MOCK_MODE) {
    await mockDelay(500);
    const users = getUsers();
    const userIdMatch = token.match(/fake-jwt-for-user-(\d+)/);
    if (!userIdMatch) throw { response: { data: { detail: 'Invalid token' } } };
    const userId = parseInt(userIdMatch[1], 10);

    const userEntry = Object.entries(users).find(([email, u]) => u.id === userId);
    if (!userEntry) throw { response: { data: { detail: 'User not found' } } };
    const [oldEmail, user] = userEntry;

    if (user.password !== payload.currentPassword) {
      throw { response: { data: { detail: 'Неверный текущий пароль' } } };
    }

    if (payload.email && payload.email !== oldEmail) {
      if (users[payload.email] && users[payload.email].id !== userId) {
        throw { response: { data: { detail: 'Email уже используется' } } };
      }
      delete users[oldEmail];
      user.email = payload.email;
      users[payload.email] = user;
    }
    if (payload.phone !== undefined) {
      if (Object.values(users).some(u => u.phone === payload.phone && u.id !== userId)) {
        throw { response: { data: { detail: 'Телефон уже используется' } } };
      }
      user.phone = payload.phone!;
    }
    if (payload.password) {
      user.password = payload.password;
    }

    saveUsers(users);

    return {
      id: user.id,
      email: user.email,
      phone: user.phone,
      is_staff: false,
    };
  }
  throw new Error('Not implemented');
}