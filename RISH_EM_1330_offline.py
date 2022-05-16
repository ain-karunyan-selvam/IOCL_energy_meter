#!/usr/bin/env python3

import time
import minimalmodbus
import logging
from logging.handlers import RotatingFileHandler
import paho.mqtt.client as mqtt
import json
import os
import datetime
#import threading
import sqlite3
import sys

with open('/home/pi/ioclt/config.json', 'r') as configFile:
	CONFIG = json.load(configFile)
configFile.close()

username_mqtt = CONFIG['MQTT']['USERNAME']
password_mqtt = CONFIG['MQTT']['PASSWORD']
Publish_Topic = CONFIG['MQTT']['TOPIC_PREFIX']
mqtt_port =  CONFIG['MQTT']['PORT']
mqtt_broker = CONFIG['MQTT']['HOST']
mqtt_qos = CONFIG['MQTT']['QOS']

file_path = CONFIG['DATABASE']['FILEPATH']
table_name = CONFIG['DATABASE']['TABLENAME']


rs485 = minimalmodbus.Instrument(CONFIG['MODBUS']['ENERGYMETER']['PORT'],CONFIG['MODBUS']['ENERGYMETER']['SLAVE'])
rs485.serial.baudrate = CONFIG['MODBUS']['ENERGYMETER']['BAUDRATE']
rs485.serial.bytesize = CONFIG['MODBUS']['ENERGYMETER']['BYTESIZE']
rs485.serial.parity = minimalmodbus.serial.PARITY_NONE
rs485.serial.stopbits = CONFIG['MODBUS']['ENERGYMETER']['STOPBITS']
rs485.serial.timeout = CONFIG['MODBUS']['ENERGYMETER']['TIMEOUT']
rs485.debug = CONFIG['MODBUS']['ENERGYMETER']['DEBUG']
rs485.mode = minimalmodbus.MODE_RTU

parameters = CONFIG['MODBUS']['REGISTERS']['PARAMETERS']
address = CONFIG['MODBUS']['REGISTERS']['ADDRESS']
sperate_parameters = CONFIG['MODBUS']['REGISTERS']['SPERATE_PARAMETERS']

counter = 0

if len(parameters) == len(address):
    pass
else : 
    exit()

Datapackage = {}

try :
	os.system('mkdir -p {}'.format(CONFIG['LOGS']['IOCLT']))
except Exception as e:
    logging.error(e)
    pass

log_path = CONFIG['LOGS']['IOCLT'] + "energymeter.log"

logging.basicConfig(handlers=[RotatingFileHandler(log_path, maxBytes=CONFIG['LOG_ROTATE']['MAXBYTES'], backupCount=CONFIG['RETENTIONS']['EM'])],level=logging.DEBUG,format='%(asctime)s %(levelname)s - %(name)s.%(funcName)s - %(message)s',datefmt='%Y-%m-%d %H:%M:%S')





class rs485_em_data():
    def __init__(self, parameters, address):
        self.parameters = parameters
        self.address = address

    def rish1330_data(self):
        try:
            Datapackage = {}
            Datapackage["ts"] = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
            for indx,A in enumerate(address):
                Val = rs485.read_float(A, functioncode=4, number_of_registers=2)
                Datapackage[parameters[indx]] = float(str(f'{Val :.3f}'))
                time.sleep(.1)
            logging.info("Datapackage- {}".format(Datapackage))
            return Datapackage
        except Exception as e:
            logging.error(e)
            sys.exit()
            return e


class mqqt_connect():
    def __init__(self,username_mqtt,password_mqtt,mqtt_broker,mqtt_port,Publish_Topic,mqtt_qos):
        self.username_mqtt =username_mqtt
        self.password_mqtt =password_mqtt
        self.Publish_Topic=Publish_Topic
        self.mqtt_port=mqtt_port
        self.mqtt_broker=mqtt_broker
        self.mqtt_qos=mqtt_qos

    def MQTT_Connect(self):
        try :    
            client = mqtt.Client()
            client.username_pw_set(self.username_mqtt,password=self.password_mqtt)
            client.connect(host=self.mqtt_broker, port=self.mqtt_port)
            return True,client
        except Exception as e:
            return False,e

    def Publish_Data(self,client,Message):
        try: 
            client.publish(self.Publish_Topic,Message,self.mqtt_qos)
            return True,None
        except Exception as sd:
            return False,sd 

