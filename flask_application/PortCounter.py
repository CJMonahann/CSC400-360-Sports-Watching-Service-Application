class PortCounter:
    def __init__(self, port_num):
        self.port = port_num
    
    def get_port(self):
        return self.port
    
    def inc_port(self):
        self.port += 1