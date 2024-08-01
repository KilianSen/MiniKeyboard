package main

import (
	"context"
	"fmt"
	"github.com/sethvargo/go-envconfig"
	"gopkg.in/yaml.v3"
	"log"
	"os"
	"os/exec"
	"strconv"
	"time"

	MQTT "github.com/eclipse/paho.mqtt.golang"
)

var (
	lastKey  int
	lastTime time.Time
)

type Config struct {
	MQTT struct {
		Protocol string `yaml:"protocol" env:"MQTT_PROTOCOL, default=tcp"`
		Host     string `yaml:"host" env:"MQTT_HOST, default=localhost"`
		Port     int    `yaml:"port" env:"MQTT_PORT, default=1883"`
		Topic    string `yaml:"topic" env:"MQTT_TOPIC, default=mmkb/mmkb"`
		Auth     struct {
			Username string `yaml:"username" env:"MQTT_USERNAME, default="`
			Password string `yaml:"password" env:"MQTT_PASSWORD, default="`
			ClientID string `yaml:"clientid" env:"MQTT_CLIENTID, default=mmkb"`
		} `yaml:"auth"`
	} `yaml:"mqtt"`
	Handler struct {
		Exec   string `yaml:"exec" env:"HANDLER_PATH, default=py"`
		Script string `yaml:"script" env:"HANDLER_SCRIPT, default=./mmkb.py"`
	} `yaml:"handler"`

	Restart int `yaml:"restart" env:"RESTART, default=25"`
}

var config Config
var client MQTT.Client

type LogWriter struct {
}

func (w LogWriter) Write(p []byte) (n int, err error) {
	log.Printf("[mmkb] %s", p)
	return len(p), nil
}

func execHandler(keyIndex int, pressTime float64) {
	// Execute the handler with the key index and press time as arguments

	cmd := exec.Command(config.Handler.Exec, config.Handler.Script, strconv.Itoa(keyIndex), fmt.Sprintf("%f", pressTime))
	// Get stdout and stderr and use log (error) if needed

	// create a custom io.Writer that logs the output with a timestamp
	cmd.Stdout = LogWriter{}
	cmd.Stderr = cmd.Stdout

	err := cmd.Run()

	if err != nil {
		log.Printf("[mmkb] Error executing handler: %v", err)
		return
	}
}

func onMessage(_ MQTT.Client, msg MQTT.Message) {
	key, err := strconv.Atoi(string(msg.Payload()))
	if err != nil {
		log.Printf("[mmkb] Invalid key received: %v", err)
		return
	}

	if key == -1 {
		execHandler(lastKey, time.Since(lastTime).Seconds())
	} else {
		lastKey = key
		lastTime = time.Now()

		log.Printf("[mmkb] Key pressed %d, waiting for release to run or timeout", key)
	}
}

func onConnect(client MQTT.Client) {
	reader := client.OptionsReader()
	log.Println("[mmkb] Connected with client ID:", reader.ClientID())
}

func loadConfig(filename string) {
	data, err := os.ReadFile(filename)
	if err != nil {
		log.Fatalf("[mmkb] Error reading config file: %v", err)
	}
	if err := yaml.Unmarshal(data, &config); err != nil {
		log.Fatalf("[mmkb] Error unmarshalling config: %v", err)
	}
}

func readEnv() {
	if err := envconfig.Process(context.Background(), &config); err != nil {
		log.Fatal(err)
	}
}

func Service() {
	// if config file exists, load it
	if _, err := os.Stat("config.yaml"); err == nil {
		loadConfig("config.yaml")
	}
	readEnv()

	opts := MQTT.NewClientOptions().AddBroker(fmt.Sprintf("%s://%s:%d", config.MQTT.Protocol, config.MQTT.Host, config.MQTT.Port))
	opts.SetClientID(config.MQTT.Auth.ClientID)
	opts.SetUsername(config.MQTT.Auth.Username)
	opts.SetPassword(config.MQTT.Auth.Password)

	opts.OnConnect = func(client MQTT.Client) {
		onConnect(client)
	}

	opts.OnConnectionLost = func(client MQTT.Client, err error) {
		log.Printf("[MQTT] Connection lost: %v", err)
	}

	client = MQTT.NewClient(opts)
	if token := client.Connect(); token.Wait() && token.Error() != nil {
		log.Fatalf("[MQTT] Error connecting: %v", token.Error())
	}

	client.Subscribe(config.MQTT.Topic, 1, onMessage)
}

func main() {

	for {
		Service()
		time.Sleep(time.Duration(config.Restart) * time.Second)
		client.Unsubscribe(config.MQTT.Topic)
		client.Disconnect(250)
	}
}
