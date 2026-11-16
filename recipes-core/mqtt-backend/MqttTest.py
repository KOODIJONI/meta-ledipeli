import mqttClient as mqtt

publisher = mqtt.MqttPublisher("TestClient/", "newTopic/", "payload")
listener = mqtt.MqttListener(publisher.client_id, "newTopic/score")

publisher.start_loop('localhost', 1883, 60)
listener.start_loop('localhost', 1883, 60)

while True:
    try:
        print(f"Listener payload: {listener.payload}")
        publisher.payload = input()
        publisher.publish(publisher.get_topic() + "subTopic" ,1)
    except KeyboardInterrupt: # exits on ^C 
        break
publisher.end_loop()
listener.end_loop()