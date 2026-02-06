/**
 * User-Specific AWS Credential Cache Service
 * Prevents repeated API calls for credentials across page navigations
 * Each user has their own isolated cache
 */
import { debugLog } from '../utils/env';
class CredentialCacheService {
  constructor() {
    this.userCredentials = new Map(); // Map of user ID to credentials
    this.cacheExpiry = 5 * 60 * 1000; // 5 minutes
    this.isFetching = new Map(); // Track fetching state per user
    this.fetchPromises = new Map(); // Track fetch promises per user
  }

  /**
   * Get user ID from the API instance (extract from auth headers)
   */
  _getUserId(api) {
    try {
      // Try to get user ID from localStorage or decode JWT token
      const token = localStorage.getItem('access_token');
      if (token) {
        // Simple JWT decode to get user ID (payload.sub)
        const payload = JSON.parse(atob(token.split('.')[1]));
        return payload.sub || payload.user_id || 'unknown';
      }
    } catch (error) {
      console.warn('Could not extract user ID from token:', error);
    }
    return 'unknown';
  }

  /**
   * Get cache key for a specific user
   */
  _getCacheKey(userId) {
    return `awsset-cached-credentials-${userId}`;
  }

  /**
   * Get credentials from cache or fetch if needed
   */
  async getCredentials(api, forceRefresh = false) {
    const userId = this._getUserId(api);
    const cacheKey = this._getCacheKey(userId);
    
    // Return cached credentials if they exist and haven't expired
    const userCache = this.userCredentials.get(userId);
    if (!forceRefresh && userCache && userCache.lastFetch && 
        (Date.now() - userCache.lastFetch) < this.cacheExpiry) {
      debugLog(`📋 Returning cached AWS credentials for user ${userId}`);
      return userCache.credentials;
    }

    // If already fetching for this user, return the existing promise
    if (this.isFetching.get(userId) && this.fetchPromises.get(userId)) {
      debugLog(`📋 Credentials already being fetched for user ${userId}, waiting...`);
      return this.fetchPromises.get(userId);
    }

    // Fetch new credentials
    debugLog(`📋 Fetching fresh AWS credentials for user ${userId}...`);
    this.isFetching.set(userId, true);
    
    try {
      const response = await api.get('/api/aws/credentials');
      const credentialsData = response.data;
      
      // Update user-specific cache
      this.userCredentials.set(userId, {
        credentials: credentialsData,
        lastFetch: Date.now()
      });
      
      // Cache in localStorage for persistence across browser sessions (user-specific)
      localStorage.setItem(cacheKey, JSON.stringify({
        credentials: credentialsData,
        timestamp: Date.now()
      }));
      
      debugLog(`📋 AWS credentials cached successfully for user ${userId}`);
      return credentialsData;
    } catch (error) {
      console.error(`Failed to fetch AWS credentials for user ${userId}:`, error);
      // Clear user cache on error
      this.userCredentials.delete(userId);
      throw error;
    } finally {
      this.isFetching.set(userId, false);
      this.fetchPromises.delete(userId);
    }
  }

  /**
   * Update cached credentials for a specific user
   */
  updateCredentials(newCredentials, api) {
    const userId = this._getUserId(api);
    const cacheKey = this._getCacheKey(userId);
    
    // Update user-specific cache
    this.userCredentials.set(userId, {
      credentials: newCredentials,
      lastFetch: Date.now()
    });
    
    // Update localStorage
    localStorage.setItem(cacheKey, JSON.stringify({
      credentials: newCredentials,
      timestamp: Date.now()
    }));
    
    debugLog(`📋 AWS credentials cache updated for user ${userId}`);
  }

  /**
   * Clear cached credentials for a specific user
   */
  clearCredentials(api) {
    const userId = this._getUserId(api);
    const cacheKey = this._getCacheKey(userId);
    
    // Clear user-specific cache
    this.userCredentials.delete(userId);
    this.isFetching.delete(userId);
    this.fetchPromises.delete(userId);
    
    // Clear localStorage
    localStorage.removeItem(cacheKey);
    
    debugLog(`📋 AWS credentials cache cleared for user ${userId}`);
  }

  /**
   * Load credentials from localStorage on app startup for a specific user
   */
  loadFromStorage(api) {
    const userId = this._getUserId(api);
    const cacheKey = this._getCacheKey(userId);
    
    try {
      const cached = localStorage.getItem(cacheKey);
      if (cached) {
        const { credentials, timestamp } = JSON.parse(cached);
        
        // Check if cache is still valid
        if (timestamp && (Date.now() - timestamp) < this.cacheExpiry) {
          this.userCredentials.set(userId, {
            credentials: credentials,
            lastFetch: timestamp
          });
          debugLog(`📋 Loaded AWS credentials from localStorage cache for user ${userId}`);
          return true;
        } else {
          // Cache expired, remove it
          localStorage.removeItem(cacheKey);
          debugLog(`📋 AWS credentials cache expired for user ${userId}, removed`);
        }
      }
    } catch (error) {
      console.error(`Failed to load cached credentials for user ${userId}:`, error);
      localStorage.removeItem(cacheKey);
    }
    
    return false;
  }

  /**
   * Get cached credentials for a specific user without fetching
   */
  getCachedCredentials(api) {
    const userId = this._getUserId(api);
    const userCache = this.userCredentials.get(userId);
    
    if (userCache && userCache.credentials && userCache.lastFetch && 
        (Date.now() - userCache.lastFetch) < this.cacheExpiry) {
      return userCache.credentials;
    }
    
    return null;
  }

  /**
   * Check if user has valid cached credentials
   */
  hasValidCache(api) {
    const userId = this._getUserId(api);
    const userCache = this.userCredentials.get(userId);
    
    return userCache && userCache.credentials && userCache.lastFetch && 
           (Date.now() - userCache.lastFetch) < this.cacheExpiry;
  }

  /**
   * Refresh credentials for a specific user
   */
  async refreshCredentials(api) {
    return this.getCredentials(api, true);
  }

  /**
   * Clear all user caches (useful for logout)
   */
  clearAllCaches() {
    this.userCredentials.clear();
    this.isFetching.clear();
    this.fetchPromises.clear();
    
    // Clear all localStorage keys that match our pattern
    Object.keys(localStorage).forEach(key => {
      if (key.startsWith('awsset-cached-credentials-')) {
        localStorage.removeItem(key);
      }
    });
    
    debugLog('📋 All AWS credentials caches cleared');
  }
}

// Export singleton instance
const credentialCacheService = new CredentialCacheService();
export default credentialCacheService;
