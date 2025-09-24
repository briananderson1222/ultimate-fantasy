import { Platform } from 'react-native';
import PushNotification, { Importance } from 'react-native-push-notification';
import PushNotificationIOS from '@react-native-community/push-notification-ios';
import messaging from '@react-native-firebase/messaging';
import AsyncStorage from '@react-native-async-storage/async-storage';

export interface NotificationPayload {
  id: string;
  title: string;
  body: string;
  data?: Record<string, any>;
  category: 'league' | 'trade' | 'lineup' | 'scoring' | 'social' | 'general';
  priority: 'high' | 'normal' | 'low';
  soundName?: string;
  largeIcon?: string;
  bigText?: string;
  actions?: NotificationAction[];
}

export interface NotificationAction {
  id: string;
  title: string;
  options?: {
    foreground?: boolean;
    destructive?: boolean;
    authenticationRequired?: boolean;
  };
}

export interface NotificationSettings {
  enabled: boolean;
  categories: {
    league: boolean;
    trade: boolean;
    lineup: boolean;
    scoring: boolean;
    social: boolean;
    general: boolean;
  };
  quietHours: {
    enabled: boolean;
    start: string; // HH:MM format
    end: string;   // HH:MM format
  };
  soundEnabled: boolean;
  vibrationEnabled: boolean;
}

export interface NotificationHistory {
  id: string;
  payload: NotificationPayload;
  receivedAt: number;
  readAt?: number;
  actionTaken?: string;
}

export class PushNotificationService {
  private static instance: PushNotificationService;
  private initialized = false;
  private deviceToken: string | null = null;
  private settings: NotificationSettings;
  private history: NotificationHistory[] = [];

  private constructor() {
    this.settings = {
      enabled: true,
      categories: {
        league: true,
        trade: true,
        lineup: true,
        scoring: true,
        social: true,
        general: true
      },
      quietHours: {
        enabled: false,
        start: '22:00',
        end: '08:00'
      },
      soundEnabled: true,
      vibrationEnabled: true
    };
  }

  public static getInstance(): PushNotificationService {
    if (!PushNotificationService.instance) {
      PushNotificationService.instance = new PushNotificationService();
    }
    return PushNotificationService.instance;
  }

  public async initialize(): Promise<void> {
    if (this.initialized) return;

    try {
      await this.loadSettings();
      await this.loadHistory();
      await this.setupFirebase();
      await this.configurePushNotifications();
      await this.requestPermissions();
      this.initialized = true;
    } catch (error) {
      console.error('Failed to initialize push notifications:', error);
    }
  }

  private async setupFirebase(): Promise<void> {
    if (Platform.OS === 'ios') {
      await messaging().requestPermission();
    }

    messaging().onMessage(async remoteMessage => {
      this.handleForegroundMessage(remoteMessage);
    });

    messaging().onNotificationOpenedApp(remoteMessage => {
      this.handleNotificationOpen(remoteMessage);
    });

    messaging().getInitialNotification().then(remoteMessage => {
      if (remoteMessage) {
        this.handleNotificationOpen(remoteMessage);
      }
    });

    messaging().onTokenRefresh(token => {
      this.deviceToken = token;
      this.sendTokenToServer(token);
    });

    const token = await messaging().getToken();
    this.deviceToken = token;
    this.sendTokenToServer(token);
  }

  private async configurePushNotifications(): Promise<void> {
    PushNotification.configure({
      onRegister: (token) => {
        console.log('TOKEN:', token);
        if (Platform.OS === 'ios') {
          this.deviceToken = token.token;
          this.sendTokenToServer(token.token);
        }
      },

      onNotification: (notification) => {
        this.handleLocalNotification(notification);
        if (Platform.OS === 'ios') {
          notification.finish(PushNotificationIOS.FetchResult.NoData);
        }
      },

      onAction: (notification) => {
        this.handleNotificationAction(notification);
      },

      onRegistrationError: (err) => {
        console.error('Registration error:', err);
      },

      permissions: {
        alert: true,
        badge: true,
        sound: true,
      },

      popInitialNotification: true,
      requestPermissions: Platform.OS === 'ios',
    });

    this.createNotificationChannels();
  }

