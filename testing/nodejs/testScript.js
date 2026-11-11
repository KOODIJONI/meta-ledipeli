const mqtt = require('mqtt');

const brokerUrl = 'mqtt://localhost:1883';
const topic = `test/nodejs/${Math.random().toString(16).slice(2, 8)}`;


const client = mqtt.connect(brokerUrl, {
    clientId: `node_test_${Math.random().toString(16).slice(2, 8)}`,
    clean: true,
    connectTimeout: 4000,
    });

client.on('connect', () => {
    console.log(`Connected to ${brokerUrl}`);

client.subscribe(topic, { qos: 1}, (err) => {
    if (err) {
        console.error('Connection error:', err);
        client.end;
        return;
    }
    console.log(`Subscibed to ${topic}`);

    const payload = JSON.stringify({
    status: 'ok',
    timestamp: new Date().toISOString(),
    });
    client.publish(topic, payload, {qos:1},(pubErr) => {
        if (pubErr) console.error('Publish error:', pubErr);
    });
    });
});
// Listen for incoming messages
client.on('message', (receivedTopic, message) => {
  console.log(`Received on [${receivedTopic}]: ${message.toString()}`);
  // Close connection cleanly after verifying the round-trip
  client.end();
});

// Handle connection errors
client.on('error', (err) => {
  console.error('Connection error:', err);
  client.end();
});