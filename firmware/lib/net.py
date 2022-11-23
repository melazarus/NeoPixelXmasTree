from network import WLAN, STA_IF, STAT_WRONG_PASSWORD, STAT_CONNECTING ,STAT_NO_AP_FOUND
import time

def connect(config, progress_callback=None):
    
    def log(progress_pct, msg, severity = "info"):
        if progress_callback: progress_callback(progress_pct, msg, severity)
        else: print(progress_pct, severity, msg)
    
    net = WLAN(STA_IF)
    net.active(True)
    net.disconnect()

    #1 scan for existing networks
    log(5, "scanning")
    existing_networks = [x[0].decode() for x in net.scan() if len(x[0]) > 0]
    log(12, "found: " + ", ".join(existing_networks))
    
    #2 get network that has a configuration entry
    matching_networks = [x.lower() for x in existing_networks if  x.lower() in [y["ssid"].lower() for y in config["networks"]]]
    log(25, "matches:" + ", ".join(matching_networks))
    
    #3 get corresponding network
    configurations = [x for x in config["networks"] if x["hidden"] == True or x["ssid"].lower() in matching_networks]

    for c in sorted(configurations, key=lambda x:(x["hidden"], x["prio"])):
        log(50, "connecting to " + c["ssid"])
        name = c["ssid"]
        pwd = c["password"]
        net.connect(name, pwd)
        for i in range(config["connect_timeout"]):
            time.sleep(1)
            if net.isconnected(): break
            if net.status() == STAT_WRONG_PASSWORD:
                log(75, "wrong password", "error")
                break
            if net.status() == STAT_NO_AP_FOUND:
                log(75, "AP not found", "error")
                break
        if net.isconnected():
            log(100, "connected to " + name + " " + net.ifconfig()[0])
            return net
    if not net.isconnected():
        log(0, "restarting", "error")
        import machine
        machine.reset()
    


