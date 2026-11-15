import mqtt from 'mqtt';

class MqttJsonRpc {
  constructor(brokerUrl) {
    this.client = mqtt.connect(brokerUrl);
    this.pendingRequests = new Map();
    this.topicListeners = new Map(); // Stores callbacks per topic filter
    this.requestId = 0;
    this.onConnectionChange = null;

    this.client.on('connect', () => {
      console.log('Connected to MQTT Broker via WebSockets');
      if (this.onConnectionChange) this.onConnectionChange(true);

      // Subscribe to the JSON-RPC response topic
      this.client.subscribe('device/response', (err) => {
        if (err) console.error('RPC response subscription error:', err);
      });

      // Re-subscribe to any custom topics (useful on auto-reconnect)
      for (const topic of this.topicListeners.keys()) {
        this.client.subscribe(topic);
      }
    });

    this.client.on('offline', () => {
      if (this.onConnectionChange) this.onConnectionChange(false);
    });

    this.client.on('message', (topic, message) => {
      const payloadStr = message.toString();

      // 1. Handle JSON-RPC 2.0 responses
      if (topic === 'device/response') {
        try {
          const response = JSON.parse(payloadStr);
          if (response.id && this.pendingRequests.has(response.id)) {
            const { resolve, reject } = this.pendingRequests.get(response.id);
            this.pendingRequests.delete(response.id);

            if (response.error) {
              reject(new Error(response.error.message || 'JSON-RPC Error'));
            } else {
              resolve(response.result);
            }
          }
        } catch (e) {
          console.error('Failed to parse incoming JSON-RPC message:', e);
        }
        return;
      }

      // 2. Route standard MQTT messages to matching topic listeners.
      // Preserve raw binary payloads so matrix/GRB blobs are not destroyed by UTF-8 conversion.
      for (const [filter, callbacks] of this.topicListeners.entries()) {
        if (this._topicMatches(filter, topic)) {
          callbacks.forEach((cb) => cb(message, topic));
        }
      }
    });
  }

  /**
   * Execute a JSON-RPC 2.0 call over MQTT
   */
  call(method, params = {}, timeoutMs = 5000) {
    return new Promise((resolve, reject) => {
      const id = ++this.requestId;

      const timer = setTimeout(() => {
        if (this.pendingRequests.has(id)) {
          this.pendingRequests.delete(id);
          reject(new Error(`RPC timeout after ${timeoutMs}ms for method: ${method}`));
        }
      }, timeoutMs);

      this.pendingRequests.set(id, {
        resolve: (res) => {
          clearTimeout(timer);
          resolve(res);
        },
        reject: (err) => {
          clearTimeout(timer);
          reject(err);
        },
      });

      const payload = JSON.stringify({
        jsonrpc: '2.0',
        method,
        params,
        id,
      });

      this.client.publish('device/request', payload, (err) => {
        if (err) {
          clearTimeout(timer);
          this.pendingRequests.delete(id);
          reject(err);
        }
      });
    });
  }

  /**
   * Publish a raw string or JSON object to any MQTT topic
   */
  publish(topic, payload, options = {}) {
    return new Promise((resolve, reject) => {
      const message = typeof payload === 'object' ? JSON.stringify(payload) : String(payload);
      this.client.publish(topic, message, options, (err) => {
        if (err) reject(err);
        else resolve();
      });
    });
  }

  /**
   * Subscribe to an MQTT topic and register a message callback.
   * Returns an unsubscribe cleanup function (ideal for React useEffect).
   */
  subscribe(topic, callback) {
    if (!this.topicListeners.has(topic)) {
      this.topicListeners.set(topic, new Set());
      if (this.client.connected) {
        this.client.subscribe(topic, (err) => {
          if (err) console.error(`Failed to subscribe to ${topic}:`, err);
        });
      }
    }

    this.topicListeners.get(topic).add(callback);

    // Return cleanup function
    return () => {
      const listeners = this.topicListeners.get(topic);
      if (listeners) {
        listeners.delete(callback);
        if (listeners.size === 0) {
          this.topicListeners.delete(topic);
          if (this.client.connected) {
            this.client.unsubscribe(topic);
          }
        }
      }
    };
  }

  /**
   * Helper to match incoming topics against MQTT '+' and '#' wildcards
   */
  _topicMatches(filter, topic) {
    if (filter === topic) return true;
    const filterParts = filter.split('/');
    const topicParts = topic.split('/');

    for (let i = 0; i < filterParts.length; i++) {
      if (filterParts[i] === '#') return true;
      if (filterParts[i] === '+') continue;
      if (filterParts[i] !== topicParts[i]) return false;
    }
    return filterParts.length === topicParts.length;
  }
}

// Export singleton instance using the target device's current hostname
const brokerUrl = `ws://${window.location.hostname}:9001`;
export const rpcClient = new MqttJsonRpc(brokerUrl);
