import os
import time
import psutil
import docker
from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import FileResponse
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
import jwt
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

__version__ = "1.3.0"

app = FastAPI(title="SynsetMonitor", version=__version__)

# Configuración psutil
if os.environ.get("PROCFS_PATH"):
    psutil.PROCFS_PATH = os.environ.get("PROCFS_PATH")

ADMIN_USER = os.getenv("ADMIN_USER", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin")
JWT_SECRET = os.getenv("JWT_SECRET", "supersecretjwtkey_change_me")
ALGORITHM = "HS256"

TARGET_SERVICES = os.getenv("TARGET_SERVICES", "http://localhost:8000/").split(",")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

class LoginData(BaseModel):
    username: str
    password: str

def verify_token(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
        if payload.get("sub") != ADMIN_USER:
            raise HTTPException(status_code=401, detail="Usuario inválido")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")
    return True

@app.post("/auth/login")
def login(data: LoginData):
    if data.username == ADMIN_USER and data.password == ADMIN_PASSWORD:
        expiration = datetime.utcnow() + timedelta(hours=24)
        token = jwt.encode({"sub": data.username, "exp": expiration}, JWT_SECRET, algorithm=ALGORITHM)
        return {"access_token": token, "token_type": "bearer"}
    raise HTTPException(status_code=401, detail="Credenciales incorrectas")

import urllib.request
import urllib.error

@app.get("/metrics/health")
def get_healthchecks(authorized: bool = Depends(verify_token)):
    results = []
    for url in TARGET_SERVICES:
        url = url.strip()
        if not url: continue
        try:
            start = time.time()
            req = urllib.request.Request(url, headers={'User-Agent': 'SynsetMonitor/1.3'})
            with urllib.request.urlopen(req, timeout=3) as response:
                elapsed = round((time.time() - start) * 1000)
                results.append({"url": url, "status": str(response.getcode()), "latency_ms": elapsed})
        except urllib.error.HTTPError as e:
            elapsed = round((time.time() - start) * 1000)
            results.append({"url": url, "status": str(e.code), "latency_ms": elapsed})
        except Exception as e:
            results.append({"url": url, "status": "Down", "latency_ms": 0})
    return results

@app.get("/metrics/system")
def get_system_metrics(authorized: bool = Depends(verify_token)):
    cpu = psutil.cpu_percent(interval=None)
    ram = psutil.virtual_memory()

    rootfs = os.environ.get("HOST_ROOTFS", "/")
    try:
        disk = psutil.disk_usage(rootfs)
    except Exception:
        disk = psutil.disk_usage("/")

    # Uptime
    uptime_seconds = time.time() - psutil.boot_time()

    # Temps
    temp_c = None
    if hasattr(psutil, "sensors_temperatures"):
        try:
            temps = psutil.sensors_temperatures()
            if temps:
                first_sensor = list(temps.values())[0]
                if first_sensor:
                    temp_c = round(first_sensor[0].current, 1)
        except Exception:
            pass

    # Load Avg
    try:
        if hasattr(psutil, "getloadavg"):
            load_avg = [round(x, 2) for x in psutil.getloadavg()]
        else:
            load_avg = [round(x, 2) for x in os.getloadavg()]
    except Exception:
        load_avg = [0.0, 0.0, 0.0]

    # Procs count
    active_procs = len(psutil.pids())

    # Network
    net = psutil.net_io_counters()

    # TCP Connections
    tcp_states = {}
    try:
        conns = psutil.net_connections(kind='tcp')
        for c in conns:
            st = str(c.status)
            tcp_states[st] = tcp_states.get(st, 0) + 1
    except Exception:
        pass
    
    # Disk IO
    disk_io_info = None
    try:
        d = psutil.disk_io_counters()
        if d:
            disk_io_info = {
                "rcount": getattr(d, 'read_count', 0),
                "wcount": getattr(d, 'write_count', 0),
                "rbytes": getattr(d, 'read_bytes', 0),
                "wbytes": getattr(d, 'write_bytes', 0),
                "rtime": getattr(d, 'read_time', 0),
                "wtime": getattr(d, 'write_time', 0)
            }
    except Exception:
        pass

    # Top processes
    procs = []
    for p in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
        try:
            procs.append(p.info)
        except Exception:
            pass
            
    # Sort by cpu usage roughly
    top_cpu = sorted(procs, key=lambda x: x.get('cpu_percent') or 0, reverse=True)[:5]
    for p in top_cpu:
        p['cpu_percent'] = round(p.get('cpu_percent') or 0, 1)
        p['memory_percent'] = round(p.get('memory_percent') or 0, 1)

    # v1.1.0 Deep System Metrics
    iowait = 0.0
    val_steal = 0.0
    if hasattr(psutil, "cpu_times_percent"):
        try:
            cput = psutil.cpu_times_percent(interval=None)
            iowait = getattr(cput, "iowait", 0.0)
            val_steal = getattr(cput, "steal", 0.0)
        except Exception:
            pass

    try:
        swap = psutil.swap_memory()
        swap_info = {
            "total": round(swap.total / (1024**3), 2),
            "used": round(swap.used / (1024**3), 2),
            "percent": swap.percent,
            "sin": getattr(swap, "sin", 0),
            "sout": getattr(swap, "sout", 0)
        }
    except Exception:
        swap_info = {"total": 0, "used": 0, "percent": 0, "sin": 0, "sout": 0}

    def to_gb(bytes_val):
        return round(bytes_val / (1024**3), 2)

    return {
        "cpu": {"usage": cpu, "temp": temp_c, "iowait": iowait, "steal": val_steal},
        "swap": swap_info,
        "ram": {
            "total": to_gb(ram.total),
            "used": to_gb(ram.used),
            "available": to_gb(ram.available),
            "percent": ram.percent
        },
        "disk": {
            "total": to_gb(disk.total),
            "used": to_gb(disk.used),
            "free": to_gb(disk.free),
            "percent": disk.percent
        },
        "disk_io": disk_io_info,
        "uptime": uptime_seconds,
        "load_avg": load_avg,
        "procs_count": active_procs,
        "network": {
            "bytes_sent": net.bytes_sent,
            "bytes_recv": net.bytes_recv,
            "errin": getattr(net, 'errin', 0),
            "errout": getattr(net, 'errout', 0),
            "dropin": getattr(net, 'dropin', 0),
            "dropout": getattr(net, 'dropout', 0),
            "tcp": tcp_states
        },
        "top_procs": top_cpu
    }

@app.get("/metrics/docker")
def get_docker_metrics(authorized: bool = Depends(verify_token)):
    try:
        client = docker.from_env()
        containers = client.containers.list(all=True)
        res = []
        for c in containers:
            started_at = c.attrs.get('State', {}).get('StartedAt', '')
            restarts = c.attrs.get('RestartCount', 0)
            tags = c.image.tags
            image_name = tags[0] if tags else c.image.id[:12]
            
            # Extract ports
            ports_str = ""
            ports_info = c.attrs.get('NetworkSettings', {}).get('Ports', {})
            if ports_info:
                mappings = []
                for p, maps in ports_info.items():
                    if maps:
                        for m in maps:
                            host_port = m.get('HostPort', '')
                            if host_port:
                                mappings.append(f"{host_port}->{p}")
                if mappings:
                    ports_str = ", ".join(mappings)
            
            res.append({
                "name": c.name,
                "state": c.status,
                "restarts": restarts,
                "image": image_name,
                "uptime": started_at,
                "ports": ports_str or "Ninguno"
            })
        return res
    except Exception as e:
        return {"error": str(e)}

@app.get("/metrics/logs")
def get_logs(authorized: bool = Depends(verify_token)):
    log_dir = os.environ.get("HOST_LOG_DIR", "/var/log")
    log_files = ["syslog", "messages"]
    lines = []
    
    for lf in log_files:
        file_path = os.path.join(log_dir, lf)
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    all_lines = f.readlines()
                    lines = [line.strip() for line in all_lines[-50:]]
            except Exception as e:
                lines.append(f"Error leyendo {file_path}: {e}")
            break
            
    if not lines:
        lines = ["No se encontró archivo syslog o messages en el directorio de logs."]
        
    return lines

@app.get("/")
def serve_index():
    return FileResponse("static/index.html")