class database():
    def __init__(self,database_path,table_name):
        self.database_path = database_path
        self.table_name = table_name

    def connection(self):
        try : 
            conn = sqlite3.connect(self.database_path)
            c = conn.cursor()
            try :
                c.execute("CREATE TABLE" + " " + self.table_name + " " + "(data json)")
                os.system("sudo chmod 664 {}".format(self.database_path))
                logging.info("table created")
                
            except Exception as e:
                logging.error("table {}".format(e))
                pass
            return c,conn
        except Exception as e:
            logging.error("database error {}".format(e))
            return False,e

    def insert_value(self,currsor,connection,EM_data):
        try :
            currsor.execute('''insert into''' + ''' ''' + self.table_name + ''' ''' + ''' values(?)''', (json.dumps(EM_data),))
            connection.commit()
            return True
        except Exception as e:
            logging.error("insert_value error {}".format(e))
            return e

    def delete_all_tasks(self,currsor,conn):
        try:
            currsor.execute('DELETE FROM {}'.format(self.table_name))
            conn.commit()
            return True
        except Exception as e:
            logging.error("delete_all_tasks error {}".format(e))
            return e

    def offline_data_publish(self,currsor):
        try: 
            currsor.execute('select * from {}'.format(self.table_name))
            data = currsor.fetchall()
            #conn.close()
            if data == []:
                return None
            else :
                return data     
        except Exception as e:
            logging.error("offline_data_publish error {}".format(e))
            return None
        
def check_db_size(file_path):
    file_size = os.stat(file_path)
    if(CONFIG['RETENTIONS']['DB_SIZE'] <= file_size/1000):
         os.remove(file_path)
         logging.info('DB file restarted {}'.format(file_size))
         os.system('sudo systemctl restart ioclt.service')
         logging.info('service restarted')



    
def main_function():
    global counter
    try :
        flag = 0
        val = rs485_em_data(parameters,address)
        EM = val.rish1330_data()
        mqtt_parameters = {}
        client = {}
        Datapackage = {}
        for i in range(len(Publish_Topic)):
            mqtt_parameters[i] = mqqt_connect(username_mqtt,password_mqtt,mqtt_broker,mqtt_port,Publish_Topic[i],mqtt_qos)
            flag, client[i] = mqtt_parameters[i].MQTT_Connect()
            logging.info("client message- {} ".format(flag))
        if flag == True:
            #EM["type"] = "live"
            logging.info("client message-11")
            client_id = 0
            for i in range(1,4):
                indx = i
                #val_dic = EM.values()
                #value_list = list(val_dic)
                Datapackage["ts"] = list(EM.values())[0]
                for j in range(len(sperate_parameters)):
                    #val_dic = EM.values()
                    #value_list = list(val_dic)
                    #Datapackage[sperate_parameters[j]] = value_list[indx]
                    Datapackage[sperate_parameters[j]] = list(EM.values())[indx]
                    indx = indx + 3
                #Datapackage["type"] = "live"
                logging.info("sperate data {}".format(Datapackage))
                pub_message = mqtt_parameters[client_id].Publish_Data(client[client_id],json.dumps(Datapackage).encode())
                #pub_message = mqtt_parameters.Publish_Data(client[client_id],json.dumps(Datapackage))
                logging.info("publish message- {}".format(pub_message))
                offline_data = offline.offline_data_publish(cursur)
                logging.info("offline_data {}".format(offline_data))
                client_id = client_id + 1
                Datapackage = {}
            if offline_data != None:
                length = len(offline_data)
                if length != counter : 
                    val = "[]()'".join(offline_data[counter])
                    for i in range(1,4):
                        indx = i
                        #val_dic = val.values()
                        #value_list = list(val_dic)
                        Datapackage["ts"] = list(val.values())[0]
                        for j in range(len(sperate_parameters)):
                            #val_dic = EM.values()
                            #value_list = list(val_dic)
                            Datapackage[sperate_parameters[j]] = list(val.values())[indx]
                            indx = indx + 3
                        #Datapackage["type"] = "log"
                        pub_message = mqtt_parameters[client_id].Publish_Data(client[client_id],Datapackage)
                        logging.info("publish offline message- {} {} {}".format(pub_message,counter,length))
                        counter = counter + 1
                        client_id = client_id + 1
                else :
                    logging.info("delete message {}".format(offline.delete_all_tasks(cursur,conn)))
                    #conn.close()
                    counter = 0
            for i in range(len(Publish_Topic)):
                client[i].disconnect()
        else :
            EM["type"] = "log"
            #data = offline.insert_value(cursur,conn,EM)
            logging.info("offline message- {}".format(data))
            #conn.close()
            
    except Exception as e:
        logging.error(e)
        #cursur,conn = offline.connection()
        pass


if __name__ == "__main__":
    offline = database(file_path,table_name)
    cursur,conn = offline.connection()
    while 1:
        main_function()
        time.sleep(CONFIG['RETENTIONS']['DURATION'])
        #check_db_size(file_path)




      












        