from re import match as re_match
from robodk import *
import threading



def is_number_regex(s):
    """ Returns True if string is a number. """
    if re_match("^\d+?\.\d+?$", s) is None:
        return s.isdigit()

    return True


class RoboDKConnector:
    def __init__(self, robot_names_list, robots_info_dict, robodk_ip='localhost', port=None, args=[]):
        self.robot_names_list = robot_names_list
        self.RDK = robolink.Robolink(robodk_ip=robodk_ip, port=port, args=args)
        self.robots_info_dict = robots_info_dict
        self.lock = threading.Lock()
        self.stop_threads = False

    def update_robot_position(self, robot_name):
        try:
            robot = self.RDK.Item(name=robot_name)
            while not self.stop_threads:
                robot_joint_pose = robot.Pose()
                new_joint_pos = dict(joint_position=robot_joint_pose)

                # Acquisisce il lock prima di aggiornare il dizionario
                with self.lock:
                    self.robots_info_dict[robot_name] = new_joint_pos
        except Exception as e:
            print(f"An error occurred for {robot_name}: {e}")

    def update_positions(self):
        threads = []
        self.stop_threads = False
        for robot_name in self.robot_names_list:
            thread = threading.Thread(target=self.update_robot_position, args=(robot_name,))
            threads.append(thread)
            thread.start()
        """da valutare se serve o meno il thread.join()"""
        for thread in threads:
            thread.join()

    def stop_position_updating(self):
        self.stop_threads = True


    def call_main_proc(self):
        main_proc = self.RDK.Item('MainProg', robolink.ITEM_TYPE_PROGRAM)
        main_proc.RunProgram("MainProg()")

    def stop_robot(self, robot_name):

        # Ottieni il robot specifico dal nome
        robot = self.RDK.Item(robot_name, robolink.ITEM_TYPE_ROBOT)

        # Verifica se una procedura con il nome specificato è attualmente in esecuzione
        if robot.IsRunning():
            # Verifica se la procedura in esecuzione ha il nome specificato
            running_program_name = robot.ProgramName()
            if running_program_name == procedure_name:
                # Se la procedura in esecuzione ha il nome specificato, fermala
                robot.Stop()
                print(f"Procedura '{procedure_name}' fermata con successo.")
            else:
                print(f"Una procedura diversa '{running_program_name}' è in esecuzione.")
        else:
            print("Nessuna procedura in esecuzione.")


    def stop_main_program(self):

        # Verifica se la procedura principale "MainProg" è in esecuzione
        if self.RDK.Item('MainProg', robolink.ITEM_TYPE_PROGRAM).IsRunning():

            self.RDK.Item('MainProg', robolink.ITEM_TYPE_PROGRAM).Stop()

        else:
            print("La procedura 'MainProg' non è in esecuzione.")