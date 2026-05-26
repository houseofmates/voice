"""system info — detect cpu, ram, gpu, vram on current and remote machines.

used by the smart model downloader to estimate which models will run well.
"""

import os
import sys
import subprocess
import json
import re


def get_cpu_info() -> dict:
    """detect cpu model, cores, threads."""
    info = {"model": "unknown", "cores": 0, "threads": 0}
    try:
        with open("/proc/cpuinfo") as f:
            text = f.read()
        # model name
        for line in text.split("\n"):
            if "model name" in line:
                info["model"] = line.split(":")[1].strip()
                break
        # count cores
        cores = set()
        for line in text.split("\n"):
            if "core id" in line:
                cid = line.split(":")[1].strip()
                if cid:
                    cores.add(cid)
        info["cores"] = len(cores) or os.cpu_count() or 0
        info["threads"] = os.cpu_count() or 0
    except Exception:
        info["cores"] = os.cpu_count() or 0
        info["threads"] = os.cpu_count() or 0
    return info


def get_ram_info() -> dict:
    """detect total and available ram in gb."""
    info = {"total_gb": 0, "available_gb": 0}
    try:
        with open("/proc/meminfo") as f:
            text = f.read()
        for line in text.split("\n"):
            if line.startswith("MemTotal:"):
                kb = int(line.split()[1])
                info["total_gb"] = round(kb / (1024 * 1024), 1)
            if line.startswith("MemAvailable:"):
                kb = int(line.split()[1])
                info["available_gb"] = round(kb / (1024 * 1024), 1)
    except Exception:
        pass
    return info


