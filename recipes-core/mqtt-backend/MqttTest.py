import mqttClient as mqtt

testClient = mqtt.MqttClient("client_id/", "topic/", "payload")

testClient.start_loop('localhost', 1883, 60)

while True:
    try:
        testClient.payloadPublish = input()
        testClient.publish(1)
    except KeyboardInterrupt: # exits on ^C 
        break
testClient.end_loop()