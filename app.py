from flask import Flask, render_template, jsonify
import psutil
import wmi
import pythoncom

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/stats')
def stats():
    # Nécessaire pour éviter les crashs avec WMI et Flask
    pythoncom.CoInitialize() 
    
    # On prépare le dictionnaire avec des valeurs par défaut (au cas où un capteur manque)
    data = {
        'temp': {'cpu': 0, 'gpu': 0, 'mb': 0, 'vrm': 0, 'sys': 0, 'ssds': [0, 0, 0, 0]},
        'usage': {'cpu': 0, 'ram': 0, 'gpu': 0, 'vram': 0, 'net': 0, 'ssds': [0, 0, 0, 0]}
    }

    # --- 1. LECTURE DES DONNÉES SYSTÈME (psutil) ---
    data['usage']['cpu'] = psutil.cpu_percent(interval=None)
    data['usage']['ram'] = psutil.virtual_memory().percent
    
    # Lecture de l'usage de tes 4 disques (3 SSD + 1 SATA)
    partitions = psutil.disk_partitions()
    disk_usages = []
    for p in partitions:
        # On ignore les lecteurs vides ou inaccessibles
        if 'cdrom' not in p.opts and p.fstype != '':
            try:
                disk_usages.append(psutil.disk_usage(p.mountpoint).percent)
            except PermissionError:
                pass
                
    # On s'assure d'avoir 4 valeurs pour l'interface
    while len(disk_usages) < 4: disk_usages.append(0)
    data['usage']['ssds'] = disk_usages[:4]

    # --- 2. LECTURE DES TEMPÉRATURES & GPU AMD (Open Hardware Monitor) ---
    try:
        # On se connecte au logiciel Open Hardware Monitor
        w = wmi.WMI(namespace="root\\OpenHardwareMonitor")
        hw_sensors = w.Sensor()
        
        ssd_temps = []
        
        for sensor in hw_sensors:
            name = sensor.Name.lower()
            sensor_type = sensor.SensorType.lower()
            value = int(sensor.Value)
            
            # --- TEMPÉRATURES ---
            if sensor_type == 'temperature':
                if 'cpu core' in name or 'cpu package' in name:
                    data['temp']['cpu'] = value
                elif 'gpu core' in name:
                    data['temp']['gpu'] = value
                # Capte les disques durs / SSD / NVMe
                elif 'temperature' in name and sensor.Parent.lower().find('hdd') != -1 or 'nvme' in sensor.Parent.lower():
                     ssd_temps.append(value)
            
            # --- USAGE (LOAD) ---
            if sensor_type == 'load':
                if 'gpu core' in name:
                    data['usage']['gpu'] = value
                elif 'gpu memory' in name:
                    data['usage']['vram'] = value

        # On s'assure d'avoir 4 valeurs de température pour tes disques
        while len(ssd_temps) < 4: ssd_temps.append(0)
        data['temp']['ssds'] = ssd_temps[:4]
        
    except Exception as e:
        print("Erreur : Assure-toi qu'Open Hardware Monitor est lancé !", e)

    return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True, port=5000)