/**
 * Direct Connection Client
 * 
 * Discovers and connects directly to the user's local execution node,
 * bypassing the cloud for actual execution.
 * 
 * The cloud is only used for:
 * 1. Authentication
 * 2. Discovery (finding the execution node)
 * 3. Fallback if direct connection fails
 */

class DirectConnectionClient {
    constructor() {
        this.executionNodeUrl = null;
        this.isConnected = false;
        this.useDirectConnection = true;
    }

    /**
     * Discover the user's execution node
     */
    async discover(userId) {
        try {
            // Ask cloud: where is this user's execution node?
            const response = await fetch(`/digital-twin/api/direct_connection/discover/${userId}`);
            const data = await response.json();

            if (data.found) {
                // Found! Try to connect directly
                const nodeUrl = data.connection_instructions.preferred;
                console.log(`📍 Discovered execution node at: ${nodeUrl}`);

                // Test connection
                if (await this.testConnection(nodeUrl)) {
                    this.executionNodeUrl = nodeUrl;
                    this.isConnected = true;
                    console.log(`✅ Direct connection established!`);
                    return true;
                } else {
                    console.log(`⚠️  Could not connect directly to: ${nodeUrl}`);
                    // Try fallback if available
                    if (data.connection_instructions.fallback) {
                        const fallback = data.connection_instructions.fallback;
                        if (await this.testConnection(fallback)) {
                            this.executionNodeUrl = fallback;
                            this.isConnected = true;
                            console.log(`✅ Connected via fallback: ${fallback}`);
                            return true;
                        }
                    }
                }
            } else {
                console.log(`❌ Execution node not found: ${data.message}`);
            }

            return false;
        } catch (error) {
            console.error('Discovery error:', error);
            return false;
        }
    }

    /**
     * Test if we can reach the execution node
     */
    async testConnection(nodeUrl) {
        try {
            const response = await fetch(`${nodeUrl}/digital-twin/api/health/`, {
                method: 'GET',
                mode: 'cors',  // Allow cross-origin
                timeout: 5000
            });
            return response.ok;
        } catch (error) {
            console.log(`Connection test failed for ${nodeUrl}:`, error.message);
            return false;
        }
    }

    /**
     * Send message directly to execution node
     */
    async sendToExecutionNode(conversationId, message, history, authToken) {
        if (!this.isConnected || !this.executionNodeUrl) {
            throw new Error('Not connected to execution node');
        }

        try {
            const response = await fetch(`${this.executionNodeUrl}/digital-twin/api/think/`, {
                method: 'POST',
                mode: 'cors',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${authToken}`
                },
                body: JSON.stringify({
                    input: message,
                    context: {
                        conversation_id: conversationId,
                        user_intent: 'chat'
                    },
                    history: history
                })
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('Direct connection failed:', error);
            // Mark as disconnected
            this.isConnected = false;
            this.executionNodeUrl = null;
            throw error;
        }
    }

    /**
     * Send through cloud (fallback)
     */
    async sendThroughCloud(conversationId, message, authToken) {
        const response = await fetch('/chat-app/api/chat/send', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${authToken}`
            },
            body: JSON.stringify({
                conversation_id: conversationId,
                content: message,
                sender: 'user'
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        return await response.json();
    }

    /**
     * Smart send - tries direct first, falls back to cloud
     */
    async sendMessage(conversationId, message, userId, authToken) {
        // Try direct connection first (if enabled)
        if (this.useDirectConnection) {
            // Discover if not already connected
            if (!this.isConnected) {
                console.log('🔍 Discovering execution node...');
                await this.discover(userId);
            }

            // If connected, try direct
            if (this.isConnected) {
                try {
                    console.log('🏠 Sending via direct connection...');
                    const result = await this.sendToExecutionNode(
                        conversationId,
                        message,
                        [], // history would be loaded from state
                        authToken
                    );
                    console.log('✅ Direct connection successful!');
                    return {
                        success: true,
                        mode: 'direct',
                        data: result
                    };
                } catch (error) {
                    console.log('⚠️  Direct connection failed, using cloud fallback...');
                }
            }
        }

        // Fallback to cloud
        console.log('☁️  Sending via cloud...');
        const result = await this.sendThroughCloud(conversationId, message, authToken);
        return {
            success: true,
            mode: 'cloud',
            data: result
        };
    }

    /**
     * Get connection status
     */
    getStatus() {
        return {
            isConnected: this.isConnected,
            executionNodeUrl: this.executionNodeUrl,
            useDirectConnection: this.useDirectConnection
        };
    }

    /**
     * Enable/disable direct connection
     */
    setDirectConnection(enabled) {
        this.useDirectConnection = enabled;
        console.log(`Direct connection ${enabled ? 'enabled' : 'disabled'}`);
    }
}

// Global instance
window.DirectConnection = new DirectConnectionClient();
