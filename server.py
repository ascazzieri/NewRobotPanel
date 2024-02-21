import argparse
import socket
import struct
import time
from threading import Thread, Event
from queue import Queue
from data import Data
from serverGUI import ConnectionPanel
from logger import Logger
from utils import is_number_regex
#from fanucpy import Robot
# Universal Robot imports
import rtde.rtde as rtde
import rtde.rtde_config as rtde_config
import math

class ConnectionManager:
    connList = []
    panel = None

    def __init__(self, firstTabTitle) -> None:
        # init queue for passing data between thread
        self.queue = Queue() 

        # init first connection
        conn = RobotConnection(firstTabTitle, len(self.connList), self.queue)
        # store connection
        self.connList.append(conn)

        # init connection manager panel 
        self.panel = ConnectionPanel(firstTabTitle, conn.onStart, conn.onStop, self.onNewConnection, self.isConnectionRunning, self.setTestData, self.queue, args.iodebug)

        # show and run GUI
        self.panel.run(self.onClosing)

    def onNewConnection(self, title):
        # create new connection
        conn = RobotConnection(title, len(self.connList), self.queue)
        # store connection
        self.connList.append(conn)

        return [conn.onStart, conn.onStop]
    
    def isConnectionRunning(self, index):
        return self.connList[index].isRunning

    def setTestData(self, index, data):
        conn = self.connList[index]
        if conn.data.IS_DEBUG:
            for i, val in enumerate(data):
                conn.j_data[i] = val

    def onClosing(self):
        isClosed = self.panel.end()

        if isClosed:
            self.stopAll()

    def stopAll(self):
        for c in self.connList:
            c.killConnection()

