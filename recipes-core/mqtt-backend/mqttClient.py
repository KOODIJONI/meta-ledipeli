import paho.mqtt.client as mqtt

class MqttPublisher:
    def __init__(self, client_id, topic, payload):
        # Client ID HAS to be unique
        self.client_id = client_id
        self.topic = topic
        self.payload = payload
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=self.client_id)

        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_publish = self.on_publish

        print("Publisher using client_id / topic: " + self.client_id + " / " + self.topic)
    
    def on_connect(self, client, userdata, flags, reason_code, properties):
        # Doesn't subscribe on connect
        if (reason_code.is_failure):
            print(f"{self.client_id} failed to connect {self.topic} with reason code {reason_code}")
        else:
            print(f"{self.client_id} connected to {self.topic} with reason code {reason_code}")

    def on_disconnect(self, client, userdata, flags, reason_code, properties):
        if (reason_code.is_failure):
            print(f"{self.client_id} Failed to disconnect from topic {self.topic} with reason code {reason_code}")
        else:
            print(f"{self.client_id} Disconnected from topic {self.topic} with reason code {reason_code}")
    
    def on_publish(self, client, userdata, mid, reason_code, properties):
        if (reason_code.is_failure):
            print(f"{self.client_id} failed to publish {self.payload} to {self.topic} with reason code {reason_code}")
        else:
            print(f"{self.client_id} published {self.payload} to {self.topic} with reason code {reason_code}")

    def start_loop(self, broker, port, keepalive):
        self.client.connect(broker, port, keepalive)
        self.client.loop_start()
    
    def end_loop(self):
        self.client.disconnect()
        self.client.loop_stop()
    
    def publish(self, topic, qos = 0):
        print(f"Publishing {self.payload}")
        self.client.publish(topic, self.payload, qos)

class MqttSubscriber(MqttPublisher):
    def __init__(self, client_id, topic):
        # Client ID HAS to be unique
        self.client_id = client_id
        self.topic = topic
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=self.client_id)
        self.payload = None
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_subscribe = self.on_subscribe
        self.client.on_unsubscribe = self.on_unsubscribe
        self.client.on_disconnect = self.on_disconnect

        print("Publisher using client_id / topic: " + self.client_id + " / " + self.topic)

    def on_connect(self, client, userdata, flags, reason_code, properties):
        print(f"{self.client_id} connected to {self.topic} with reason code {reason_code}")
        client.subscribe(self.topic)

    def on_message(self, client, userdata, msg):
        self.payload = msg.payload.decode("utf-8")
        print(f"{self.client_id} recived on {msg.topic}: {self.payload}")

    def on_subscribe(self, client, userdata, mid, reason_code_list, properties):
        if reason_code_list[0].is_failure:
            print(f"Broker rejected you subscription: {reason_code_list[0]}")
        else:
            print(f"Broker granted the following QoS: {reason_code_list[0].value}")

    def on_unsubscribe(self, client, userdata, mid, reason_code_list, properties):
        if len(reason_code_list) == 0 or not reason_code_list[0].is_failure:
            print("unsubscribe succeeded")
        else:
            print(f"Broker replied with failure: {reason_code_list[0]}")
        
    def publish(self, topic , qos = 0):
        print(f"Publishing on a listener not allowed ):<")
