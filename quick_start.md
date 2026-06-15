# Environment Bootstrap Protocol

## 1. Compute Node Provisioning (Kaggle Tensor Accelerators)

Execute the following POSIX-compliant bootstrap sequence within the target accelerator environment to allocate the necessary GPU buffers and inject the underlying compression binaries.

### Dependency Injection
```bash
!apt-get update && apt-get install -y zstd
```

### Binary Resolution and Expansion
```bash
!curl -fsSL https://ollama.com/download/ollama-linux-amd64.tar.zst -o ollama.tar.zst
!tar -xvf ollama.tar.zst -C /usr
!ollama --version
```

### Daemon Initialization via Subprocess Orchestration
Execute the following wrapper to daemonize the inference server and detach it from the main execution thread, binding it to the wildcard interface:
```python
import subprocess, os, time

env = os.environ.copy()
env["OLLAMA_MODELS"] = "/kaggle/working/ollama_models"
env["OLLAMA_HOST"] = "0.0.0.0"

log = open("ollama.log", "w")
process = subprocess.Popen(
    ["/usr/bin/ollama", "serve"],
    env=env, stdout=log, stderr=log
)

time.sleep(5)  # block until daemon binding completes
print(f"Inference daemon instantiated — PID: {process.pid}")
```

### Weights Acquisition
```bash
!OLLAMA_HOST=0.0.0.0 ollama pull qwen3:8b
```

### Ingress Topology via Port Forwarding
```bash
!npm install -g localtunnel
!lt --port 11434
```

Persist the generated ingress endpoint URL into your environment variables (`.env` file) as the `base_url` proxy target.

---

## 2. Application Cluster Boot Sequence

Initialize the segregated client and server processes via your local interactive shell. Ensure your current working directory resolves to the repository root.

First, resolve all requisite Python packages to establish the runtime environment:
```bash
pip install -r requirements.txt
```

Instantiate Inference Layer:
```bash
cd my_deepseek
python app/server/server.py
```

Instantiate Presentation Layer:
```bash
cd my_deepseek
python app/client/client.py
```

*(Note: Depending on your system's Python alias configuration, `python3` may be required to execute the AST compiler.)*

---

## 3. Subsystem Verification

Navigate your standard web client to the view-controller's loopback interface:
[http://127.0.0.1:5001/chat/new](http://127.0.0.1:5001/chat/new) to validate the end-to-end handshake.