  private createNotificationChannels(): void {
    if (Platform.OS === 'android') {
      PushNotification.createChannel(
        {
          channelId: 'fantasy-league',
          channelName: 'League Updates',
          channelDescription: 'Notifications about league activities',
          importance: Importance.HIGH,
          soundName: 'default',
          vibrate: true,
        },
        () => {}
      );

      PushNotification.createChannel(
        {
          channelId: 'fantasy-trade',
          channelName: 'Trade Notifications',
          channelDescription: 'Trade proposals and updates',
          importance: Importance.HIGH,
          soundName: 'default',
          vibrate: true,
        },
        () => {}
      );

      PushNotification.createChannel(
        {
          channelId: 'fantasy-lineup',
          channelName: 'Lineup Reminders',
          channelDescription: 'Lineup deadline reminders',
          importance: Importance.DEFAULT,
          soundName: 'default',
          vibrate: true,
        },
        () => {}
      );

      PushNotification.createChannel(
        {
          channelId: 'fantasy-scoring',
          channelName: 'Scoring Updates',
          channelDescription: 'Live scoring and game updates',
          importance: Importance.DEFAULT,
          soundName: 'default',
          vibrate: false,
        },
        () => {}
      );

      PushNotification.createChannel(
        {
          channelId: 'fantasy-social',
          channelName: 'Social Features',
          channelDescription: 'Messages and social interactions',
          importance: Importance.DEFAULT,
          soundName: 'default',
          vibrate: true,
        },
        () => {}
      );
    }
  }

  private async requestPermissions(): Promise<boolean> {
    try {
      if (Platform.OS === 'ios') {
        const authStatus = await messaging().requestPermission();
        const enabled =
          authStatus === messaging.AuthorizationStatus.AUTHORIZED ||
          authStatus === messaging.AuthorizationStatus.PROVISIONAL;
        return enabled;
      } else {
        return true; // Android permissions are handled during channel creation
      }
    } catch (error) {
      console.error('Permission request failed:', error);
      return false;
    }
  }

  public async scheduleLocalNotification(payload: NotificationPayload, scheduleTime?: Date): Promise<void> {
    if (!this.shouldShowNotification(payload)) return;

    const notificationConfig = {
      id: payload.id,
      title: payload.title,
      message: payload.body,
      date: scheduleTime || new Date(Date.now() + 1000),
      channelId: `fantasy-${payload.category}`,
      soundName: this.settings.soundEnabled ? (payload.soundName || 'default') : undefined,
      playSound: this.settings.soundEnabled,
      vibrate: this.settings.vibrationEnabled,
      actions: payload.actions?.map(action => action.id) || [],
      userInfo: payload.data || {},
      category: payload.category,
      ...(Platform.OS === 'android' && {
        largeIcon: payload.largeIcon || 'ic_launcher',
        bigText: payload.bigText || payload.body,
        importance: payload.priority === 'high' ? 'high' : 'default',
      }),
    };

    PushNotification.localNotificationSchedule(notificationConfig);
    this.addToHistory(payload);
  }

  public async showImmediateNotification(payload: NotificationPayload): Promise<void> {
    if (!this.shouldShowNotification(payload)) return;

    const notificationConfig = {
      id: payload.id,
      title: payload.title,
      message: payload.body,
      channelId: `fantasy-${payload.category}`,
      soundName: this.settings.soundEnabled ? (payload.soundName || 'default') : undefined,
      playSound: this.settings.soundEnabled,
      vibrate: this.settings.vibrationEnabled,
      actions: payload.actions?.map(action => action.id) || [],
      userInfo: payload.data || {},
      category: payload.category,
      ...(Platform.OS === 'android' && {
        largeIcon: payload.largeIcon || 'ic_launcher',
        bigText: payload.bigText || payload.body,
        importance: payload.priority === 'high' ? 'high' : 'default',
      }),
    };

    PushNotification.localNotification(notificationConfig);
    this.addToHistory(payload);
  }

  private shouldShowNotification(payload: NotificationPayload): boolean {
    if (!this.settings.enabled || !this.settings.categories[payload.category]) {
      return false;
    }

    if (this.settings.quietHours.enabled && this.isQuietHours()) {
      return payload.priority === 'high';
    }

    return true;
  }

