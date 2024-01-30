import logging

class Logger:
    def __init__(self, to_console, to_file, is_active) -> None:
        self.toConsole = to_console
        self.toFile = to_file
        self.isActive = is_active

        if self.isActive and self.toFile:
            logging.basicConfig(filename="server_log",
                    filemode='a',
                    format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.DEBUG)
            
    def log(self, text):
        if not self.isActive:
            return

        if self.toConsole:
            print(text)
        if self.toFile:
            logging.info(text)