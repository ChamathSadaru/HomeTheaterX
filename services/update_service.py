import os
import sys
import json
import time
import re
import tempfile
import threading
import subprocess
import urllib.request
import urllib.error
import ssl

CURRENT_VERSION = "2.0.0"
GITHUB_REPO = "ChamathSadaru/HomeTheaterX-V2"

class UpdateManager:
    def __init__(self, repo=GITHUB_REPO, current_version=CURRENT_VERSION):
        self.repo = repo
        self.current_version = current_version
        self.lock = threading.Lock()
        self.download_thread = None
        self._cancel_flag = False
        
        self.state = {
            "status": "idle",  # idle, checking, downloading, downloaded, installing, error
            "progress": 0,      # 0 - 100
            "speed_mbps": 0.0,
            "downloaded_bytes": 0,
            "total_bytes": 0,
            "error_msg": None,
            "installer_path": None,
            "latest_release": None
        }

    def parse_version(self, version_str):
        """Converts strings like 'v2.1.0' or '2.0' into a comparable tuple of ints: (2, 1, 0)."""
        if not version_str:
            return (0, 0, 0)
        clean = version_str.strip().lstrip("vV")
        parts = re.findall(r'\d+', clean)
        if not parts:
            return (0, 0, 0)
        nums = [int(p) for p in parts[:3]]
        while len(nums) < 3:
            nums.append(0)
        return tuple(nums)

    def is_newer(self, latest_str, current_str):
        """Returns True if latest_str is strictly newer than current_str."""
        return self.parse_version(latest_str) > self.parse_version(current_str)

    def check_for_updates(self):
        """Queries GitHub Releases API for the latest release metadata."""
        api_url = f"https://api.github.com/repos/{self.repo}/releases/latest"
        headers = {
            "User-Agent": f"HomeTheaterX-Updater/{self.current_version}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        req = urllib.request.Request(api_url, headers=headers)
        context = ssl.create_default_context()
        
        try:
            with urllib.request.urlopen(req, timeout=10, context=context) as response:
                if response.status != 200:
                    return {
                        "has_update": False,
                        "error": f"GitHub API returned status {response.status}"
                    }
                data = json.loads(response.read().decode("utf-8"))

            tag_name = data.get("tag_name", "")
            release_name = data.get("name") or tag_name
            release_notes = data.get("body", "")
            html_url = data.get("html_url", "")
            published_at = data.get("published_at", "")
            
            # Locate suitable Windows setup asset (.exe)
            assets = data.get("assets", [])
            download_url = None
            asset_name = None
            asset_size = 0
            
            for asset in assets:
                name = asset.get("name", "")
                if name.lower().endswith(".exe"):
                    download_url = asset.get("browser_download_url")
                    asset_name = name
                    asset_size = asset.get("size", 0)
                    if "setup" in name.lower() or "allinone" in name.lower():
                        break
            
            has_update = self.is_newer(tag_name, self.current_version)
            
            release_info = {
                "has_update": has_update,
                "current_version": self.current_version,
                "latest_version": tag_name.lstrip("vV") if tag_name else self.current_version,
                "tag_name": tag_name,
                "release_name": release_name,
                "release_notes": release_notes,
                "release_url": html_url,
                "published_at": published_at,
                "download_url": download_url,
                "asset_name": asset_name,
                "asset_size": asset_size
            }
            
            with self.lock:
                self.state["latest_release"] = release_info
                
            return release_info

        except urllib.error.HTTPError as he:
            if he.code == 404:
                return {
                    "has_update": False,
                    "current_version": self.current_version,
                    "message": "No public releases published on GitHub repository yet."
                }
            return {
                "has_update": False,
                "current_version": self.current_version,
                "error": f"HTTP error {he.code}: {he.reason}"
            }
        except Exception as e:
            return {
                "has_update": False,
                "current_version": self.current_version,
                "error": str(e)
            }

    def start_download(self, download_url=None, progress_callback=None):
        """Starts background download of the installer."""
        with self.lock:
            if self.state["status"] == "downloading":
                return {"status": "error", "message": "Download is already in progress."}

            if not download_url:
                if self.state.get("latest_release") and self.state["latest_release"].get("download_url"):
                    download_url = self.state["latest_release"]["download_url"]
                else:
                    return {"status": "error", "message": "No download URL available. Please check for updates first."}

            self._cancel_flag = False
            self.state["status"] = "downloading"
            self.state["progress"] = 0
            self.state["speed_mbps"] = 0.0
            self.state["downloaded_bytes"] = 0
            self.state["total_bytes"] = 0
            self.state["error_msg"] = None
            self.state["installer_path"] = None

        def _worker():
            try:
                temp_dir = tempfile.gettempdir()
                filename = "HomeTheaterX_Update_Setup.exe"
                out_path = os.path.join(temp_dir, filename)

                req = urllib.request.Request(
                    download_url,
                    headers={"User-Agent": f"HomeTheaterX-Updater/{self.current_version}"}
                )
                context = ssl.create_default_context()

                with urllib.request.urlopen(req, timeout=30, context=context) as response:
                    total_size = int(response.headers.get("content-length", 0))
                    with self.lock:
                        self.state["total_bytes"] = total_size

                    chunk_size = 64 * 1024
                    downloaded = 0
                    start_time = time.time()
                    last_broadcast_time = start_time

                    with open(out_path, "wb") as f:
                        while True:
                            if self._cancel_flag:
                                with self.lock:
                                    self.state["status"] = "idle"
                                    self.state["error_msg"] = "Download cancelled by user"
                                return

                            chunk = response.read(chunk_size)
                            if not chunk:
                                break

                            f.write(chunk)
                            downloaded += len(chunk)

                            now = time.time()
                            elapsed = now - start_time
                            speed = (downloaded / (1024 * 1024)) / elapsed if elapsed > 0 else 0.0
                            progress = int((downloaded / total_size) * 100) if total_size > 0 else 0

                            if now - last_broadcast_time >= 0.25 or progress == 100:
                                last_broadcast_time = now
                                with self.lock:
                                    self.state["downloaded_bytes"] = downloaded
                                    self.state["progress"] = progress
                                    self.state["speed_mbps"] = round(speed, 2)
                                if progress_callback:
                                    try:
                                        progress_callback(dict(self.state))
                                    except Exception:
                                        pass

                with self.lock:
                    self.state["status"] = "downloaded"
                    self.state["progress"] = 100
                    self.state["installer_path"] = out_path

                if progress_callback:
                    try:
                        progress_callback(dict(self.state))
                    except Exception:
                        pass

            except Exception as e:
                with self.lock:
                    self.state["status"] = "error"
                    self.state["error_msg"] = str(e)
                if progress_callback:
                    try:
                        progress_callback(dict(self.state))
                    except Exception:
                        pass

        self.download_thread = threading.Thread(target=_worker, daemon=True)
        self.download_thread.start()
        return {"status": "started"}

    def apply_update_and_restart(self, silent=True):
        """Executes the downloaded installer and cleanly exits current process."""
        with self.lock:
            installer = self.state.get("installer_path")
            if not installer or not os.path.exists(installer):
                return {"status": "error", "message": "No downloaded installer file found."}

            self.state["status"] = "installing"

        try:
            flags = ["/SP-"]
            if silent:
                flags.extend(["/SILENT", "/CLOSEAPPLICATIONS", "/RESTARTAPPLICATIONS"])

            cmd = [installer] + flags

            def _launch_and_quit():
                time.sleep(1.0)
                creation_flags = 0
                if sys.platform.startswith("win"):
                    creation_flags = subprocess.CREATE_NEW_PROCESS_GROUP | 0x00000008 # DETACHED_PROCESS
                subprocess.Popen(cmd, creationflags=creation_flags)
                time.sleep(0.5)
                os._exit(0)

            threading.Thread(target=_launch_and_quit, daemon=True).start()
            return {"status": "installing", "message": "Update installer launched. Exiting HomeTheaterX..."}
        except Exception as e:
            with self.lock:
                self.state["status"] = "error"
                self.state["error_msg"] = str(e)
            return {"status": "error", "message": str(e)}

    def get_status(self):
        with self.lock:
            return dict(self.state)

update_manager = UpdateManager()
