/**
 * Global AWS Credential Cache Service
 * Prevents repeated API calls for credentials across page navigations
 */

class CredentialCacheService {
  constructor() {
    this.credentials = null;
    this.lastFetch = null;
    this.cacheExpiry = 5 * 60 * 1000; // 5 minutes
    this.isFetching = false;
    this.fetchPromise = null;
  }

  /**
   * Get credentials from cache or fetch if needed
   */
  async getCredentials(api, forceRefresh = false) {
    // Return cached credentials if they exist and haven't expired
    if (!forceRefresh && this.credentials && this.lastFetch && 
        (Date.now() - this.lastFetch) < this.cacheExpiry) {
      console.log('📋 Returning cached AWS credentials');
      return this.credentials;
    }

    // If already fetching, return the existing promise
    if (this.isFetching && this.fetchPromise) {
      console.log('📋 Credentials already being fetched, waiting...');
      return this.fetchPromise;
    }

    // Fetch new credentials
    console.log('📋 Fetching fresh AWS credentials...');
    this.isFetching = true;
    
    try {
      const response = await api.get('/api/aws/credentials');
      this.credentials = response.data;
      this.lastFetch = Date.now();
      
      // Cache in localStorage for persistence across browser sessions
      localStorage.setItem('awsset-cached-credentials', JSON.stringify({
        credentials: this.credentials,
        timestamp: this.lastFetch
      }));
      
      console.log('📋 AWS credentials cached successfully');
      return this.credentials;
    } catch (error) {
      console.error('Failed to fetch AWS credentials:', error);
      this.credentials = null;
      throw error;
    } finally {
      this.isFetching = false;
      this.fetchPromise = null;
    }
  }

  /**
   * Update cached credentials (e.g., after storing new ones)
   */
  updateCredentials(newCredentials) {
    this.credentials = newCredentials;
    this.lastFetch = Date.now();
    
    // Update localStorage
    localStorage.setItem('awsset-cached-credentials', JSON.stringify({
      credentials: this.credentials,
      timestamp: this.lastFetch
    }));
    
    console.log('📋 AWS credentials cache updated');
  }

  /**
   * Clear cached credentials (e.g., after removal)
   */
  clearCredentials() {
    this.credentials = null;
    this.lastFetch = null;
    localStorage.removeItem('awsset-cached-credentials');
    console.log('📋 AWS credentials cache cleared');
  }

  /**
   * Load credentials from localStorage on app startup
   */
  loadFromStorage() {
    try {
      const cached = localStorage.getItem('awsset-cached-credentials');
      if (cached) {
        const { credentials, timestamp } = JSON.parse(cached);
        
        // Check if cache is still valid
        if (timestamp && (Date.now() - timestamp) < this.cacheExpiry) {
          this.credentials = credentials;
          this.lastFetch = timestamp;
          console.log('📋 Loaded AWS credentials from localStorage cache');
          return true;
        } else {
          // Cache expired, remove it
          localStorage.removeItem('awsset-cached-credentials');
          console.log('📋 AWS credentials cache expired, removed');
        }
      }
    } catch (error) {
      console.error('Error loading credentials from localStorage:', error);
      localStorage.removeItem('awsset-cached-credentials');
    }
    return false;
  }

  /**
   * Get cached credentials without fetching
   */
  getCachedCredentials() {
    return this.credentials;
  }

  /**
   * Check if credentials are cached and valid
   */
  hasValidCache() {
    return this.credentials && this.lastFetch && 
           (Date.now() - this.lastFetch) < this.cacheExpiry;
  }

  /**
   * Force refresh credentials
   */
  async refreshCredentials(api) {
    return this.getCredentials(api, true);
  }
}

// Create singleton instance
const credentialCacheService = new CredentialCacheService();

// Load any existing cache on service initialization
credentialCacheService.loadFromStorage();

export default credentialCacheService;
