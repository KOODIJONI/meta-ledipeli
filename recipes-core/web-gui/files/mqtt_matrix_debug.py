import json
import time

import paho.mqtt.client as mqtt

BROKER_HOST = "localhost"
BROKER_PORT = 1883

MATRIX_SIZE_TOPIC = "device/matrix/size"
CAMERA_SIZE_TOPIC = "device/camera/size"
MATRIX_DATA_TOPIC = "device/matrix/data"
MOUSE_TOPIC = "device/mouse"


def on_connect(client, userdata, flags, rc):
    print(f"Connected to MQTT broker with code {rc}")
    client.subscribe(MOUSE_TOPIC)


def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode("utf-8"))
    except Exception:
        payload = msg.payload.decode("utf-8", errors="replace")

    print(f"Received on {msg.topic}: {payload}")


def build_grb_blob(width, height):
    blob = bytearray()
    for y in range(height):
        for x in range(width):
            if (x + y) % 2 == 0:
                g = 255
                r = 0
                b = 0
            else:
                g = 0
                r = 0
                b = 255
            blob.extend([g, r, b])
    return bytes(blob)


def publish_matrix_data(client):
    matrix_size = {"width": 48, "height": 48}
    camera_size = {"width": 640, "height": 480}
    matrix_blob = build_grb_blob(matrix_size["width"], matrix_size["height"])

    client.publish(MATRIX_SIZE_TOPIC, json.dumps(matrix_size), qos=0)
    client.publish(CAMERA_SIZE_TOPIC, json.dumps(camera_size), qos=0)
    client.publish(MATRIX_DATA_TOPIC, matrix_blob, qos=0)
    print(f"Published matrix size: {matrix_size}")
    print(f"Published camera size: {camera_size}")
    print(f"Published binary GRB blob ({len(matrix_blob)} bytes)")


def main():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    try:
        client.connect(BROKER_HOST, BROKER_PORT, 60)
        client.loop_start()

        time.sleep(1)
        publish_matrix_data(client)

        print("Listening for mouse coordinates... Press Ctrl+C to stop.")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopping debug listener")
    finally:
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()
