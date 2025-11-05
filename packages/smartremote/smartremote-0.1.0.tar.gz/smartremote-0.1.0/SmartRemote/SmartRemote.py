import zmq, time 

class SmartRemote: 
    address = "tcp://localhost:5581"    
    rpcid = 1 
    jsonrpc_version = "2.0"
    method = None
    params = None 
    zmq_type = zmq.REQ
    context = None
    socket = None

    method_dic = {"send_script" : "js_cmd",
                  "check_status" : "js_run", 
                  "check_connection" : "js_connect",
                  "query_position": "pos_query", 
                  "query_scan_status": "scan_query", 
                  "query_geometry": "geometry_query"}

    def __init__(self): 
        self.connect_socket() 

    def connect_socket(self): 
        self.context = zmq.Context() 
        self.socket = self.context.socket(self.zmq_type) 
        self.socket.connect(self.address) 

    def generate_payload(self):
        payload = {
            "jsonrpc" : self.jsonrpc_version, 
            "method" : self.method, 
            "params" : self.params, 
            "id" : self.rpcid
        }

        return payload 
    
    def request(self): 
        payload = self.generate_payload() 
        self.socket.send_json(payload)         

        return self.socket.recv_json() 
    
    def set_method(self, method): 
        self.method = method 

    def set_params(self, params): 
        self.params = params 

    def check_connection(self): 
        self.set_method(self.method_dic["check_connection"])
        self.set_params("None") 
        reply = self.request()   

        return reply["result"]
    
    def check_status(self): 
        self.set_method(self.method_dic["check_status"])
        self.set_params("None") 
        reply = self.request() 

        return reply["result"]
    
    def query_stage_pos(self): 
        self.set_method(self.method_dic["query_position"])
        self.set_params("None") 
        reply = self.request() 
        pos = reply["result"].split(',')

        return {"x": float(pos[0]), "y": float(pos[1]), "z": float(pos[2])}
    
    def query_scan_status(self): 
        self.set_method(self.method_dic["query_scan_status"])
        self.set_params("None") 
        reply = self.request() 
        scan_status = reply["result"]

        return scan_status
    
    def query_geometry(self): 
        self.set_method(self.method_dic["query_geometry"])
        self.set_params("None") 
        reply = self.request() 
        g = reply["result"].split(',')

        return {"pixelHeight": int(g[0]), "pixelWidth": int(g[1]), "width": float(g[2]), 
                "height": float(g[3]), "offsetX": float(g[4]), "offsetY": float(g[5]), "rotation": float(g[6])}        

    def send_script(self, script): 
        self.set_method(self.method_dic["send_script"])
        self.set_params(script) 
        reply = self.request() 

        return reply
    
    def is_script_finished(self): 
        while True: 
            time.sleep(0.3)
            reply = self.check_status() 
            if reply == "false": 
                break 
        
        return "Done"

    def run(self, script): 
        reply = self.send_script(script) 
        result = reply["result"]
        value = reply["value"]
        finished = self.is_script_finished() 

        return {"result": result, "value": value}   
    