class RobotConnection:
    # UDP server thread
    udpServerThread = None
    # TCP server thread
    tcpServerThread = None

    # UDP connection socket
    UDPServerSocket = None
    # TCP connection socket
    TCPServerSocket = None

    # count packets number
    udpPacketsReceived = 0
    udpPacketsSent = 0
    tcpPacketsReceived = 0
    tcpPacketsSent = 0

    isRunning = False

    def __init__(self, title, id, queue) -> None:
        # init default data for panel
        self.data = Data()
        # setup basic info
        self.title = title
        self.id = id
        # store update callback
        self.queue = queue
        # init event to stop threads
        self.stop_threads = Event()

    def killConnection(self):
        if self.TCPServerSocket == None:
            return
        
        if self.data.ROBOT_TYPE == 1:
            # kill threads
            self.stop_threads.set()
            
            if hasattr(self, "rtdeConn"):
                self.rtdeConn.send_pause()
                self.rtdeConn.disconnect()
        else:
            if self.UDPServerSocket == None:
                return
            
            # kill threads
            self.stop_threads.set()
            # close socket to prevent UDP recvfrom from hanging
            self.UDPServerSocket.close()

        # close socket to prevent TCP recvfrom from hanging
        self.TCPServerSocket.close()

        if self.udpServerThread == None or self.tcpServerThread == None:
            return

        # wait until thread ends
        self.udpServerThread.join()
        self.tcpServerThread.join()
        self.udpServerThread = None
        self.tcpServerThread = None

        self.isRunning = False


    def onStart(self, robotType, udpHostEntry, udpPortEntry, tcpHostEntry, tcpPortEntry, j_count, ao_count, ai_count, do_count, di_count, isSimulate, isActive):
        # get modified values
        self.data.ROBOT_TYPE = robotType
        self.data.UDP_HOST = udpHostEntry
        self.data.UDP_PORT = int(udpPortEntry)
        self.data.TCP_HOST = tcpHostEntry
        self.data.TCP_PORT = int(tcpPortEntry)
        self.data.J_COUNT = int(j_count)
        self.data.AO_COUNT = int(ao_count)
        self.data.AI_COUNT = int(ai_count)
        self.data.DO_COUNT = int(do_count)
        self.data.DI_COUNT = int(di_count)
        self.data.IS_DEBUG = True if isSimulate == 1 else False
        self.data.IS_ACTIVE = True if isActive == 1 else False

        if not self.data.IS_ACTIVE:
            return False
        try:
            # check IP validity for UDP connection
            socket.inet_aton(self.data.UDP_HOST)
        except socket.error as err:
            logger.log("Error: [UDP_HOST] " + str(err))
            return False

        try:
            # check IP validity for TCP connection
            socket.inet_aton(self.data.TCP_HOST)
        except socket.error as err:
            logger.log("Error: [TCP_HOST] " + str(err))
            return False

        # init data exchange variable
        self.j_data = [0.0] * self.data.J_COUNT
        self.ao_data = [0.0] * self.data.AO_COUNT
        self.ai_data = [0.0] * self.data.AI_COUNT
        self.do_data = [0.0] * self.data.DO_COUNT
        self.di_data = [0.0] * self.data.DI_COUNT
        
        # reset some data
        self.stop_threads.clear()
        self.tcpPacketsReceived = 0
        self.tcpPacketsSent = 0
        self.udpPacketsReceived = 0
        self.udpPacketsSent = 0
        if not self.data.IS_DEBUG:
            if robotType == 1:
                # RTDE configuration
                conf = rtde_config.ConfigFile(self.data.DEFAULT_RTDE_CONFIG_FILE)
                self.outNames, self.outTypes = conf.get_recipe('out')
            elif robotType == 2:
                #FANUC configuration
                pass
            elif robotType == 3:
                #FANUC configuration
                pass

            else:
                # Create a datagram socket for UDP connection
                print(self.data.UDP_HOST, self.data.UDP_PORT)
                self.UDPServerSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
                # Bind to address and ip
                self.UDPServerSocket.bind((self.data.UDP_HOST, self.data.UDP_PORT))
                logger.log("[UDP server - " + self.title +"] up and listening ...")

        # Create a socket for TCP connection
        self.TCPServerSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM) 

        # make the address reusable (can start the server again if you shut it down,
        # instead of waiting for a minute for TIME_WAIT status to finish with your server port)
        self.TCPServerSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) 
        self.TCPServerSocket.bind((self.data.TCP_HOST, self.data.TCP_PORT))
        self.TCPServerSocket.listen()
        logger.log("[TCP server - " + self.title +"] up and listening ...")

        # setup both sockets using thread
        if not self.data.IS_DEBUG:
            self.udpServerThread = Thread(target=(self.RTDEClient if robotType==1 else self.UDPServer), args=(self.queue, ))
        self.tcpServerThread = Thread(target=self.TCPServer, args=(self.queue, ))
        # start threads
        self.tcpServerThread.start()
        if not self.data.IS_DEBUG:
            self.udpServerThread.start()

        self.isRunning = True

        return True
    
    def onStop(self):
        self.killConnection()
        return True

    def getIsRunning(self):
        return self.isRunning

    def UDPServer(self, queue):               
        while not self.stop_threads.is_set():
            try:
                bytesAddressPair = self.UDPServerSocket.recvfrom(self.data.UDP_PACKET_SIZE)
                self.udpPacketsReceived += 1
                # add update to queue
                queue.put([self.id, {'pktsRecv-udp': self.udpPacketsReceived}])
            except socket.error as err:
                logger.log("UDP err: " + str(err))
                break

            msg = bytesAddressPair[0]
            addr = bytesAddressPair[1]


            ##########################
            ######   RECEIVE    ######
            ######  py -> robot ######
            ##########################  
            # getting data from message: axis positions, spare analog outputs, spare digital outputs 
            dataCount = self.data.J_COUNT + self.data.AO_COUNT + self.data.DO_COUNT
            start = 0
            for i in range(dataCount):
                dataIndex = i+1
                if dataIndex <= self.data.J_COUNT:
                    # Axis
                    end = start + 4
                    self.j_data[i] = struct.unpack("f", msg[start:end])[0]
                elif dataIndex > self.data.J_COUNT and dataIndex <= self.data.J_COUNT+self.data.AO_COUNT:
                    # Analog outputs (second half of PLC Analog Outputs)
                    end = start + 4
                    self.ao_data[i-self.data.J_COUNT] = struct.unpack("f", msg[start:end])[0]
                elif dataIndex > self.data.J_COUNT+self.data.AO_COUNT and dataIndex <= self.data.J_COUNT+self.data.AO_COUNT+self.data.DO_COUNT:
                    # Digital output
                    end = start + 2
                    self.do_data[i-self.data.J_COUNT-self.data.AO_COUNT] = struct.unpack("h", msg[start:end])[0]
                start = end

            # add update to queuedi_data
            queue.put([self.id, {'msgJRecv-udp': self.j_data}])
            queue.put([self.id, {'msgARecv-udp': self.ao_data}])
            queue.put([self.id, {'msgDORecv-udp': self.do_data}])

            # don't send data if simulating axis movement
            if self.data.IS_DEBUG:
                continue

            ##########################
            #######    SEND    #######
            ######  py -> robot ######
            ##########################   
            msgToPLC = bytes()
            #for j in self.j_data:
            #    msgToPLC = msgToPLC + struct.pack("f", j)

            for ai in self.ai_data:                                 
                msgToPLC = msgToPLC + struct.pack("f", ai)

            #for do in self.do_data:
            #    msgToPLC = msgToPLC + struct.pack("h", do)
            for di in self.di_data:                                 
                msgToPLC = msgToPLC + struct.pack("h", int(di)) #bools saved as floats (1.0 or 0.0) -> converted as ints (1 or 0)
            
            # Sending a reply to client
            self.UDPServerSocket.sendto(msgToPLC, addr)
            self.udpPacketsSent += 1
            # add update to queue
            queue.put([self.id, {'pktsSent-udp': self.udpPacketsSent}])
            queue.put([self.id, {'msgJSent-udp': self.j_data}])
            queue.put([self.id, {'msgASent-udp': self.ao_data}])
            queue.put([self.id, {'msgDOSent-udp': self.do_data}])
            queue.put([self.id, {'msgDISent-udp': self.di_data}])

    def RTDEClient(self, queue):
        recvData = [0.0] * self.data.J_COUNT

        # don't connect RTDE if simulating axis movement
        if self.data.IS_DEBUG:
            for j in range(self.data.J_COUNT):
                self.j_data[j] = math.degrees(recvData[j])
        else:
            self.rtdeConn = rtde.RTDE(self.data.UDP_HOST, self.data.DEFAULT_RTDE_PORT)
            self.rtdeConn.connect()

            logger.log("[RTDE client] connected...")
            
            # get controller version
            self.rtdeConn.get_controller_version()

            # setup recipes
            if not self.rtdeConn.send_output_setup(self.outNames, self.outTypes, frequency = self.data.DEFAULT_RTDE_FREQUENCY):
                logger.log("Error: [RTDEClient] Unable to configure output")
                return

            # start data synchronization
            if not self.rtdeConn.send_start():
                logger.log("Error: [RTDEClient] Unable to start synchronization")
                return
            
            while not self.stop_threads.is_set():
                try:
                    msg = self.rtdeConn.receive(False)
                    if msg is not None:
                        value = msg.__dict__[self.outNames[0]]
                        self.udpPacketsReceived += 1
                        # add update to queue
                        queue.put([self.id, {'pktsRecv-udp': self.udpPacketsReceived}])
                        
                        # getting data from message
                        for j in range(self.data.J_COUNT):
                            recvData[j] = value[j]
                        # add update to queue
                        queue.put([self.id, {'msgJRecv-udp': recvData}])

                        # send data
                        for j in range(self.data.J_COUNT):
                            self.j_data[j] = math.degrees(recvData[j])

                except rtde.RTDEException:
                    self.rtdeConn.disconnect()
                    return
            
            self.rtdeConn.send_pause()
            self.rtdeConn.disconnect()

    def TCPServer(self, queue):

        while not self.stop_threads.is_set():
            try:
                conn, remoteAddr = self.TCPServerSocket.accept()
            except socket.error as err:
                logger.log("TCP accept err: " + str(err))
                break

            with conn:
                logger.log(f"Connection received from {remoteAddr}")

                while not self.stop_threads.is_set():   
                    try:
                        ReceivedData = conn.recv(self.data.TCP_PACKET_SIZE).decode()
                    except socket.error as err:
                        logger.log("Error RECV: " + str(err))
                        break

                    # check if is there some data
                    if not ReceivedData:
                        break

                    # print the received data
                    logger.log(ReceivedData)

                    # main loop SEND-RECV
                    while not self.stop_threads.is_set():
                        
                        time.sleep(1/30)      

                        ##########################
                        #######    SEND    #######
                        #######  UE -> py  #######
                        ##########################                                            
                        # pack UDP data to create a message
                        # (numAxes) joints + (numAxes) spare AOs + 15 DOs
                        j_string = "&".join([str(j) for j in self.j_data])
                        ao_string = "&".join(str(ao) for ao in self.ao_data)
                        do_string = "&".join([str(do) for do in self.do_data])
                        msgToUE = bytes(j_string + "&" + ao_string + "&" + do_string,"utf-8")
                           
                        # SEND message (TCP, py -> UE)
                        try:
                            conn.sendall(msgToUE)
                            self.tcpPacketsSent += 1
                            # add update to queue
                            queue.put([self.id, {'pktsSent-tcp': self.tcpPacketsSent}])
                            queue.put([self.id, {'msgJSent-tcp': self.j_data}])
                            queue.put([self.id, {'msgDOSent-tcp': self.do_data}])
                        except socket.error as err:
                            logger.log("Error SEND: " + str(err))
                            break

                        ##########################
                        #######  RECEIVE   #######
                        #######  UE -> py  #######
                        ##########################
                        # receive (PLC) AIs and DIs
                        try:
                            ReceivedDataUnDecoded = conn.recv(self.data.TCP_PACKET_SIZE)
                            # logger.log(ReceivedDataUnDecoded)
                            # logger.log(str(self.id) + " - message bytes length: " + str(len(ReceivedDataUnDecoded)))
                            ReceivedData = ReceivedDataUnDecoded.decode()
                            self.tcpPacketsReceived += 1
                            # add update to queue
                            queue.put([self.id, {'pktsRecv-tcp': self.tcpPacketsReceived}])
                        except socket.error as err:
                            logger.log("Error RECV: " + str(err))
                            break
                        except UnicodeDecodeError as err:
                            logger.log("Error RECV: " + str(err))
                            logger.log("Data to decode: " + ReceivedData)

                        # print the received data
                        # logger.log("Recv from UE: " + ReceivedData)
                        
                        # check if message is empty
                        if ReceivedData == '':
                            logger.log("Warning: got EMPTY message from TCP connection!")
                            continue

                        packet = ReceivedData.split("&")
                        
                        # print data after splitting
                        logger.log(str(self.id) + " - ".join([el for el in packet]))

                        #for i in range(1, len(packet)):
                        #    try: 
                        #        if is_number_regex(packet[i]):
                        #            self.di_data[i-1] = float(packet[i]) 
                        #    except ValueError as err: 
                        #        logger.log(str(err)) 
                        #        logger.log(str(self.id) + " --- bad data received!")
                        
                        for ai in range(1,self.data.AI_COUNT):
                            try:
                                if is_number_regex(packet[ai]):
                                    self.ai_data[ai-1] = float(packet[ai])
                            except ValueError as err:
                                logger.log(str(err))
                                logger.log(str(self.id) + " --- bad data received")
                        
                        for di in range(1, self.data.DI_COUNT):
                            try:
                                if is_number_regex(packet[di]):
                                    self.di_data[di-1] = float(packet[di])
                            except ValueError as err:
                                logger.log(str(err))
                                logger.log(str(self.id) + " --- bad received data")
                        
                        # add update to queue
                        queue.put([self.id, {'msgDIRecv-tcp': self.di_data}])
                        
                        logger.log(str(self.id) + " PY --> UE: " + " | ".join([str(di) for di in self.di_data]))

if __name__ == '__main__':
    # getting arguments
    parser = argparse.ArgumentParser()
    # usage: [--iodebug | --no-iodebug] to launch or not executable at startup
    parser.add_argument('--iodebug', default=False, action=argparse.BooleanOptionalAction)
    args = parser.parse_args()

    # setup logger
    logger = Logger(to_console=True, to_file=False, is_active=True)

    # create and start panel
    ConnectionManager("Robot2")