import paho.mqtt.client as mqtt

class MqttPublisher:
    def __init__(self, client_id, topic, payload):
        # Client ID HAS to be unique
        self.client_id = client_id
        self.topic = topic
        self.payload = payload
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=self.client_id)
        self.subscribedTo = []
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_publish = self.on_publish

        print("Publisher using client_id / topic: " + self.client_id + " / " + self.topic)
    
    def on_connect(self, client, userdata, flags, reason_code, properties):
        # Doesn't subscribe on connect
        if (reason_code.is_failure):
            print(f"{self.client_id} failed to connect with reason code {reason_code}")
        else:
            print(f"{self.client_id} connected with reason code {reason_code}")

    def on_disconnect(self, client, userdata, flags, reason_code, properties):
        if (reason_code.is_failure):
            print(f"{self.client_id} Failed to disconnect with reason code {reason_code}")
        else:
            print(f"{self.client_id} Disconnected with reason code {reason_code}")
    
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
    
    def publish(self, topic, payload, qos = 0):
        print(f"Publishing {payload}")
        self.client.publish(topic, payload, qos)

class MqttSubscriber(MqttPublisher):
    def __init__(self, client_id, topic, subscribeOnConnect = True):
        # Client ID HAS to be unique
        self.client_id = client_id
        self.topic = topic
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id=self.client_id)
        self.subscribedTopicsList = []
        self.subscribeOnConnect = subscribeOnConnect
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_subscribe = self.on_subscribe
        self.client.on_unsubscribe = self.on_unsubscribe
        self.client.on_disconnect = self.on_disconnect

        print("Publisher using client_id / topic: " + self.client_id + " / " + self.topic)

    def on_connect(self, client, userdata, flags, reason_code, properties):
        if (reason_code.is_failure):
            print(f"{self.client_id} failed to connect with reason code {reason_code}")
        else:
            print(f"{self.client_id} connected with reason code {reason_code}")
            if (self.subscribeOnConnect):
                self.subscribe(self.topic)
        
    def on_disconnect(self, client, userdata, flags, reason_code, properties):
        if (reason_code.is_failure):
            print(f"{self.client_id} Failed to disconnect with reason code {reason_code}")
        else:
            print(f"{self.client_id} Disconnected with reason code {reason_code}")
            self.subscribedTopicsList.clear()
            
    def on_message(self, client, userdata, msg):
        payload = msg.payload.decode("utf-8")
        self.addPayload(msg.topic, payload)
        print(f"{self.client_id} recived on {msg.topic}: {payload}")

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

    def subscribe(self, topic):
        #Meant for subscribing to multiple topics with one client
        print(f"{self.client_id} subscribing to {topic}")
        self.client.subscribe(topic)
        self.addSubscribedTopic(topic)
        
    def unsubscribe(self, topic):
        print(f"{self.client_id} subscribing to {topic}")
        self.client.unsubscribe(topic)

    def removeSubscribedTopic(self, topic):
        for x in self.subscribedTopicsList:
            if x.topic == topic:
                subscribedTopicsList.remove(x)
                break

    def addSubscribedTopic(self, topic):
        if (any(x for x in self.subscribedTopicsList if x.topic == topic)):
            print(f"Already subscribed to {topic}")
        else:
            newSubscribedTopic = SubscribedTopic(topic)
            self.subscribedTopicsList.append(newSubscribedTopic)
    
    def addPayload(self, topic, payload):
        for x in self.subscribedTopicsList:
            if x.topic == topic:
                x.payload = payload
                break

    def findTopicFromList(self, topic):
        for x in self.subscribedTopicsList:
            if x.topic == topic:
                return x
        return False
        

class SubscribedTopic:
    def __init__(self, topic):
        self.topic = topic
        self.payload = None




        
