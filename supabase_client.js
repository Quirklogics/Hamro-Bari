/**
 * HAMRO BAARI (हाम्रो बारी) - SUPABASE & BACKEND API CLIENT
 * Supports both:
 * 1. Direct Supabase JavaScript Client (via Supabase CDN or REST)
 * 2. Local/Remote FastAPI Backend API (http://localhost:8000/api)
 */

const DB_CONFIG = {
  // Option A: FastAPI Backend Server URL
  API_BASE_URL: 'http://localhost:8000/api',

  // Option B: Supabase Direct Credentials (can also be read from window.ENV or config)
  SUPABASE_URL: '',      // e.g. 'https://xyzcompany.supabase.co'
  SUPABASE_ANON_KEY: '', // e.g. 'eyJhbGciOiJIUzI1NiIsInR5cCI...'
};

const dbApi = {
  /**
   * Check if backend API is reachable
   */
  async checkHealth() {
    try {
      const res = await fetch(`${DB_CONFIG.API_BASE_URL}/health`, { signal: AbortSignal.timeout(3000) });
      return res.ok;
    } catch {
      return false;
    }
  },

  /**
   * Fetch all produce from Supabase / FastAPI
   */
  async getProduce(filters = {}) {
    const params = new URLSearchParams();
    if (filters.category && filters.category !== 'all') params.append('category', filters.category);
    if (filters.districts && filters.districts.length > 0) params.append('district', filters.districts.join(','));
    if (filters.search) params.append('search', filters.search);
    if (filters.maxPrice) params.append('max_price', filters.maxPrice);
    if (filters.sortBy) params.append('sort', filters.sortBy);

    const url = `${DB_CONFIG.API_BASE_URL}/produce?${params.toString()}`;
    const res = await fetch(url);
    if (!res.ok) throw new Error(`Failed to fetch produce: ${res.statusText}`);
    return await res.json();
  },

  /**
   * Submit Customer Pre-order to Supabase database
   */
  async submitOrder(orderPayload) {
    const res = await fetch(`${DB_CONFIG.API_BASE_URL}/orders`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(orderPayload)
    });
    if (!res.ok) throw new Error(`Order submission failed: ${res.statusText}`);
    return await res.json();
  },

  /**
   * Record a farmer voice harvest batch into Supabase
   */
  async submitFarmerBatch(batchPayload) {
    const res = await fetch(`${DB_CONFIG.API_BASE_URL}/farmer/batches`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(batchPayload)
    });
    if (!res.ok) throw new Error(`Farmer batch recording failed: ${res.statusText}`);
    return await res.json();
  },

  /**
   * Fetch operational metrics for Admin console
   */
  async getAdminMetrics() {
    const res = await fetch(`${DB_CONFIG.API_BASE_URL}/admin/metrics`);
    if (!res.ok) throw new Error(`Metrics fetch failed: ${res.statusText}`);
    return await res.json();
  }
};

window.dbApi = dbApi;
