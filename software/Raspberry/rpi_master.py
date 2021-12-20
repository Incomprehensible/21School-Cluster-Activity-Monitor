import sqlite3
from smbus2 import SMBus, i2c_msg
from configparser import ConfigParser
import time
#import Adafruit_ADS1x15
import ADS1x15
from rpi_DB import Status, ClusterDB
from STM32 import STM32_addr, STM32_leds, STM32_rooms
from Grafana import Grafana

C_MODE = 1

config = ConfigParser()
config.read('config.ini')
BRIGHT = float(config.get('settings', 'BRIGHT')) # Volt
DARK = float(config.get('settings', 'DARK')) # Volt
MAX_LUX = float(config.get('settings', 'MAX_LUX'))
MIN_LUX = float(config.get('settings', 'MIN_LUX'))
POWER_FACTOR = (MAX_LUX - MIN_LUX)/(BRIGHT - DARK)

ADC_PIN = int(config.get('settings', 'ADC_PIN')) # GPIO4 on Rpi
CLUSTERS_NUM = int(config.get('settings', 'CLUSTERS_NUM'))
COMMAND_SET_BRIGHTNESS = int(config.get('settings', 'COMMAND_SET_BRIGHTNESS'))
COMMAND_SET_COLORS = int(config.get('settings', 'COMMAND_SET_COLORS'))
COMMAND_SET_MATRIX = int(config.get('settings', 'COMMAND_SET_MATRIX'))
COLOR_FREE = int(config.get('settings', 'COLOR_FREE'))
COLOR_USED = int(config.get('settings', 'COLOR_USED'))
COLOR_COVID = int(config.get('settings', 'COLOR_COVID'))
COLOR_EXAM = int(config.get('settings', 'COLOR_EXAM'))
COLOR_HERE = int(config.get('settings', 'COLOR_HERE'))

COMMAND_SET_C_COLORS = int(config.get('settings', 'COMMAND_SET_C_COLORS'))
COMMAND_SET_C_MATRIX = int(config.get('settings', 'COMMAND_SET_C_MATRIX'))
COLOR_EMP = int(config.get('settings', 'COLOR_EMP'))
COLOR_ALP = int(config.get('settings', 'COLOR_ALP'))
COLOR_CAP = int(config.get('settings', 'COLOR_CAP'))
COLOR_SAL = int(config.get('settings', 'COLOR_SAL'))
COLOR_MED = int(config.get('settings', 'COLOR_MED'))

class STM32:
    def __init__(self, addr, name, leds, rooms) -> None:
        self.address = addr
        self.name = name
        self.leds_num = leds
        self.rooms_num = rooms
    def addr(self):
        return self.address
    def name(self):
        return self.name
    def leds(self):
        return self.leds_num
    def rooms(self):
        return self.rooms_num

class ADC:
    def __init__(self, pin) -> None:
        self.adc = ADS1x15.ADS1115()
        self.GAIN = 1
        self.pin = pin
    def read_pin(self, pin):
        return self.adc.read_adc(pin, gain=self.GAIN)
    def adc_test(self):
    # Read all the ADC channel values in a list.
        values = [0]*4
        for i in range(4):
        # Read the specified ADC channel using the previously set gain value.
            values[i] = self.read_pin(i)
        # Note you can also pass in an optional data_rate parameter that controls
        # the ADC conversion time (in samples/second). Each chip has a different
        # set of allowed data rate values, see datasheet Table 9 config register
        # DR bit values.
        #values[i] = adc.read_adc(i, gain=GAIN, data_rate=128)
        # Each value will be a 12 or 16 bit signed integer value depending on the
        # ADC (ADS1015 = 12-bit, ADS1115 = 16-bit).
    # Print the ADC values.
            print('| {0:>6} | {1:>6} | {2:>6} | {3:>6} |'.format(*values))
    # Pause for half a second.
            time.sleep(0.5)

