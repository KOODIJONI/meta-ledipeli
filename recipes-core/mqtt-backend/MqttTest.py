import mqttClient as mqtt

#Example on how to use the custom mqttClient classes

publisher = mqtt.MqttPublisher("Publisher", "instance/testGame/score", "payload")
listener = mqtt.MqttSubscriber("Listener", publisher.topic)

publisher.start_loop('localhost', 1883, 60)
listener.start_loop('localhost', 1883, 60)
listener.subscribe("instance/testGame/highscore")

while True:
    try:
        publisher.payload = input()
        publisher.publish(publisher.topic, publisher.payload, qos = 1)
        publisher.publish("instance/testGame/highscore", "test " + publisher.payload, qos = 1)
        print(f"Listeners {listener.subscribedTopicsList}")
        print(f"Listener payload: {listener.findTopicFromList("instance/testGame/highscore").payload}")
    except KeyboardInterrupt: # exits on ^C
        break
publisher.end_loop()
listener.end_loop()