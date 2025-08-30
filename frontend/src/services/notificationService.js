import { toast } from 'react-toastify';

class NotificationService {
  constructor() {
    this.permission = 'default';
    this.isSupported = 'Notification' in window;
    this.notifications = [];
    this.listeners = new Set();
    // Initialize permission status synchronously
    if (this.isSupported) {
      this.permission = Notification.permission;
    }
  }



  async requestPermission() {
    if (!this.isSupported) {
      console.warn('Notifications not supported in this browser');
      return false;
    }

    try {
      const permission = await Notification.requestPermission();
      this.permission = permission;
      
      if (permission === 'granted') {
        console.log('Notification permission granted');
        return true;
      } else {
        console.log('Notification permission denied');
        return false;
      }
    } catch (error) {
      console.error('Error requesting notification permission:', error);
      return false;
    }
  }

  async showNotification(title, options = {}) {
    // Check if notifications are enabled in user preferences
    const userPreferences = this.getUserPreferences();
    if (!userPreferences.notifications) {
      return false;
    }

    // Show in-app toast notification
    this.showInAppNotification(title, options);

    // Show push notification if permission granted
    if (this.permission === 'granted' && this.isSupported) {
      try {
        const notification = new Notification(title, {
          icon: '/favicon.svg',
          badge: '/favicon.svg',
          tag: options.tag || 'awsset-notification',
          requireInteraction: options.requireInteraction || false,
          silent: !userPreferences.soundEnabled,
          ...options
        });

        // Handle notification click
        notification.onclick = () => {
          window.focus();
          notification.close();
          if (options.onClick) {
            options.onClick();
          }
        };

        // Auto-close after 5 seconds unless requireInteraction is true
        if (!options.requireInteraction) {
          setTimeout(() => {
            notification.close();
          }, 5000);
        }

        // Store notification for history
        this.addNotification({
          id: Date.now(),
          title,
          message: options.body || '',
          type: options.type || 'info',
          timestamp: new Date(),
          read: false
        });

        return notification;
      } catch (error) {
        console.error('Error showing push notification:', error);
        return false;
      }
    }

    return false;
  }

  showInAppNotification(title, options = {}) {
    const { type = 'info', message = title } = options;
    
    switch (type) {
      case 'success':
        toast.success(message);
        break;
      case 'warning':
        toast.warning(message);
        break;
      case 'error':
        toast.error(message);
        break;
      case 'info':
      default:
        toast.info(message);
        break;
    }
  }

  addNotification(notification) {
    this.notifications.unshift(notification);
    
    // Keep only last 100 notifications
    if (this.notifications.length > 100) {
      this.notifications = this.notifications.slice(0, 100);
    }

    // Save to localStorage
    this.saveNotifications();
    
    // Notify listeners
    this.notifyListeners();
  }

  getNotifications() {
    return this.notifications;
  }

  getUnreadCount() {
    return this.notifications.filter(n => !n.read).length;
  }

  markAsRead(notificationId) {
    const notification = this.notifications.find(n => n.id === notificationId);
    if (notification) {
      notification.read = true;
      this.saveNotifications();
      this.notifyListeners();
    }
  }

  markAllAsRead() {
    this.notifications.forEach(n => n.read = true);
    this.saveNotifications();
    this.notifyListeners();
  }

  clearNotifications() {
    this.notifications = [];
    this.saveNotifications();
    this.notifyListeners();
  }

  saveNotifications() {
    try {
      localStorage.setItem('awsset-notifications', JSON.stringify(this.notifications));
    } catch (error) {
      console.error('Error saving notifications to localStorage:', error);
    }
  }

  loadNotifications() {
    try {
      const saved = localStorage.getItem('awsset-notifications');
      if (saved) {
        this.notifications = JSON.parse(saved);
        // Convert timestamp strings back to Date objects
        this.notifications.forEach(n => {
          if (typeof n.timestamp === 'string') {
            n.timestamp = new Date(n.timestamp);
          }
        });
      }
    } catch (error) {
      console.error('Error loading notifications from localStorage:', error);
      this.notifications = [];
    }
  }

  addListener(callback) {
    this.listeners.add(callback);
    return () => this.listeners.delete(callback);
  }

  notifyListeners() {
    this.listeners.forEach(callback => {
      try {
        callback(this.notifications, this.getUnreadCount());
      } catch (error) {
        console.error('Error in notification listener:', error);
      }
    });
  }

  getUserPreferences() {
    try {
      const saved = localStorage.getItem('awsset-notification-preferences');
      return saved ? JSON.parse(saved) : {
        notifications: true,
        soundEnabled: true,
        emailAlerts: true,
        autoRefresh: true,
        refreshInterval: 30
      };
    } catch (error) {
      console.error('Error loading notification preferences:', error);
      return {
        notifications: true,
        soundEnabled: true,
        emailAlerts: true,
        autoRefresh: true,
        refreshInterval: 30
      };
    }
  }

  saveUserPreferences(preferences) {
    try {
      localStorage.setItem('awsset-notification-preferences', JSON.stringify(preferences));
      
      // Update permission if notifications were disabled
      if (!preferences.notifications && this.permission === 'granted') {
        // Note: We can't revoke permission, but we can stop showing notifications
        console.log('Notifications disabled by user preference');
      }
    } catch (error) {
      console.error('Error saving notification preferences:', error);
    }
  }

  // Test notification
  async testNotification() {
    return await this.showNotification('Test Notification', {
      body: 'This is a test notification from AWSSET',
      type: 'info',
      tag: 'test-notification'
    });
  }

  // Show different types of notifications
  async showSuccessNotification(title, message) {
    return await this.showNotification(title, {
      body: message,
      type: 'success'
    });
  }

  async showWarningNotification(title, message) {
    return await this.showNotification(title, {
      body: message,
      type: 'warning'
    });
  }

  async showErrorNotification(title, message) {
    return await this.showNotification(title, {
      body: message,
      type: 'error'
    });
  }

  async showInfoNotification(title, message) {
    return await this.showNotification(title, {
      body: message,
      type: 'info'
    });
  }
}

// Create singleton instance
const notificationService = new NotificationService();

// Load saved notifications on initialization
notificationService.loadNotifications();

export default notificationService;