class Master:
    def __init__(self, num_of_clusters) -> None:
        self.adc = ADC(ADC_PIN)
        self.bus = SMBus(1)
        self.stm32 = [None]*num_of_clusters
        self.db = ClusterDB()
        self.grafana = Grafana(self.db)
        self.clusters = ['oasis', 'illusion', 'mirage', 'atlantis', 'atrium']
        self.num_of_clusters = num_of_clusters
    def init_slaves(self):
        # init all STM32
        for stm32 in range(0, self.num_of_clusters):
            cluster_name = self.clusters[stm32]
            i2c_addr = STM32_addr.get(cluster_name)
            leds = STM32_leds.get(cluster_name)
            rooms = STM32_rooms.get(cluster_name)
            self.stm32[stm32] = STM32(i2c_addr, cluster_name, leds, rooms)
    def init_colors(self):
        for cluster in self.clusters:
            print(cluster)
            if (C_MODE):
                self.construct_packet(cluster, COMMAND_SET_C_COLORS)
            else:
                self.construct_packet(cluster, COMMAND_SET_COLORS)

    def monitor_clusters(self):
        # parse metrics data for each cluster
        # ask bd if any changes per mac (try to change status)
        # based on return value construct msg to stm, at the end update stm32
        if (C_MODE):
            self.grafana.get_metrics_c_mode() # grafana class updates bd
        else:
            self.grafana.get_metrics()
        for cluster in self.clusters:
            # get number of leds in cluster
            # get value by led id
            print(cluster)
            self.construct_packet(cluster, COMMAND_SET_BRIGHTNESS)
            print('sent brightness')
            if cluster == 'atrium':
                continue
            time.sleep(0.1)
            self.construct_packet(cluster, COMMAND_SET_MATRIX)
            print('sent matrix')
    def update_bd(self):
        pass

    def construct_packet(self, cluster, cmd):
        if (C_MODE):
            construct_packet_c_mode(cluster, cmd)
        else:
            stm32 = self.clusters.index(cluster)
            leds = self.stm32[stm32].leds()
            rooms = self.stm32[stm32].rooms()
            i2c_array = [0] * (1 + leds + rooms)
            if cmd == COMMAND_SET_MATRIX:
                #i2c_array = [None] * (6 + leds)
                i2c_array[0] = int(COMMAND_SET_MATRIX)
                #i2c_array[0] = int(Status.FREE)
                #i2c_array[1] = int(Status.USED)
                #i2c_array[2] = int(Status.COVID)
                #i2c_array[3] = int(Status.EXAM)
                #i2c_array[4] = 0 # WTF
                #i2c_array[5] = self.getBrightnessLevel()
                self.fill_cluster_array(cluster, i2c_array, leds, rooms)
            elif cmd == COMMAND_SET_BRIGHTNESS:
                i2c_array[0] = int(COMMAND_SET_BRIGHTNESS)
                i2c_array[1] = int(self.get_brightness())
                print(i2c_array)
            elif cmd == COMMAND_SET_COLORS:
                i2c_array[0] = int(COMMAND_SET_COLORS)
                i2c_array[1] = (COLOR_FREE & 0xff0000) >> 16
                i2c_array[2] = (COLOR_FREE & 0x00ff00) >> 8
                i2c_array[3] = (COLOR_FREE & 0x0000ff)
                i2c_array[4] = (COLOR_USED & 0xff0000) >> 16
                i2c_array[5] = (COLOR_USED & 0x00ff00) >> 8
                i2c_array[6] = (COLOR_USED & 0x0000ff)
                i2c_array[7] = (COLOR_COVID & 0xff0000) >> 16
                i2c_array[8] = (COLOR_COVID & 0x00ff00) >> 8
                i2c_array[9] = (COLOR_COVID & 0x0000ff)
                i2c_array[10] = (COLOR_EXAM & 0xff0000) >> 16
                i2c_array[11] = (COLOR_EXAM & 0x00ff00) >> 8
                i2c_array[12] = (COLOR_EXAM & 0x0000ff)
                i2c_array[13] = (COLOR_HERE & 0xff0000) >> 16
                i2c_array[14] = (COLOR_HERE & 0x00ff00) >> 8
                i2c_array[15] = (COLOR_HERE & 0x0000ff)
                print(i2c_array)
            elif cmd == COMMAND_SET_C_COLORS:
                i2c_array[0] = int(COMMAND_SET_COLORS)
                i2c_array[1] = (COLOR_EMP & 0xff0000) >> 16
                i2c_array[2] = (COLOR_EMP & 0x00ff00) >> 8
                i2c_array[3] = (COLOR_EMP & 0x0000ff)
                i2c_array[4] = (COLOR_ALP & 0xff0000) >> 16
                i2c_array[5] = (COLOR_ALP & 0x00ff00) >> 8
                i2c_array[6] = (COLOR_ALP & 0x0000ff)
                i2c_array[7] = (COLOR_CAP & 0xff0000) >> 16
                i2c_array[8] = (COLOR_CAP & 0x00ff00) >> 8
                i2c_array[9] = (COLOR_CAP & 0x0000ff)
                i2c_array[10] = (COLOR_SAL & 0xff0000) >> 16
                i2c_array[11] = (COLOR_SAL & 0x00ff00) >> 8
                i2c_array[12] = (COLOR_SAL & 0x0000ff)
                i2c_array[13] = (COLOR_MED & 0xff0000) >> 16
                i2c_array[14] = (COLOR_MED & 0x00ff00) >> 8
                i2c_array[15] = (COLOR_MED & 0x0000ff)
                print(i2c_array)
            stm32_addr = self.stm32[stm32].addr()
            try:
                self.send_packet(stm32_addr, i2c_array)
            except:
                print("error sending packet!!!")
                pass
    def send_packet(self, addr, data):
        msg = i2c_msg.write(addr, data)
        self.bus.i2c_rdwr(msg)
        #data = data[32:]
        #if len(data) > 0:
        #    self.bus.write_i2c_block_data(addr, 0, data)
    def fill_cluster_array(self, cluster, data, leds, rooms):
        # import data from db one by one
        for room in range(0, rooms):
            data[1+room] = 0
        for led in range(0, leds):
            data[1+rooms+led] = self.db.fetch_cluster_led_status(cluster, led)
            if not data[1+rooms+led]:
                data[1+rooms+led] = int(Status.COVID)
            #data[6+led] = self.db.fetch_cluster_led_status(cluster, led)
        print(data)
        print(len(data))
        # cluster_data = []
        # cluster_status = self.db.fetch_cluster_led_status(cluster, 3)
        # cluster_data = self.db.fetch_cluster_data(cluster, cluster_data)
        # print(cluster_status)
        # print(cluster_data)
        # self.db.change_mac_status(cluster, 'b2', 3)
        # cluster_status = self.db.fetch_cluster_led_status(cluster, 6)
        # print(cluster_status)

    def writeByte(self, address, value):
        self.bus.write_byte(address, value)
    def readByte(self, address):
        return self.bus.read_byte(address)
    def get_brightness(self):
        volt = self.adc.read_pin(self.adc.pin)
        lvl = volt * POWER_FACTOR
        return lvl
    # def setBrightness(self, lvl, address):
    #     # implement protocol here
    #     self.writeByte(address, lvl)
    # def setBrightnessAll(self):
    #     lux = self.get_brightness()
    #     for stm in self.stm32:
    #         self.setBrightness(stm.address, lux)




if __name__ == '__main__':
    rpi = Master(CLUSTERS_NUM)
    rpi.init_slaves()
    rpi.init_colors()
    while True:
        try:
            rpi.monitor_clusters()
            time.sleep(0.5)
        except:
            pass

