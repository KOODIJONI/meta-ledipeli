import paho.mqtt.client as mqtt

class MqttPublisher:
    def __init__(self, client_id, topic, payload):
        
        self.client_id = client_id
        self.topic = topic
        self.payload = payload
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=self.get_topic())

        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect

        print("Publisher using client_id / topic: " + self.get_topic())

    def on_connect(self, client, userdata, flags, reason_code, properties):
        print(f"Subscribing to {self.get_topic()} with reason code {reason_code}")
        client.subscribe(self.get_topic())  

    def on_disconnect(self, client, userdata, flags, reason_code, properties):
        print(f"Disconnected topic {self.get_topic()} with reason code {reason_code}")

    def get_topic(self):
        return self.client_id + self.topic
    
    def start_loop(self, broker, port, keepalive):
        self.client.connect(broker, port, keepalive)
        self.client.loop_start()
    
    def end_loop(self):
        self.client.disconnect()
        self.client.loop_stop()
    
    def publish(self, topic , qos = 0):
        print(f"Publishing {self.payload}")
        self.client.publish(topic, self.payload, qos)

class MqttListener(MqttPublisher):
    def __init__(self, client_id, topic):
        
        self.client_id = client_id
        self.topic = topic
        self.payload = ""
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=self.get_topic())

        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect

        print("Listener using client_id / topic: " + self.get_topic())

    def on_message(self, client, userdata, msg):
        self.payload = msg.payload.decode("utf-8")
        print(f"Recived on {msg.topic}: {self.payload}")
    
    def publish(self, topic , qos = 0):
        print(f"Publishing on a listener not allowed ):<")
