class Data:
    # robot types
    ROBOT_TYPES  = ["0: Staubli (SRS)", "1: Universal Robot - UR", "2: FANUC", "3: KUKA - KK"] # NB: do not touch indexes before text!
    ROBOT_TYPE = ROBOT_TYPES[0]

    # UDP parameters PLC - Python
    UDP_HOST        = "127.0.0.1"
    UDP_PORT        = 8010
    UDP_PACKET_SIZE = 1024
    # RTDE parameters
    DEFAULT_RTDE_PORT = 30004
    DEFAULT_RTDE_SAMPLES = 0
    DEFAULT_RTDE_FREQUENCY = 125
    DEFAULT_RTDE_CONFIG_FILE = "data_config.xml"
    # FANUC parameters
    DEFAULT_FANUC_CONTROLLER_PORT = 187358
    #KUKA parameters
    DEFAULT_KUKA_CONTROLLER_PORT = 808080

    # TCP parameters: Python - Unreal
    TCP_HOST        = "127.0.0.1"
    TCP_PORT        = 1012
    TCP_PACKET_SIZE = 1024

    # number of axis to manage
    JOINTS_OPTIONS  = [4, 6]

    # Data exchange variables
    J_COUNT        = JOINTS_OPTIONS[0]   # analog (PLC) outputs: actual joints poisition (robot -> py -> UE)
    AO_COUNT       = J_COUNT             # analog (PLC) outputs: spares (robot -> py -> UE)
    AI_COUNT       = J_COUNT             # analog (PLC) inputs : only spares (UE -> py -> robot)
    DO_COUNT       = 15                  # output digital (robot -> py -> UE)
    DI_COUNT       = 15                  # input digital (UE -> py -> robot)

    # true if you want to simulate locally a fixed pose
    IS_DEBUG        = False

    # true if robot connection is enabled
    IS_ACTIVE       = True 