import paho.mqtt.client as mqtt

DEFAULT_BROKER_ADDRESS = "broker.hivemq.com"
DEFAULT_MQTT_PORT = 1883


class MQTTClient:

    def __init__(self, broker_address: str = DEFAULT_BROKER_ADDRESS, broker_port: int = DEFAULT_MQTT_PORT, on_connect_callback=None):
        """
        :param broker_address: broker address
        :param broker_port: broker port
        :param on_connect_callback: listener when client is connected
        """
        super().__init__()
        self.broker_address = broker_address
        self.broker_port = broker_port
        self._subscriber_callback = None
        self._on_connect_callback = on_connect_callback

        self.client = mqtt.Client()
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message

    # ----------------------------------------------------------------------------------------
    # Setup
    # ----------------------------------------------------------------------------------------

    def connect_safe(self, username, password):
        print(f"Connecting with {self.broker_address}:{self.broker_port}....")
        self.client.username_pw_set(username, password)
        self.client.connect(self.broker_address, self.broker_port, 60)

    def connect(self):
        print(f"Connecting with {self.broker_address}:{self.broker_port}....")
        self.client.connect(self.broker_address, self.broker_port, 60)

    def disconnect(self):
        print(f"Disconnecting with {self.broker_address}:{self.broker_port}....")
        self.client.disconnect()

    # ----------------------------------------------------------------------------------------
    # Internal Methods
    # ----------------------------------------------------------------------------------------

    def _on_message(self, current_client: mqtt.Client, userdata, msg):
        _response = msg.payload.decode('utf-8')
        self._subscriber_callback(msg.topic, _response)

    def _on_connect(self, current_client: mqtt.Client, userdata, flags, rc):
        if rc == 0:
            print("MQTT client is on....")
            self._on_connect_callback()
        else:
            print(f"Failed to connect, return code: {rc}")

    # ----------------------------------------------------------------------------------------
    # Public Methods
    # ----------------------------------------------------------------------------------------

    def publish(self, topic, data) -> bool:
        result = self.client.publish(topic, data)
        status = result[0]
        if status == 0:
            return True
        else:
            print(f"Failed to send message to topic {topic}")
            return False

    def subscribe(self, topic: str, subscriber_callback):
        """
        :param topic:
        :param subscriber_callback: listener when receiving a message mqtt
        :example: def _subscriber_callback(topic: str, response: str)
        """
        print(f"Subscribe topic: {topic}")
        self._subscriber_callback = subscriber_callback
        self.client.subscribe(topic)

    def unsubscribe(self, topic: str):
        self.client.unsubscribe(topic)

    # ----------------------------------------------------------------------------------------
    # Lifecycle
    # ----------------------------------------------------------------------------------------

    def loop_forever(self):
        try:
            self.client.loop_forever()
        except KeyboardInterrupt:
            self.disconnect()

    def loop_start(self):
        try:
            self.client.loop_start()
        except KeyboardInterrupt:
            self.disconnect()

    def loop_stop(self):
        try:
            self.client.loop_stop()
        except KeyboardInterrupt:
            self.disconnect()
