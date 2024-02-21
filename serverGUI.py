from tkinter import *
from tkinter import ttk
from tkinter import messagebox
from PIL import ImageTk, Image
from data import Data
from configHandler import *
import uuidGenerator
import pyperclip
import subprocess

class ConnectionPanel:
    root = Tk()
    logoImage = ImageTk.PhotoImage(Image.open("_images/applied_logo.png"))
    plcImage = ImageTk.PhotoImage(Image.open("_images/plc_logo.png"))
    robotsImage = ImageTk.PhotoImage(Image.open("_images/robots_logo.png"))
    udpImage = ImageTk.PhotoImage(Image.open("_images/robot_logo.png"))
    udpImage2 = ImageTk.PhotoImage(Image.open("_images/robot_logo2.png"))
    udpImage3 = ImageTk.PhotoImage(Image.open("_images/fanuc_robot.png"))
    udpImage4 = ImageTk.PhotoImage(Image.open("_images/kuka_robot.png"))
    tcpImage = ImageTk.PhotoImage(Image.open("_images/ue_logo.png"))
    rpin = ImageTk.PhotoImage(Image.open("_images/rpin.png"))
    ypin = ImageTk.PhotoImage(Image.open("_images/ypin.png"))
    gpin = ImageTk.PhotoImage(Image.open("_images/gpin.png"))
    setupIcon = ImageTk.PhotoImage(Image.open("_images/icon_setup.png"))
    moveIcon = ImageTk.PhotoImage(Image.open("_images/icon_move.png"))
    ioIcon = ImageTk.PhotoImage(Image.open("_images/icon_io.png"))
    REFRESH_RATE_MS = 200
    ACTIVE_SIGN = "[X] "
    
    ConnectionTabs = []
    selectedTypes = []
    selectedJoints = []
    isSimulate = []
    isActive = []

    def __init__(self, firstTabTitle, onStart, onStop, onNewTab, isConnRunning, setTestData, queue, debugIO) -> None:
        self.queue = queue
        # init GUI root
        self.root.title("Configuration Panel")
        self.root.iconbitmap('_images/logo.ico')

        self.debugIO = debugIO
        

        # init main area
        self.setupMainArea(isConnRunning)

        # init robot notebook widget (container of tabs)
        self.robotNotebook = ttk.Notebook(self.root)
        self.robotNotebook.bind("<<NotebookTabChanged>>", lambda event: self.handleTabChange(onNewTab))
        self.robotNotebook.pack(padx=10, pady=15)

        # adding version label
        vLabel = Label(self.root, text="v1.4", font="Helvetica 8")
        vLabel.pack(side="right", anchor="se")

        # store some callbacks
        self.onNewTab = onNewTab
        self.setTestData = setTestData

        # init first tab
        frame = self.addNewTab(firstTabTitle)
        # add + tab 
        self.addNewTab("+")
        # setup first tab
        self.setupTab(frame, Data(), onStart, onStop)

        # load config if avaliable
        self.onLoadConfig()
    
    def run(self, onClosing):
        # setting panel closing event
        self.root.protocol("WM_DELETE_WINDOW", onClosing)
        # setting interval timer to refresh GUI data
        self.root.after(self.REFRESH_RATE_MS, self.updateStatusData)
        # show GUI
        self.root.mainloop()

    def end(self):
        if messagebox.askokcancel("Exit", "Do you want to quit?"):
            self.root.destroy()
            return True
        return False
    
    def handleTabChange(self, onNewTab):
        if self.robotNotebook.select() == self.robotNotebook.tabs()[-1]:
            index = len(self.robotNotebook.tabs())-1
            if messagebox.askokcancel("New Connection", "Do you want to create a new robot connection?"):
                self.createNewRobot(index, onNewTab)
            else:
                self.robotNotebook.select(index-1)

    def createNewRobot(self, index, onNewTab):
        title = "Robot"+str(index+1)
        # insert new tab
        frame = self.insetNewTabAtIndex(index, title)                
        # notify back that new tab is created
        [onStart, onStop] = onNewTab(title)
        self.setupTab(frame, Data(), onStart, onStop)

    def addNewTab(self, title):
        frame = Frame(self.robotNotebook)
        frame.pack(fill="both", expand=1)
        if title != "+": 
            self.robotNotebook.add(frame, text=self.ACTIVE_SIGN + title, image=self.rpin, compound=RIGHT)
            self.ConnectionTabs.append(frame)
        else:
            self.robotNotebook.add(frame, text=title)
        return frame

    def insetNewTabAtIndex(self, index, title):
        frame = Frame(self.robotNotebook)
        frame.pack(fill="both", expand=1)
        self.ConnectionTabs.append(frame)
        self.robotNotebook.insert(index, frame, text=self.ACTIVE_SIGN + title, image=self.rpin, compound=RIGHT)
        self.robotNotebook.select(index)
        return frame
    
    def toggleActive(self, index):
        active = 1 if self.isActive[index].get() else 0
        tabTitle = self.robotNotebook.tab(index, "text")
        if active == 1:
            self.robotNotebook.tab(index, text=self.ACTIVE_SIGN + tabTitle)
        else:
            self.robotNotebook.tab(index, text=tabTitle.lstrip(self.ACTIVE_SIGN))
        # notify user to remember to export
        self.notifyExport()

    def setupMainArea(self, isConnRunning):
        mainFrame = LabelFrame(self.root, text="Main Area", name="main_area", padx=15, pady=15)
        mainFrame.pack(padx=10, pady=(5,0))
        statusLabel = Label(mainFrame, text="Status:")
        statusLabel.grid(row=0, column=0, padx=(0,5))
        startAllButton = Button(mainFrame, text="Run All", fg="white", bg="#1c1c1c", command=lambda: self.onStartAllPressed(isConnRunning))
        startAllButton.grid(row=0, column=1, pady=(0,0))
        stopAllButton = Button(mainFrame, text="Stop All", fg="white", bg="#db1c12", command=lambda: self.onStopAllPressed(isConnRunning))
        stopAllButton.grid(row=1, column=1, pady=(5,0))
        enableLabel = Label(mainFrame, text="Enable:")
        enableLabel.grid(row=0, column=2, padx=(10,5))
        activateAllButton = Button(mainFrame, text="Activate All", command=lambda: self.onActivateAllPressed(isConnRunning))
        activateAllButton.grid(row=0, column=3, pady=(0,0))
        deactivateAllButton = Button(mainFrame, text="Deactivate All", command=lambda: self.onDeactivateAllPressed(isConnRunning))
        deactivateAllButton.grid(row=1, column=3, pady=(5,0))
        configLabel = Label(mainFrame, text="Config:")
        configLabel.grid(row=0, column=4, padx=(10,5))
        exportConfigBtn = Button(mainFrame, text="Export", name="export_btn", command=lambda: self.onExportConfig())
        exportConfigBtn.grid(row=0, column=5, pady=(0,0))
        loadConfigBtn = Button(mainFrame, text="Load", command=lambda: self.onLoadConfig())
        loadConfigBtn.grid(row=1, column=5, pady=(5,0))
        launchPLCBtn = Button(mainFrame, text="PLC", name="launchplc_btn", image=self.plcImage, compound="top", command=lambda: self.onLaunchPLC())
        launchPLCBtn.grid(row=0, column=7, rowspan = 2, padx=(50,5))
        launchRobotsBtn = Button(mainFrame, text="Robots", name="launchrobots_btn", image=self.robotsImage, compound="top", command=lambda: self.onLaunchRobots())
        launchRobotsBtn.grid(row=0, column=8, rowspan = 2, padx=5)
        launchGameBtn = Button(mainFrame, text="Launch scene", name="launchgame_btn", image=self.logoImage, compound="top", command=lambda: self.onLaunchGame())
        launchGameBtn.grid(row=0, column=9, rowspan = 2, padx=5)

    def setupTab(self, robotFrame, data, onStart, onStop):
        # init notebook widget (container of tabs)
        [frame1, frame2, frame3] = self.setupModes(robotFrame)

        # connection id
        index = len(self.selectedJoints)

        self.setupMode1(frame1, data, index)
        self.setupMode2(frame2, data.J_COUNT, index)
        self.setupMode3(frame3, data)

        # Start/Stop Area
        startButton = Button(robotFrame, text="Run", name="start_btn", width=10, height=2, fg="white", bg="#1c1c1c", command=lambda: self.onStartPressed(onStart, index, robotFrame, startButton, stopButton))
        startButton.pack(pady=(0,10))
        stopButton = Button(robotFrame, text="Stop", name="stop_btn", width=10, height=2, fg="white", bg="#db1c12", command=lambda: self.onStopPressed(onStop, index, robotFrame, startButton, stopButton))

    def setupModes(self, robotFrame):
        notebook = ttk.Notebook(robotFrame)
        notebook.pack(padx=10, pady=10)
        frame1 = Frame(notebook, name="setup_tab")
        frame1.pack(fill="both", expand=1)
        notebook.add(frame1, text="Setup", image=self.setupIcon, compound=TOP)
        frame2 = Frame(notebook, name="move_tab")
        frame2.pack(fill="both", expand=1)
        notebook.add(frame2, text="Move", image=self.moveIcon, compound=TOP)
        frame3 = Frame(notebook, name="io_tab")
        frame3.pack(fill="both", expand=1)
        notebook.add(frame3, text="I/O", image=self.ioIcon, compound=TOP)

        return [frame1, frame2, frame3]

    def setupMode1(self, frame1, data, index):
        # Info Area
        infoFrame = LabelFrame(frame1, text="Info", name="info_frame", padx=15, pady=15)
        infoFrame.pack(padx=5, pady=5)

        uIDLabel = Label(infoFrame, text="uID")
        uIDLabel.grid(row=0, column=0, pady=(0,5))
        uIDValue = Label(infoFrame, text=uuidGenerator.create(), name="uid_value")
        uIDValue.grid(row=0, column=1, pady=(0,5))
        uIDBtn = Button(infoFrame, text="Copy", command=lambda: pyperclip.copy(uIDValue['text']))
        uIDBtn.grid(row=0, column=2)

        typeLabel = Label(infoFrame, text="Type")
        typeLabel.grid(row=1, column=0, pady=(0,5))
        self.selectedTypes.append(StringVar())
        self.selectedTypes[index].set(data.ROBOT_TYPE)
        typeDrop = OptionMenu(infoFrame, self.selectedTypes[index], *data.ROBOT_TYPES, command=lambda t: self.changeRobotType(index, t, data, frame1, False))
        typeDrop.grid(row=1, column=1)

        nameLabel = Label(infoFrame, text="Name")
        nameLabel.grid(row=2, column=0, pady=(5,0))
        nameEntry = Entry(infoFrame, name="name_entry")
        nameEntry.grid(row=2, column=1, pady=(5,0))
        nameEntry.insert(0, "Robot" + str(index+1))
        nameBtn = Button(infoFrame, text="Change", command=lambda: self.changeTabTitle(index, nameEntry))
        nameBtn.grid(row=2, column=2, pady=(5,0))

        # UDP Area
        udpFrame = LabelFrame(frame1, text="UDP connection [PLC - Python]", name="udp_frame", padx=15, pady=15)
        udpFrame.pack(padx=5, pady=5)

        udpImageLabel = Label(udpFrame, name="udp_image", image=self.udpImage)
        udpImageLabel.grid(row=0, column=0, columnspan = 2, pady=(0,5))

        udpHostLabel = Label(udpFrame, text="Host IP")
        udpHostLabel.grid(row=1, column=0)
        udpHostEntry = Entry(udpFrame, name="udp_host_entry", width=15)
        udpHostEntry.grid(row=1, column=1)
        udpHostEntry.insert(0, data.UDP_HOST)

        udpPortLabel = Label(udpFrame, text="Port")
        udpPortLabel.grid(row=2, column=0)
        udpPortEntry = Entry(udpFrame, name="udp_port_entry", width=15)
        udpPortEntry.grid(row=2, column=1)
        udpPortEntry.insert(0, data.UDP_PORT)

        # TCP Area
        tcpFrame = LabelFrame(frame1, text="TCP connection [Python - Unreal]", name="tcp_frame", padx=15, pady=15)
        tcpFrame.pack(padx=5, pady=5)

        tcpImageLabel = Label(tcpFrame, image=self.tcpImage)
        tcpImageLabel.grid(row=0, column=0, columnspan = 2, pady=(0,5))

        tcpHostLabel = Label(tcpFrame, text="Host IP")
        tcpHostLabel.grid(row=1, column=0)
        tcpHostEntry = Entry(tcpFrame, name="tcp_host_entry", width=15)
        tcpHostEntry.grid(row=1, column=1)
        tcpHostEntry.insert(0, data.TCP_HOST)

        tcpPortLabel = Label(tcpFrame, text="Port")
        tcpPortLabel.grid(row=2, column=0)
        tcpPortEntry = Entry(tcpFrame, name="tcp_port_entry", width=15)
        tcpPortEntry.grid(row=2, column=1)
        tcpPortEntry.insert(0, data.TCP_PORT)

        # Properties Area
        propFrame = LabelFrame(frame1, text="Properties", name="props_frame", padx=15, pady=15)
        propFrame.pack(padx=5, pady=5)

        jointsLabel = Label(propFrame, text="Joints")
        jointsLabel.grid(row=0, column=0, padx=3)
        self.selectedJoints.append(IntVar())
        self.selectedJoints[index].set(data.J_COUNT)
        jointsDrop = OptionMenu(propFrame, self.selectedJoints[index], *data.JOINTS_OPTIONS, command=lambda x: self.changeJoints(index, x))
        jointsDrop.grid(row=1, column=0)

        #analogLabel = Label(propFrame, text="Analogs")
        #analogLabel.grid(row=0, column=1, padx=3)
        #analogEntry = Entry(propFrame, name="analogs_entry", justify=CENTER, width=4)
        #analogEntry.grid(row=1, column=1)
        #analogEntry.insert(0, data.A_COUNT)
        #analogEntry.config(state='disabled')

        aoLabel = Label(propFrame, text = "AOs")
        aoLabel.grid(row = 0, column = 1, padx = 0)
        aoEntry = Entry(propFrame,name = "ao_entry", justify = CENTER, width = 4)
        aoEntry.grid(row = 1, column = 1)
        aoEntry.insert(0, data.AO_COUNT)
        aoEntry.config(state='normal')

        aiLabel = Label(propFrame, text = "AIs")
        aiLabel.grid(row = 0, column = 2, padx = 9)
        aiEntry = Entry(propFrame,name = "ai_entry", justify = CENTER, width = 4)
        aiEntry.grid(row = 1, column = 2)
        aiEntry.insert(0, data.AI_COUNT)
        aiEntry.config(state='normal')

        doLabel = Label(propFrame, text="DOs")
        doLabel.grid(row=0, column=3, padx=9)
        doEntry = Entry(propFrame, name="do_entry", justify = CENTER, width = 4)
        doEntry.grid(row=1, column=3)
        doEntry.insert(0, data.DO_COUNT)
        doEntry.config(state='normal')

        diLabel = Label(propFrame, text="DIs")
        diLabel.grid(row=0, column=4, padx=9)
        diEntry = Entry(propFrame, name="di_entry", justify = CENTER, width = 4)
        diEntry.grid(row=1, column=4)
        diEntry.insert(0, data.DI_COUNT)
        diEntry.config(state='normal')

        self.isSimulate.append(IntVar())
        self.isSimulate[index].set(1 if data.IS_DEBUG else 0)
        debugLabel = Label(propFrame, text="Simulate locally")
        debugLabel.grid(row=4, column=1, pady=(5,0))
        debugCheck = Checkbutton(propFrame, variable=self.isSimulate[index])
        debugCheck.grid(row=4, column=2, pady=(5,0))

        self.isActive.append(IntVar())
        self.isActive[index].set(1 if data.IS_ACTIVE else 0)
        isActiveLabel = Label(propFrame, text="Is active")
        isActiveLabel.grid(row=5, column=1, pady=(5,0))
        isActiveCheck = Checkbutton(propFrame, name="isactive_check", variable=self.isActive[index], command=lambda: self.toggleActive(index))
        isActiveCheck.grid(row=5, column=2, pady=(5,0))

        return index

    def setupMode2(self, frame2, jCount, index):
        startRecordingButton = None
        
        uuid_value = self.ConnectionTabs[index].children["!notebook"].children["setup_tab"].children["info_frame"].children["uid_value"]['text']
        
        
        # Funzione per controllare se esiste un robot con l'UUID specifico in config.json
        def checkRobotExists():
            try:
                with open("config.json", 'r') as conf_file:
                    conf = json.load(conf_file)
                    return any(robot != 'quantity' and (conf[robot]['uid'] == uuid_value and conf[robot]['saved_robtargets'] != None) for robot in conf)
            except (FileNotFoundError, json.JSONDecodeError, KeyError):
                return False
                
                
        def onEntry(event):
            val = event.widget.get()
            entryIndex = event.widget.winfo_name().split('jEntry')[1]
            s = jointsFrame.children['jSlider'+entryIndex]
            if self.is_numeric(val):
                val = float(val)               
                s.set(val)
                min = s.cget("from")
                max = s.cget("to") 
                if val < min or val > max:
                    event.widget.delete(0, END)
                    event.widget.insert(0, s.get())
                # update test data
                self.setTestData(index, [float(w.get()) for w in jointsFrame.winfo_children() if isinstance(w, Entry)])

        def onSlide(event):
            sliderIndex = event.widget.winfo_name().split('jSlider')[1]
            e = jointsFrame.children['jEntry'+sliderIndex]
            e.delete(0, END)
            e.insert(0, event.widget.get())
            # update test data
            self.setTestData(index, [float(w.get()) for w in jointsFrame.winfo_children() if isinstance(w, Entry)])
        
        # Funzione per gestire il click su "Save Robot Target"
        def onSaveRobotTarget():
            with open("config.json", 'r+') as conf_file:
                conf = json.load(conf_file)
            joint_data = [float(w.get()) for w in jointsFrame.winfo_children() if isinstance(w, Entry)]
            
            found_robot = False

            # Trova il robot con l'UUID corrispondente e aggiungi i valori dei giunti a 'saved_robtargets'
            for robot in conf:
                if robot != 'quantity' and conf[robot]['uid'] == uuid_value:
                    if 'saved_robtargets' not in conf[robot]:
                        conf[robot]['saved_robtargets'] = []
                    conf[robot]['saved_robtargets'].append(joint_data)
                    found_robot = True
                    break
                
            if not found_robot:
                if messagebox.askokcancel("Save trajectories", "In order to save trajectory of a new robot you first have to export configuration"):
                    self.onExportConfig()
                    onSaveRobotTarget()
                else:
                    return
            else:
                # Riscrivi il file JSON con i dati aggiornati
                with open("config.json", 'w+') as file:
                    json.dump(conf, file, indent=4)


        # Funzione per gestire il click su "Stop Recording"
        def onStopRecording():
            stopRecordingButton.pack_forget()
            saveButton.pack_forget()
            startRecordingButton.pack(side=BOTTOM, pady=10)
            # Controlla se il robot con questo UUID esiste nel file config.json
            robot_exists = checkRobotExists()

            # Logica per mostrare pulsanti diversi in base alla presenza del robot
            if robot_exists:
                deleteButton.pack(side=LEFT, pady=100, padx=50)
                loadButton.pack(side=RIGHT, pady=100, padx=50)
                startRecordingButton.pack_forget()
            else:
                deleteButton.pack_forget()
                loadButton.pack_forget()
                startRecordingButton.pack(side=BOTTOM, pady=10)

        # Funzione per alternare i pulsanti "Start Recording" e "Stop Recording"
        def onStartRecording():
            startRecordingButton.pack_forget()
            stopRecordingButton.pack(side=LEFT, padx=50)
            saveButton.pack(side=RIGHT, padx=50)

        def onDeleteSavedTrajectory():
            try:
                # Apri il file config.json e carica i dati
                with open("config.json", 'r') as file:
                    conf = json.load(file)

                # Cerca l'oggetto con l'UID specificato e rimuovi 'saved_robtargets'
                for robot in conf:
                    if robot != 'quantity' and conf[robot]['uid'] == uuid_value:
                        if 'saved_robtargets' in conf[robot]:
                            del conf[robot]['saved_robtargets']
                        break

                # Scrivi i dati aggiornati nel file config.json
                with open("config.json", 'w') as file:
                    json.dump(conf, file, indent=4)

                messagebox.showinfo("Success", "Saved trajectories for robot with UUID " + uuid_value + " have been deleted.")
                # Controlla se il robot con questo UUID esiste nel file config.json
                robot_exists = checkRobotExists()

                # Logica per mostrare pulsanti diversi in base alla presenza del robot
                if robot_exists:
                    deleteButton.pack(side=LEFT, pady=100, padx=50)
                    loadButton.pack(side=RIGHT, pady=100, padx=50)
                    startRecordingButton.pack_forget()
                else:
                    deleteButton.pack_forget()
                    loadButton.pack_forget()
                    startRecordingButton.pack(side=BOTTOM, pady=10)
                        
            except FileNotFoundError:
                messagebox.showerror("Error", "The configuration file was not found.")
            except json.JSONDecodeError:
                messagebox.showerror("Error", "Error reading the configuration file.")

        def initSavedTrajectoriesSlider():
            try:
                with open("config.json", 'r') as conf_file:
                    conf = json.load(conf_file)

                for robot in conf:
                    if robot != 'quantity' and conf[robot]['uid'] == uuid_value:
                        if 'saved_robtargets' in conf[robot]:
                            saved_trajectories = conf[robot]['saved_robtargets']
                            savedTrajectoriesSlider['to'] = len(saved_trajectories) - 1
                            savedTrajectoriesSlider.pack(pady=10)
                            break
                        
                stopLoadingTrajectoy.pack(pady=10)
            except Exception as e:
                print("Error initializing saved trajectories slider:", e)
                
        def loadSavedTrajectory():
            tab_index = int(savedTrajectoriesSlider.get())
            try:
                with open("config.json", 'r') as conf_file:
                    conf = json.load(conf_file)
                for robot in conf:
                    if robot != 'quantity' and conf[robot]['uid'] == uuid_value:
                        if 'saved_robtargets' in conf[robot]:
                            saved_trajectory = conf[robot]['saved_robtargets'][tab_index]
                            # Itera attraverso i valori salvati e imposta i valori degli slider
                            for j, value in enumerate(saved_trajectory):
                                slider_name = "jSlider" + str(j+1)
                                if slider_name in jointsFrame.children:
                                    slider = jointsFrame.children[slider_name]
                                    slider.set(value)
                                e = jointsFrame.children['jEntry'+str(j + 1)]
                                e.delete(0, END)
                                e.insert(0, value)
                self.setTestData(index, saved_trajectory)
            except Exception as e:
                print("Error printing saved trajectory:", e)
                
        def onLoadSavedTrajectory():
            # Implementa la logica per caricare la traiettoria salvata
            initSavedTrajectoriesSlider()
            loadButton.pack_forget()
            deleteButton.pack_forget()
            loadSavedTrajectory()
        def onStopLoadingTrajectory():
            savedTrajectoriesSlider.pack_forget()
            deleteButton.pack(side=LEFT, pady=100, padx=50)
            loadButton.pack(side=RIGHT, pady=100, padx=50)
            stopLoadingTrajectoy.pack_forget()
            
            pass
            
        startRecordingButton = Button(frame2, text="Start recording", bg='green', fg='white', command=onStartRecording, name="start_recording_robtarget")
        stopRecordingButton = Button(frame2, text="Stop Recording", bg='red', fg='white', command=onStopRecording, name="stop_recording_button")
        stopLoadingTrajectoy = Button(frame2, text="Stop Loading", bg='red', fg='white', command=onStopLoadingTrajectory, name="stop_loading_button")
        saveButton = Button(frame2, text="Save Robot Target", bg="blue", fg='white', command=onSaveRobotTarget, name="save_robot_target_button")
        deleteButton = Button(frame2, text="Delete Saved Trajectory", bg='red', fg='white', command=lambda: onDeleteSavedTrajectory(), name="delete_saved_trajectory")
        loadButton = Button(frame2, text="Load Saved Trajectory", bg="blue", fg='white', command=lambda: onLoadSavedTrajectory(), name='load_saved_trajectory')
        
        
        # Aggiungi il nuovo Slider per le traiettorie salvate
        savedTrajectoriesSlider = Scale(frame2, from_=0, to=0, orient=HORIZONTAL, name='saved_trajectories_slider')
        savedTrajectoriesSlider.bind("<B1-Motion>", lambda event: loadSavedTrajectory())

        # Controlla se il robot con questo UUID esiste nel file config.json
        robot_exists = checkRobotExists()

        # Logica per mostrare pulsanti diversi in base alla presenza del robot
        if robot_exists:
            deleteButton.pack(side=LEFT, pady=0)
            loadButton.pack(side=RIGHT, pady=0)
        else:
            startRecordingButton.pack(side=BOTTOM, pady=10)
                
                
        jointsFrame = LabelFrame(frame2, text="Joints", name="joints_frame", padx=15, pady=15)
        jointsFrame.pack(padx=10, pady=10)
        
        for j in range(jCount):
            start = j * 2
            end = start + 2
            couplePos = [i for i in range(start + 1, end + 1)]
            no = Label(jointsFrame, text=str(j+1), font="Helvetica 11")
            no.grid(row=couplePos[0], column=0)
            entry = Entry(jointsFrame, name="jEntry"+str(j+1), justify=CENTER, width=12)
            entry.grid(row=couplePos[0], column=1, pady=(10,3))
            entry.insert(0, 0)
            slider = Scale(jointsFrame, name="jSlider"+str(j+1), length=250, resolution=0.01, from_=-360, to=360, orient=HORIZONTAL, showvalue=0)
            slider.grid(row=couplePos[1], column=1, pady=(0,10))

            # bind events
            entry.bind("<KeyRelease>", lambda event: onEntry(event))
            slider.bind("<B1-Motion>", lambda event: onSlide(event))


    def setupMode3(self, frame3, data):
        # UDP Area
        udpFrame = LabelFrame(frame3, text="UDP connection [PLC - Python]", name="udp_frame", padx=15, pady=15)
        udpFrame.pack(padx=10, pady=10)

        udpPacketsRecvLabel = Label(udpFrame, text="# Received", font='Helvetica 10 bold')
        udpPacketsRecvLabel.grid(row=0, column=0, pady=(0,5))
        udpPacketsRecv = Label(udpFrame, name="pktsRecv", text="0", font='Helvetica 10 bold')
        udpPacketsRecv.grid(row=0, column=1)
        
        if self.debugIO:
            udpRecvJLabel = Label(udpFrame, text="J")
            udpRecvJLabel.grid(row=1, column=0, padx=3)
            self.spawnLabels(udpFrame, 1, data.J_COUNT, "JRecv")

            udpRecvALabel = Label(udpFrame, text="A")
            udpRecvALabel.grid(row=2, column=0, padx=3)
            self.spawnLabels(udpFrame, 2, data.A_COUNT, "ARecv")

            udpRecvDOLabel = Label(udpFrame, text="DO")
            udpRecvDOLabel.grid(row=3, column=0, padx=3)
            self.spawnLabels(udpFrame, 3, data.DO_COUNT, "DORecv")

        udpPacketsSentLabel = Label(udpFrame, text="# Sent", font='Helvetica 10 bold')
        udpPacketsSentLabel.grid(row=5, column=0, pady=5)
        udpPacketsSent = Label(udpFrame, name="pktsSent", text="0", font='Helvetica 10 bold')
        udpPacketsSent.grid(row=5, column=1)

        if self.debugIO:
            udpSentJLabel = Label(udpFrame, text="J")
            udpSentJLabel.grid(row=6, column=0, padx=3)
            self.spawnLabels(udpFrame, 6, data.J_COUNT, "JSent")

            udpSentALabel = Label(udpFrame, text="A")
            udpSentALabel.grid(row=7, column=0, padx=3)
            self.spawnLabels(udpFrame, 7, data.A_COUNT,"ASent")

            udpSentDOLabel = Label(udpFrame, text="DO")
            udpSentDOLabel.grid(row=8, column=0, padx=3)
            self.spawnLabels(udpFrame, 8, data.DO_COUNT, "DOSent")

            udpSentDILabel = Label(udpFrame, text="DI")
            udpSentDILabel.grid(row=9, column=0, padx=3)
            self.spawnLabels(udpFrame, 9, data.DI_COUNT, "DISent")

        # TCP Area
        tcpFrame = LabelFrame(frame3, text="TCP connection [Python - Unreal]", name="tcp_frame", padx=15, pady=15)
        tcpFrame.pack(padx=10, pady=10)

        tcpPacketsRecvLabel = Label(tcpFrame, text="# Received", font='Helvetica 10 bold')
        tcpPacketsRecvLabel.grid(row=0, column=0, pady=(0,5))
        tcpPacketsRecv = Label(tcpFrame, name="pktsRecv", text="0", font='Helvetica 10 bold')
        tcpPacketsRecv.grid(row=0, column=1)

        if self.debugIO:
            tcpRecvDILabel = Label(tcpFrame, text="DI")
            tcpRecvDILabel.grid(row=1, column=0, padx=3)
            self.spawnLabels(tcpFrame, 1, data.DI_COUNT, "DIRecv")

        tcpPacketsSentLabel = Label(tcpFrame, text="# Sent", font='Helvetica 10 bold')
        tcpPacketsSentLabel.grid(row=2, column=0, pady=5)
        tcpPacketsSent = Label(tcpFrame, name="pktsSent", text="0", font='Helvetica 10 bold')
        tcpPacketsSent.grid(row=2, column=1)

        if self.debugIO:
            tcpSentJLabel = Label(tcpFrame, text="J")
            tcpSentJLabel.grid(row=3, column=0, padx=3)
            self.spawnLabels(tcpFrame, 3, data.J_COUNT, "JSent")

            tcpSentDOLabel = Label(tcpFrame, text="DO")
            tcpSentDOLabel.grid(row=4, column=0, padx=3)
            self.spawnLabels(tcpFrame, 4, data.DO_COUNT, "DOSent")

    def updateStatusData(self):
        # refresh GUI with new data from the queue
        while not self.queue.empty():
            [index, status] = self.queue.get()
            frame = self.ConnectionTabs[index]
            ioTab = frame.children["!notebook"].children["io_tab"]
            moveTab = frame.children["!notebook"].children["move_tab"]
            udpArea = ioTab.children["udp_frame"]
            tcpArea = ioTab.children["tcp_frame"]
            moveJoints = moveTab.children["joints_frame"]
            for key in status:
                data = status[key]
                # check commands from queue
                if key.startswith("pkts"):
                    type = key.split('-')[0] 
                    protocol = key.split('-')[1]
                    if protocol == "tcp":
                        tcpArea.children[type].config(text=str(data))
                    elif protocol == "udp":
                        udpArea.children[type].config(text=str(data))
                elif key.startswith("udpateJoints"):
                    # delete joints widgets
                    # move tab
                    moveJoints.destroy()
                    # i/o tab
                    for w in udpArea.winfo_children():
                        if w.winfo_name().startswith('msgJ'):
                            w.destroy()
                    for w in tcpArea.winfo_children():
                        if w.winfo_name().startswith('msgJ'):
                            w.destroy()
                    # recreate widgets based on new quantity
                    # move tab
                    self.setupMode2(moveTab, data, index)
                    # i/o tab
                    if self.debugIO:
                        self.spawnLabels(udpArea, 1, data, "JRecv")
                        self.spawnLabels(udpArea, 6, data, "JSent")
                        self.spawnLabels(tcpArea, 3, data, "JSent")
                else:
                    if not self.debugIO:
                        continue

                    if key.startswith("msg"):
                        type = key.split('-')[0]                    
                        protocol = key.split('-')[1]                 
                        for (idx, j) in enumerate(data):
                            if protocol == "tcp":
                                tcpArea.children[type+str(idx+1)].config(text=str(round(j,2)))
                            elif protocol == "udp":
                                udpArea.children[type+str(idx+1)].config(text=str(round(j,2)))
                    

        # recursively set interval timer 
        self.root.after(self.REFRESH_RATE_MS, self.updateStatusData)

    def spawnLabels(self, parent, row, quantity, type):
        for i in range(quantity):
            label = Label(parent, text="0.0", name="msg"+type+str(i+1), width=5)
            label.grid(row=row, column=i+1, padx=5)
    
    def changeJoints(self, index, x):
        self.queue.put([index, {'udpateJoints': x}]) if x != self.selectedJoints[index] else None

    def changeRobotType(self, index, type, data, setupFrame, loadingData):
        udpArea = setupFrame.children["udp_frame"]
        udpImage = udpArea.children["udp_image"]
        portEntry = udpArea.children["udp_port_entry"]
        jointsDrop = setupFrame.children["props_frame"].children["!optionmenu"]
        jointsMenu = jointsDrop["menu"]
        if int(type.split(':')[0]) == 1:
            # Universal Robot
            udpArea.configure(text="RTDE connection [PLC - Python]")
            udpImage.configure(image=self.udpImage2)
            self.setEntry(portEntry, data.DEFAULT_RTDE_PORT)
            portEntry.config(state='disabled')
            # disable unavailable joints
            for i in range(jointsMenu.index("end")+1):      
                if jointsMenu.entrycget(i, "label") != 6:
                    jointsMenu.entryconfig(i, state="disabled")
            self.selectedJoints[index].set(6)
            self.changeJoints(index, 6)
        elif int(type.split(':')[0]) == 2:
            # FANUC Robot
            udpArea.configure(text="FANUC Connection [PLC - Python]")
            udpImage.configure(image=self.udpImage3)
            self.setEntry(portEntry, data.DEFAULT_FANUC_CONTROLLER_PORT)
            portEntry.config(state='disabled')
            # disable unavailable joints
            for i in range(jointsMenu.index("end")+1):      
                if jointsMenu.entrycget(i, "label") != 6:
                    jointsMenu.entryconfig(i, state="disabled")
            self.selectedJoints[index].set(6)
            self.changeJoints(index, 6)
        elif int(type.split(':')[0]) == 3:
            # KUKA Robot
            udpArea.configure(text="KUKA Connection [PLC - Python]")
            udpImage.configure(image=self.udpImage4)
            portEntry.config(state='normal')
            self.setEntry(portEntry, data.DEFAULT_KUKA_CONTROLLER_PORT)
            
            # disable unavailable joints
            for i in range(jointsMenu.index("end")+1):      
                if jointsMenu.entrycget(i, "label") != 6:
                    jointsMenu.entryconfig(i, state="disabled")
            self.selectedJoints[index].set(6)
            self.changeJoints(index, 6)
        else:
            udpArea.configure(text="UDP connection [PLC - Python]")
            udpImage.configure(image=self.udpImage)
            portEntry.config(state='normal')
            self.setEntry(portEntry, data.UDP_PORT)
            # enable all joints
            for i in range(jointsMenu.index("end")+1):
                jointsMenu.entryconfig(i, state="normal")
            self.selectedJoints[index].set(data.JOINTS_OPTIONS[0])
            self.changeJoints(index, data.JOINTS_OPTIONS[0])

        if not loadingData:
            self.notifyExport()

    def notifyExport(self):
        self.root.children["main_area"].children["export_btn"]['text'] = "Export *"
        self.root.children["main_area"].children["export_btn"]['bg'] = "#e8d479"

    def changeTabTitle(self, index, entry):
        newTitle = entry.get()
        if self.robotNotebook.tab(index, "text").startswith(self.ACTIVE_SIGN):
            self.robotNotebook.tab(index, text=self.ACTIVE_SIGN + newTitle)
        else:
            self.robotNotebook.tab(index, text=newTitle)
        self.notifyExport()

    def onStartPressed(self, onStart, index, frame, startButton, stopButton):
        startButton.pack_forget()
        stopButton.pack(pady=(0,10))

        notebook = frame.children["!notebook"]
        setupTab = notebook.children["setup_tab"]
        moveTab = notebook.children["move_tab"]
        ioTab = notebook.children["io_tab"]

        started = onStart(
            int(self.selectedTypes[index].get().split(':')[0]),
            setupTab.children["udp_frame"].children["udp_host_entry"].get(),
            setupTab.children["udp_frame"].children["udp_port_entry"].get(),
            setupTab.children["tcp_frame"].children["tcp_host_entry"].get(),
            setupTab.children["tcp_frame"].children["tcp_port_entry"].get(),
            self.selectedJoints[index].get(),
            setupTab.children["props_frame"].children["ao_entry"].get(),
            setupTab.children["props_frame"].children["ai_entry"].get(),
            setupTab.children["props_frame"].children["do_entry"].get(),
            setupTab.children["props_frame"].children["di_entry"].get(),
            self.isSimulate[index].get(),
            self.isActive[index].get()
        )

        if started:
            if self.isSimulate[index].get(): # if "Simulate locally" enabled
                # show yellow pin
                self.robotNotebook.tab(index, image=self.ypin)
                # select move tab
                notebook.select(moveTab)
            else:
                # show green pin
                self.robotNotebook.tab(index, image=self.gpin)
                # select i/o tab
                notebook.select(ioTab)
        else:
            # restore buttons status 
            stopButton.pack_forget()
            startButton.pack(pady=(0,10))

    def onStopPressed(self, onStop, index, frame, startButton, stopButton):        
        stopped = onStop()
        
        if stopped: 
            self.robotNotebook.tab(index, image=self.rpin)
            stopButton.pack_forget()
            startButton.pack(pady=(0,10))

            notebook = frame.children["!notebook"]
            setupTab = notebook.children["setup_tab"]
            # select setup tab
            notebook.select(setupTab)
    
    def onStartAllPressed(self, isConnRunning):
        for index, frame in enumerate(self.ConnectionTabs):
            if not isConnRunning(index):
                frame.children["start_btn"].invoke()
    
    def onStopAllPressed(self, isConnRunning):
        for index, frame in enumerate(self.ConnectionTabs):
            if isConnRunning(index):
                frame.children["stop_btn"].invoke()

    def onActivateAllPressed(self, isConnRunning):
        for index, frame in enumerate(self.ConnectionTabs):
            if not isConnRunning(index):
                notebook = frame.children["!notebook"]
                setupTab = notebook.children["setup_tab"]
                checkbox = setupTab.children["props_frame"].children["isactive_check"]
                if not self.isActive[index].get():
                    checkbox.select()
                    # update the rest accordingly after changing checkbox status
                    self.toggleActive(index)
    
    def onDeactivateAllPressed(self, isConnRunning):
        for index, frame in enumerate(self.ConnectionTabs):
            if not isConnRunning(index):
                notebook = frame.children["!notebook"]
                setupTab = notebook.children["setup_tab"]
                checkbox = setupTab.children["props_frame"].children["isactive_check"]
                if self.isActive[index].get():
                    checkbox.deselect()
                    # update the rest accordingly after changing checkbox status
                    self.toggleActive(index)
    
    def onExportConfig(self):
        data = {}
        data['quantity'] = len(self.ConnectionTabs)
        print(len(self.ConnectionTabs))
        for index, tab in enumerate(self.ConnectionTabs):
            obj = {}
            notebook = tab.children["!notebook"]
            setupTab = notebook.children["setup_tab"]
            moveTab = notebook.children["move_tab"]
            obj['uid'] = setupTab.children["info_frame"].children["uid_value"]['text']
            obj['name'] = self.robotNotebook.tab(index, "text").lstrip(self.ACTIVE_SIGN)
            obj['type'] = self.selectedTypes[index].get()
            obj['connection'] = {
                'udp_host_entry': setupTab.children["udp_frame"].children["udp_host_entry"].get(),
                'udp_port_entry': setupTab.children["udp_frame"].children["udp_port_entry"].get(),
                'tcp_host_entry': setupTab.children["tcp_frame"].children["tcp_host_entry"].get(),
                'tcp_port_entry': setupTab.children["tcp_frame"].children["tcp_port_entry"].get()
            }
            obj['selectedJoints'] = int(self.selectedJoints[index].get())
            #obj['analogs_entry'] = int(setupTab.children["props_frame"].children["analogs_entry"].get())
            obj['ao_entry'] = int(setupTab.children["props_frame"].children["ao_entry"].get())
            obj['ai_entry'] = int(setupTab.children["props_frame"].children["ai_entry"].get())
            obj['do_entry'] = int(setupTab.children["props_frame"].children["do_entry"].get())
            obj['di_entry'] = int(setupTab.children["props_frame"].children["di_entry"].get())
            obj['isSimulate'] = self.isSimulate[index].get()
            obj['isActive'] = self.isActive[index].get()
            obj['move_joints'] = [float(w.get()) for w in moveTab.children["joints_frame"].winfo_children() if isinstance(w, Entry)]
            data[index] = obj
        
        # export data to json file 
        exportToJson(data)
        

        # reset button state
        self.root.children["main_area"].children["export_btn"]['text'] = "Export"
        self.root.children["main_area"].children["export_btn"]['bg'] = "#f0f0f0"

    def onLoadConfig(self):
        config = loadFromJson()
        
        if config != None:
            toAdd = config['quantity']-len(self.ConnectionTabs)
            if toAdd > 0:
                for i in range(toAdd):
                    # create robots
                    self.createNewRobot(len(self.ConnectionTabs), self.onNewTab)
            for i in range(len(self.ConnectionTabs)):
                if i >= config['quantity']:
                    break
                # load data
                tab = self.ConnectionTabs[i]
                notebook = tab.children["!notebook"]
                setupTab = notebook.children["setup_tab"]
                setupTab.children["info_frame"].children["uid_value"]['text'] = config[str(i)]["uid"]
                self.setEntry(setupTab.children["info_frame"].children["name_entry"], config[str(i)]["name"])
                self.robotNotebook.tab(i, text=config[str(i)]["name"])
                self.selectedTypes[i].set(config[str(i)]["type"])
                self.changeRobotType(i, config[str(i)]["type"], Data(), setupTab, True)
                self.setEntry(setupTab.children["udp_frame"].children["udp_host_entry"], config[str(i)]["connection"]["udp_host_entry"])
                self.setEntry(setupTab.children["udp_frame"].children["udp_port_entry"], config[str(i)]["connection"]["udp_port_entry"])
                self.setEntry(setupTab.children["tcp_frame"].children["tcp_host_entry"], config[str(i)]["connection"]["tcp_host_entry"])
                self.setEntry(setupTab.children["tcp_frame"].children["tcp_port_entry"], config[str(i)]["connection"]["tcp_port_entry"])
                self.selectedJoints[i].set(config[str(i)]["selectedJoints"])
                self.queue.put([i, {'udpateJoints': config[str(i)]["selectedJoints"]}])
                #self.setEntry(setupTab.children["props_frame"].children["analogs_entry"], config[str(i)]["analogs_entry"])
                self.setEntry(setupTab.children["props_frame"].children["ao_entry"], config[str(i)]["ao_entry"])
                self.setEntry(setupTab.children["props_frame"].children["ai_entry"], config[str(i)]["ai_entry"])
                self.setEntry(setupTab.children["props_frame"].children["do_entry"], config[str(i)]["do_entry"])
                self.setEntry(setupTab.children["props_frame"].children["di_entry"], config[str(i)]["di_entry"])
                self.isSimulate[i].set(1 if config[str(i)]["isSimulate"] else 0)
                active = 1 if config[str(i)]["isActive"] else 0
                tabTitle = self.robotNotebook.tab(i, "text")
                if active == 1:
                    self.robotNotebook.tab(i, text=self.ACTIVE_SIGN + tabTitle)
                else:
                    self.robotNotebook.tab(i, text=tabTitle.lstrip(self.ACTIVE_SIGN))
                self.isActive[i].set(active)

    def onLaunchPLC(self):
        # prevent user launching multiple instances of external exe
        if hasattr(self, 'plcProcess') and self.plcProcess.poll() is None:
            print("[Warning] Can't launch multiple instances of external exe.")
            return
        
        dir = "..\\..\\..\\ConveyorControl"
        path = os.path.join(dir, "ConveyorControl.apj")

        if os.path.exists(path):
            print("Launching PLC...")
            self.plcProcess = subprocess.Popen('cd ' + dir + ' && start ConveyorControl.apj', cwd='.', shell=True)

    def onLaunchRobots(self):
        # prevent user launching multiple instances of external exe
        if hasattr(self, 'robotsProcess') and self.robotsProcess.poll() is None:
            print("[Warning] Can't launch multiple instances of external exe.")
            return
        
        dir = os.path.join(os.environ["ProgramFiles(x86)"], "VMware/VMware Player")
        path = os.path.join(dir, "vmplayer.exe")

        if os.path.exists(path):
            print("Launching Robots...")
            self.robotsProcess = subprocess.Popen(["vmplayer.exe"], cwd=dir, shell=True)

    def onLaunchGame(self):
        # prevent user launching multiple instances of external exe
        if hasattr(self, 'gameProcess') and self.gameProcess.poll() is None:
            print("[Warning] Can't launch multiple instances of external exe.")
            return

        if os.path.exists("../Binaries/Win64/Fly5.exe"):
            print("Launching Game...")
            self.gameProcess = subprocess.Popen('cd ..\\Binaries\\Win64 && start Fly5.exe -log', cwd='.', shell=True)

    def setEntry(self, entry, text):
        entry.delete(0, END)
        entry.insert(0, text)

    def is_numeric(self, string):
        try:
            float(string)
            return True
        except ValueError:
            return False