def get_gpu_info() -> dict:
    """detect gpu model and vram. tries nvidia-smi first, then torch."""
    info = {"model": "none detected", "vram_gb": 0, "driver": ""}

    # try nvidia-smi
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total,driver_version",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0 and result.stdout.strip():
            parts = result.stdout.strip().split("\n")[0].split(",")
            if len(parts) >= 2:
                info["model"] = parts[0].strip()
                info["vram_gb"] = round(int(parts[1].strip()) / 1024, 1)
            if len(parts) >= 3:
                info["driver"] = parts[2].strip()
            return info
    except Exception:
        pass

    # try nvidia-ml-py or torch
    try:
        import torch
        if torch.cuda.is_available():
            info["model"] = torch.cuda.get_device_name(0)
            info["vram_gb"] = round(torch.cuda.get_device_properties(0).total_memory / (1024**3), 1)
            return info
    except Exception:
        pass

    try:
        # rocm-smi for amd gpus
        result = subprocess.run(
            ["rocm-smi", "--showmeminfo", "vram"],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0:
            for line in result.stdout.split("\n"):
                if "VRAM Size" in line or "Total Memory" in line:
                    match = re.search(r"([\d.]+)\s*(GB|MB)", line)
                    if match:
                        val = float(match.group(1))
                        if match.group(2) == "MB":
                            val /= 1024
                        info["vram_gb"] = round(val, 1)
                        info["model"] = "amd gpu"
                        return info
    except Exception:
        pass

    # try lspci for amd/intel integrated gpus
    try:
        result = subprocess.run(
            ["lspci"], capture_output=True, text=True, timeout=5,
        )
        for line in result.stdout.split("\n"):
            if "VGA" in line or "3D" in line or "Display" in line:
                if "AMD" in line or "ATI" in line or "Radeon" in line:
                    # strip pci address and hex suffix
                    parts = line.split(":")
                    if len(parts) >= 3:
                        name = ":".join(parts[2:]).strip()
                        # remove trailing hex revision
                        name = re.sub(r'\s*\(rev\s+\w+\)', '', name)
                        info["model"] = name.strip()
                        # igpus share system ram — report as shared
                        try:
                            with open("/proc/meminfo") as f:
                                for l in f:
                                    if l.startswith("MemTotal:"):
                                        kb = int(l.split()[1])
                                        info["vram_gb"] = round(kb / (1024 * 1024), 1)
                                        info["driver"] = "shared (system ram)"
                                        break
                        except: pass
                        return info
                elif "Intel" in line and "HD Graphics" in line:
                    parts = line.split(":")
                    if len(parts) >= 3:
                        name = ":".join(parts[2:]).strip()
                        name = re.sub(r'\s*\(rev\s+\w+\)', '', name)
                        info["model"] = name.strip()
                        info["vram_gb"] = 0
                        info["driver"] = "shared (system ram)"
                        return info
    except Exception:
        pass

    return info


def get_os_info() -> dict:
    """detect os name and version."""
    info = {"name": "unknown", "version": ""}
    try:
        # try /etc/os-release first
        if os.path.exists("/etc/os-release"):
            with open("/etc/os-release") as f:
                for line in f:
                    if line.startswith("PRETTY_NAME="):
                        val = line.split("=", 1)[1].strip().strip('"')
                        info["name"] = val
                        break
        # also try lsb_release
        result = subprocess.run(
            ["lsb_release", "-ds"], capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            info["name"] = result.stdout.strip()
    except Exception:
        pass
    return info


def get_full_system_info() -> dict:
    """return all system info as a single dict."""
    return {
        "cpu": get_cpu_info(),
        "ram": get_ram_info(),
        "gpu": get_gpu_info(),
        "os": get_os_info(),
        "hostname": os.uname().nodename,
    }


def get_remote_system_info(host: str = "192.168.4.250", user: str = "house") -> dict:
    """ssh to a remote machine and get its system info.
    writes a temp script to avoid shell escaping issues.
    returns a dict with the same structure as get_full_system_info(),
    or an error dict if ssh fails.
    """
    import tempfile, uuid
    script = r'''
import json, os, subprocess, re
info = {"cpu": {"model":"unknown","cores":0,"threads":0}, "ram":{"total_gb":0,"available_gb":0},"gpu":{"model":"none detected","vram_gb":0,"driver":""},"os":{"name":"unknown","version":""},"hostname":"unknown"}
info["hostname"] = os.uname().nodename
try:
    with open("/proc/cpuinfo") as f:
        t = f.read()
    for line in t.split("\n"):
        if "model name" in line:
            info["cpu"]["model"] = line.split(":")[1].strip()
            break
    cores = set()
    for line in t.split("\n"):
        if "core id" in line:
            cid = line.split(":")[1].strip()
            if cid: cores.add(cid)
    info["cpu"]["cores"] = len(cores) or (os.cpu_count() or 0)
    info["cpu"]["threads"] = os.cpu_count() or 0
except: pass
try:
    with open("/proc/meminfo") as f:
        t = f.read()
    for line in t.split("\n"):
        if line.startswith("MemTotal:"): info["ram"]["total_gb"] = round(int(line.split()[1])/(1024*1024),1)
        if line.startswith("MemAvailable:"): info["ram"]["available_gb"] = round(int(line.split()[1])/(1024*1024),1)
except: pass
try:
    r = subprocess.run(["nvidia-smi","--query-gpu=name,memory.total","--format=csv,noheader,nounits"],capture_output=True,text=True,timeout=10)
    if r.returncode==0 and r.stdout.strip():
        parts = r.stdout.strip().split("\n")[0].split(",")
        if len(parts)>=2:
            info["gpu"]["model"] = parts[0].strip()
            info["gpu"]["vram_gb"] = round(int(parts[1].strip())/1024, 1)
except: pass
try:
    if os.path.exists("/etc/os-release"):
        with open("/etc/os-release") as f:
            for line in f:
                if line.startswith("PRETTY_NAME="):
                    info["os"]["name"] = line.split("=",1)[1].strip().strip(chr(34))
                    break
except: pass
print(json.dumps(info))
'''
    try:
        tag = uuid.uuid4().hex[:8]
        local_path = f"/tmp/voice_remote_check_{tag}.py"
        remote_path = f"/tmp/voice_remote_check_{tag}.py"
        with open(local_path, "w") as f:
            f.write(script)
        # scp to remote
        subprocess.run(
            ["scp", local_path, f"{user}@{host}:{remote_path}"],
            capture_output=True, text=True, timeout=10,
        )
        # run on remote
        result = subprocess.run(
            ["ssh", f"{user}@{host}", f"python3 {remote_path} && rm {remote_path}"],
            capture_output=True, text=True, timeout=15,
        )
        os.unlink(local_path)
        if result.returncode == 0 and result.stdout.strip():
            return json.loads(result.stdout.strip())
        return {"error": f"ssh failed: {result.stderr.strip()}"}
    except Exception as e:
        return {"error": str(e)}


def estimate_model_performance(system_info: dict) -> dict:
    """estimate which model qualities will run well on the given system.
    
    returns a dict with:
      - 'tier': 'low' | 'medium' | 'high' | 'ultra'
      - 'max_sample_rate': 24000 | 32000 | 40000 | 48000
      - 'recommended_f0': 'rmvpe' | 'fcpe' | 'crepe-tiny' | 'crepe'
      - 'max_channels': int
      - 'notes': str
    """
    vram = system_info.get("gpu", {}).get("vram_gb", 0)
    ram = system_info.get("ram", {}).get("total_gb", 0)
    cores = system_info.get("cpu", {}).get("threads", 0)
    gpu_model = system_info.get("gpu", {}).get("model", "").lower()

    # no gpu = cpu only = low performance
    if vram == 0 and "none" in gpu_model:
        if ram >= 32 and cores >= 8:
            return {
                "tier": "medium",
                "max_sample_rate": 32000,
                "recommended_f0": "fcpe",
                "max_channels": 1,
                "notes": "no gpu detected. using cpu — expect ~2-3x realtime. 32gb ram helps.",
            }
        return {
            "tier": "low",
            "max_sample_rate": 24000,
            "recommended_f0": "rmvpe",
            "max_channels": 1,
            "notes": "cpu-only mode. consider lightweight models and rmvpe f0.",
        }

    # gpu detected
    if vram >= 24:
        return {
            "tier": "ultra",
            "max_sample_rate": 48000,
            "recommended_f0": "crepe",
            "max_channels": 2,
            "notes": "plenty of vram. run any model at full quality.",
        }
    elif vram >= 12:
        return {
            "tier": "high",
            "max_sample_rate": 40000,
            "recommended_f0": "crepe-tiny",
            "max_channels": 2,
            "notes": "good vram. most models at 40k or 48k will work fine.",
        }
    elif vram >= 6:
        return {
            "tier": "medium",
            "max_sample_rate": 32000,
            "recommended_f0": "fcpe",
            "max_channels": 1,
            "notes": "6-8gb vram. stick to 32k models for real-time use.",
        }
    else:
        return {
            "tier": "low",
            "max_sample_rate": 24000,
            "recommended_f0": "rmvpe",
            "max_channels": 1,
            "notes": "limited vram. lightweight models at lower sample rates recommended.",
        }