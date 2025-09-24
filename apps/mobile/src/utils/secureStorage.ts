import AsyncStorage from "@react-native-async-storage/async-storage";
import * as SecureStore from "expo-secure-store";

// Storage keys
export const STORAGE_KEYS = {
  AUTH_TOKEN: "uf_auth_token",
  REFRESH_TOKEN: "uf_refresh_token",
  USER_EMAIL: "uf_user_email",
  USER_ID: "uf_user_id",
  BIOMETRIC_ENABLED: "uf_biometric_enabled",
  THEME_PREFERENCE: "uf_theme",
  NOTIFICATION_SETTINGS: "uf_notifications",
} as const;

// Secure storage wrapper with fallback to AsyncStorage
class SecureStorageManager {
  private async isSecureStoreAvailable(): Promise<boolean> {
    try {
      return SecureStore.isAvailableAsync();
    } catch {
      return false;
    }
  }

  async setItem(key: string, value: string): Promise<void> {
    const isSecureAvailable = await this.isSecureStoreAvailable();

    if (isSecureAvailable && this.isSensitiveKey(key)) {
      await SecureStore.setItemAsync(key, value);
    } else {
      await AsyncStorage.setItem(key, value);
    }
  }

  async getItem(key: string): Promise<string | null> {
    const isSecureAvailable = await this.isSecureStoreAvailable();

    if (isSecureAvailable && this.isSensitiveKey(key)) {
      return await SecureStore.getItemAsync(key);
    } else {
      return await AsyncStorage.getItem(key);
    }
  }

  async removeItem(key: string): Promise<void> {
    const isSecureAvailable = await this.isSecureStoreAvailable();

    if (isSecureAvailable && this.isSensitiveKey(key)) {
      await SecureStore.deleteItemAsync(key);
    } else {
      await AsyncStorage.removeItem(key);
    }
  }

  async clear(): Promise<void> {
    // Clear AsyncStorage
    await AsyncStorage.clear();

    // Clear sensitive items from SecureStore
    const isSecureAvailable = await this.isSecureStoreAvailable();
    if (isSecureAvailable) {
      const sensitiveKeys = [
        STORAGE_KEYS.AUTH_TOKEN,
        STORAGE_KEYS.REFRESH_TOKEN,
      ];

      await Promise.all(
        sensitiveKeys.map((key) =>
          SecureStore.deleteItemAsync(key).catch(() => {}),
        ),
      );
    }
  }

  private isSensitiveKey(key: string): boolean {
    const sensitiveKeys = [STORAGE_KEYS.AUTH_TOKEN, STORAGE_KEYS.REFRESH_TOKEN];
    return sensitiveKeys.includes(key);
  }

  // Token management helpers
  async setTokens(authToken: string, refreshToken?: string): Promise<void> {
    await this.setItem(STORAGE_KEYS.AUTH_TOKEN, authToken);
    if (refreshToken) {
      await this.setItem(STORAGE_KEYS.REFRESH_TOKEN, refreshToken);
    }
  }

  async getAuthToken(): Promise<string | null> {
    return await this.getItem(STORAGE_KEYS.AUTH_TOKEN);
  }

  async getRefreshToken(): Promise<string | null> {
    return await this.getItem(STORAGE_KEYS.REFRESH_TOKEN);
  }

  async clearTokens(): Promise<void> {
    await Promise.all([
      this.removeItem(STORAGE_KEYS.AUTH_TOKEN),
      this.removeItem(STORAGE_KEYS.REFRESH_TOKEN),
    ]);
  }

  // User data management
  async setUserData(userId: string, email: string): Promise<void> {
    await Promise.all([
      this.setItem(STORAGE_KEYS.USER_ID, userId),
      this.setItem(STORAGE_KEYS.USER_EMAIL, email),
    ]);
  }

  async getUserData(): Promise<{
    userId: string | null;
    email: string | null;
  }> {
    const [userId, email] = await Promise.all([
      this.getItem(STORAGE_KEYS.USER_ID),
      this.getItem(STORAGE_KEYS.USER_EMAIL),
    ]);
    return { userId, email };
  }

  async clearUserData(): Promise<void> {
    await Promise.all([
      this.removeItem(STORAGE_KEYS.USER_ID),
      this.removeItem(STORAGE_KEYS.USER_EMAIL),
    ]);
  }

  // Settings management
  async setBiometricEnabled(enabled: boolean): Promise<void> {
    await this.setItem(STORAGE_KEYS.BIOMETRIC_ENABLED, enabled.toString());
  }

  async isBiometricEnabled(): Promise<boolean> {
    const value = await this.getItem(STORAGE_KEYS.BIOMETRIC_ENABLED);
    return value === "true";
  }

  async setThemePreference(theme: "light" | "dark" | "system"): Promise<void> {
    await this.setItem(STORAGE_KEYS.THEME_PREFERENCE, theme);
  }

  async getThemePreference(): Promise<"light" | "dark" | "system"> {
    const value = await this.getItem(STORAGE_KEYS.THEME_PREFERENCE);
    return (value as "light" | "dark" | "system") || "system";
  }

  async setNotificationSettings(settings: object): Promise<void> {
    await this.setItem(
      STORAGE_KEYS.NOTIFICATION_SETTINGS,
      JSON.stringify(settings),
    );
  }

  async getNotificationSettings(): Promise<object | null> {
    const value = await this.getItem(STORAGE_KEYS.NOTIFICATION_SETTINGS);
    return value ? JSON.parse(value) : null;
  }

  // Session validation
  async isAuthenticated(): Promise<boolean> {
    const token = await this.getAuthToken();
    return !!token;
  }
}

export const secureStorage = new SecureStorageManager();
