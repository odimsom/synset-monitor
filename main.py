import os
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

app = FastAPI(title="SynsetMonitor")

# Configuración psutil
if os.environ.get("PROCFS_PATH"):
    psutil.PROCFS_PATH = os.environ.get("PROCFS_PATH")

ADMIN_USER = os.getenv("ADMIN_USER", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin")
JWT_SECRET = os.getenv("JWT_SECRET", "supersecretjwtkey_change_me")
ALGORITHM = "HS256"

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

@app.get("/metrics/system")
def get_system_metrics(authorized: bool = Depends(verify_token)):
    cpu = psutil.cpu_percent(interval=None)
    ram = psutil.virtual_memory()

    rootfs = os.environ.get("HOST_ROOTFS", "/")
    try:
        disk = psutil.disk_usage(rootfs)
    except Exception:
        disk = psutil.disk_usage("/")

    def to_gb(bytes_val):
        return round(bytes_val / (1024**3), 2)

    return {
        "cpu": {"usage": cpu},
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
        }
    }

@app.get("/metrics/docker")
def get_docker_metrics(authorized: bool = Depends(verify_token)):
    try:
        client = docker.from_env()
        containers = client.containers.list(all=True)
        res = []
        for c in containers:
            started_at = c.attrs.get('State', {}).get('StartedAt', '')
            tags = c.image.tags
            image_name = tags[0] if tags else c.image.id[:12]
            res.append({
                "name": c.name,
                "state": c.status,
                "image": image_name,
                "uptime": started_at
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
