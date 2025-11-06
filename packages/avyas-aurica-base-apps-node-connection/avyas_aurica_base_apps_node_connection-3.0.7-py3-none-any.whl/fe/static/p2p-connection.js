/**
 * P2P Connection Helper for Browser
 * 
 * This module helps browser establish direct connection to local execution node.
 * 
 * Usage:
 *   import { P2PConnection } from './p2p-connection.js';
 *   
 *   const p2p = new P2PConnection(authToken);
 *   await p2p.connect();
 *   
 *   if (p2p.isConnected) {
 *     const data = await p2p.fetch('/api/endpoint');
 *   }
 */

class P2PConnection {
    constructor(authToken, cloudUrl = 'https://api.oneaurica.com') {
        this.authToken = authToken;
        this.cloudUrl = cloudUrl.replace(/\/$/, '');
        this.nodeInfo = null;
        this.isConnected = false;
    }

    /**
     * Connect to execution node
     * 
     * 1. Fetch connection info from cloud
     * 2. Verify node is online
     * 3. Test direct connection
     */
    async connect() {
        try {
            console.log('🔍 Fetching node connection info from cloud...');
            
            // Get connection info from cloud registry
            const response = await fetch(`${this.cloudUrl}/p2p/connection-info`, {
                headers: {
                    'Authorization': `Bearer ${this.authToken}`,
                    'Content-Type': 'application/json'
                }
            });

            if (!response.ok) {
                if (response.status === 404) {
                    throw new Error('No execution node registered. Please start your local server.');
                }
                throw new Error(`Failed to get connection info: ${response.statusText}`);
            }

            const result = await response.json();
            this.nodeInfo = result.node;

            console.log('📋 Node info received:', {
                node_id: this.nodeInfo.node_id,
                status: this.nodeInfo.status,
                is_online: this.nodeInfo.is_online,
                connection_url: this.nodeInfo.connection_url
            });

            // Check if node is online
            if (!this.nodeInfo.is_online) {
                throw new Error('Execution node is offline. Please start your local server.');
            }

            // Test direct connection
            console.log('🔌 Testing direct connection to execution node...');
            await this.testConnection();

            this.isConnected = true;
            console.log('✅ Connected to execution node successfully!');

            return true;

        } catch (error) {
            console.error('❌ Connection failed:', error.message);
            this.isConnected = false;
            throw error;
        }
    }

    /**
     * Test direct connection to execution node
     */
    async testConnection() {
        try {
            const testUrl = `${this.nodeInfo.connection_url}/health`;
            const response = await fetch(testUrl, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${this.authToken}`
                },
                // Add timeout
                signal: AbortSignal.timeout(5000)
            });

            if (!response.ok) {
                throw new Error('Health check failed');
            }

            console.log('✅ Direct connection test successful');
        } catch (error) {
            throw new Error(`Cannot reach execution node at ${this.nodeInfo.connection_url}: ${error.message}`);
        }
    }

    /**
     * Fetch from execution node
     * 
     * @param {string} path - API path (e.g., '/api/chat/messages')
     * @param {object} options - Fetch options
     */
    async fetch(path, options = {}) {
        if (!this.isConnected) {
            throw new Error('Not connected. Call connect() first.');
        }

        const url = `${this.nodeInfo.connection_url}${path}`;
        
        // Add auth header if not present
        const headers = {
            'Authorization': `Bearer ${this.authToken}`,
            ...options.headers
        };

        console.log(`→ Fetching: ${path}`);

        const response = await fetch(url, {
            ...options,
            headers
        });

        if (!response.ok) {
            console.error(`← Error ${response.status}: ${path}`);
        } else {
            console.log(`← Success ${response.status}: ${path}`);
        }

        return response;
    }

    /**
     * Get node status from cloud
     */
    async getNodeStatus() {
        const response = await fetch(`${this.cloudUrl}/p2p/status`, {
            headers: {
                'Authorization': `Bearer ${this.authToken}`
            }
        });

        if (!response.ok) {
            throw new Error('Failed to get node status');
        }

        return await response.json();
    }

    /**
     * Disconnect (just clears local state)
     */
    disconnect() {
        this.isConnected = false;
        this.nodeInfo = null;
        console.log('🔌 Disconnected from execution node');
    }
}

// Example usage
async function example() {
    try {
        // Get auth token (from login or storage)
        const authToken = localStorage.getItem('auth_token');
        
        // Create P2P connection
        const p2p = new P2PConnection(authToken);
        
        // Connect to execution node
        await p2p.connect();
        
        // Now make requests directly to execution node
        const response = await p2p.fetch('/api/chat/messages');
        const messages = await response.json();
        
        console.log('Messages:', messages);
        
        // Check node status
        const status = await p2p.getNodeStatus();
        console.log('Node status:', status);
        
    } catch (error) {
        console.error('Error:', error.message);
        
        // Show user-friendly error
        if (error.message.includes('not registered')) {
            alert('Please start your local execution node first.');
        } else if (error.message.includes('offline')) {
            alert('Your execution node is offline. Please check your local server.');
        } else {
            alert(`Connection error: ${error.message}`);
        }
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { P2PConnection };
}