  private isQuietHours(): boolean {
    const now = new Date();
    const currentTime = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}`;
    const { start, end } = this.settings.quietHours;

    if (start <= end) {
      return currentTime >= start && currentTime <= end;
    } else {
      return currentTime >= start || currentTime <= end;
    }
  }

  private handleForegroundMessage(remoteMessage: any): void {
    const payload: NotificationPayload = {
      id: remoteMessage.messageId || Date.now().toString(),
      title: remoteMessage.notification?.title || 'Fantasy Update',
      body: remoteMessage.notification?.body || '',
      data: remoteMessage.data,
      category: remoteMessage.data?.category || 'general',
      priority: remoteMessage.data?.priority || 'normal'
    };

    this.showImmediateNotification(payload);
  }

  private handleLocalNotification(notification: any): void {
    this.markAsRead(notification.id || notification.userInfo?.id);
  }

  private handleNotificationOpen(remoteMessage: any): void {
    const data = remoteMessage.data || {};
    this.navigateToRelevantScreen(data);
    this.markAsRead(remoteMessage.messageId);
  }

  private handleNotificationAction(notification: any): void {
    const actionId = notification.action;
    const notificationId = notification.id || notification.userInfo?.id;

    console.log('Notification action taken:', actionId, 'for notification:', notificationId);

    this.updateHistoryAction(notificationId, actionId);
    this.handleAction(actionId, notification.userInfo || {});
  }

  private navigateToRelevantScreen(data: Record<string, any>): void {
    // This would integrate with your navigation system
    console.log('Navigate to screen based on notification data:', data);
  }

  private handleAction(actionId: string, data: Record<string, any>): void {
    switch (actionId) {
      case 'accept_trade':
        console.log('Accept trade action:', data);
        break;
      case 'reject_trade':
        console.log('Reject trade action:', data);
        break;
      case 'view_lineup':
        console.log('View lineup action:', data);
        break;
      case 'set_lineup':
        console.log('Set lineup action:', data);
        break;
      default:
        console.log('Unknown action:', actionId, data);
    }
  }

  private async sendTokenToServer(token: string): Promise<void> {
    try {
      // This would send the token to your backend
      console.log('Sending device token to server:', token);
      // await ApiClient.getInstance().post('/users/device-token', { token, platform: Platform.OS });
    } catch (error) {
      console.error('Failed to send token to server:', error);
    }
  }

  public async updateSettings(newSettings: Partial<NotificationSettings>): Promise<void> {
    this.settings = { ...this.settings, ...newSettings };
    await this.saveSettings();
  }

  public getSettings(): NotificationSettings {
    return { ...this.settings };
  }

  public async clearAllNotifications(): Promise<void> {
    PushNotification.cancelAllLocalNotifications();
    if (Platform.OS === 'ios') {
      PushNotificationIOS.removeAllDeliveredNotifications();
    }
  }

  public async cancelNotification(id: string): Promise<void> {
    PushNotification.cancelLocalNotifications({ id });
  }

  public getNotificationHistory(): NotificationHistory[] {
    return [...this.history].sort((a, b) => b.receivedAt - a.receivedAt);
  }

  public getUnreadNotifications(): NotificationHistory[] {
    return this.history.filter(item => !item.readAt);
  }

  public async markAsRead(id: string): Promise<void> {
    const item = this.history.find(h => h.id === id);
    if (item && !item.readAt) {
      item.readAt = Date.now();
      await this.saveHistory();
    }
  }

  public async markAllAsRead(): Promise<void> {
    const now = Date.now();
    this.history.forEach(item => {
      if (!item.readAt) {
        item.readAt = now;
      }
    });
    await this.saveHistory();
  }

  private addToHistory(payload: NotificationPayload): void {
    const historyItem: NotificationHistory = {
      id: payload.id,
      payload,
      receivedAt: Date.now()
    };

    this.history.unshift(historyItem);

    // Keep only last 100 notifications
    if (this.history.length > 100) {
      this.history = this.history.slice(0, 100);
    }

    this.saveHistory();
  }

  private updateHistoryAction(id: string, actionId: string): void {
    const item = this.history.find(h => h.id === id);
    if (item) {
      item.actionTaken = actionId;
      item.readAt = Date.now();
      this.saveHistory();
    }
  }

  private async loadSettings(): Promise<void> {
    try {
      const data = await AsyncStorage.getItem('notification_settings');
      if (data) {
        this.settings = { ...this.settings, ...JSON.parse(data) };
      }
    } catch (error) {
      console.error('Failed to load notification settings:', error);
    }
  }

  private async saveSettings(): Promise<void> {
    try {
      await AsyncStorage.setItem('notification_settings', JSON.stringify(this.settings));
    } catch (error) {
      console.error('Failed to save notification settings:', error);
    }
  }

  private async loadHistory(): Promise<void> {
    try {
      const data = await AsyncStorage.getItem('notification_history');
      if (data) {
        this.history = JSON.parse(data);
      }
    } catch (error) {
      console.error('Failed to load notification history:', error);
    }
  }

  private async saveHistory(): Promise<void> {
    try {
      await AsyncStorage.setItem('notification_history', JSON.stringify(this.history));
    } catch (error) {
      console.error('Failed to save notification history:', error);
    }
  }

  public getDeviceToken(): string | null {
    return this.deviceToken;
  }

  public async refreshToken(): Promise<string | null> {
    try {
      await messaging().deleteToken();
      const newToken = await messaging().getToken();
      this.deviceToken = newToken;
      this.sendTokenToServer(newToken);
      return newToken;
    } catch (error) {
      console.error('Failed to refresh token:', error);
      return null;
    }
  }

  public isInitialized(): boolean {
    return this.initialized;
  }
}

export default PushNotificationService.getInstance();