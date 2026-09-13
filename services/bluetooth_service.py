import os
import sys
import subprocess
import threading
import winreg

class BluetoothService:
    def __init__(self):
        self._cached_status = None
        self._last_check = 0

    def get_bluetooth_name(self):
        """Retrieves the active Bluetooth broadcast name (Local Name or Machine Name)."""
        try:
            # Check Registry for customized BTHPORT Local Name
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Services\BTHPORT\Parameters") as key:
                val, _ = winreg.QueryValueEx(key, "Local Name")
                if val and str(val).strip():
                    return str(val).strip()
        except Exception:
            pass
        return os.environ.get("COMPUTERNAME", "HomeTheaterX-PC")

    def set_bluetooth_name(self, new_name):
        """Sets the Bluetooth Local Name in Windows Registry."""
        if not new_name or not new_name.strip():
            return {"status": "error", "message": "Bluetooth name cannot be empty"}

        clean_name = new_name.strip()
        try:
            # Write to BTHPORT Parameters
            key_path = r"SYSTEM\CurrentControlSet\Services\BTHPORT\Parameters"
            with winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
                winreg.SetValueEx(key, "Local Name", 0, winreg.REG_SZ, clean_name)

            return {
                "status": "success",
                "name": clean_name,
                "message": f"Bluetooth name set to '{clean_name}'. Note: Toggle Windows Bluetooth off/on for changes to take effect."
            }
        except PermissionError:
            return {
                "status": "error",
                "message": "Administrator privileges required to change Windows Bluetooth name."
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def open_bluetooth_settings(self):
        """Opens the native Windows 10/11 Bluetooth & Devices settings page."""
        try:
            os.system("start ms-settings:bluetooth")
            return {"status": "success", "message": "Windows Bluetooth settings opened."}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def get_bluetooth_status(self):
        """Queries Bluetooth adapter state and paired audio/mobile devices."""
        bt_name = self.get_bluetooth_name()
        
        devices = []
        is_available = True
        
        try:
            # Query active Bluetooth devices via PowerShell
            ps_cmd = (
                "Get-PnpDevice -Class Bluetooth -Status OK -ErrorAction SilentlyContinue | "
                "Where-Object { $_.FriendlyName -notmatch 'Enumerator|Adapter|RFCOMM|Transport|Intel|Realtek' } | "
                "Select-Object -Property FriendlyName, InstanceId | "
                "ConvertTo-Json -Compress"
            )
            
            creation_flags = 0
            if sys.platform.startswith("win"):
                creation_flags = 0x08000000 # CREATE_NO_WINDOW
                
            res = subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps_cmd],
                capture_output=True,
                text=True,
                timeout=4,
                creationflags=creation_flags
            )
            
            if res.stdout and res.stdout.strip():
                import json
                parsed = json.loads(res.stdout.strip())
                if isinstance(parsed, dict):
                    devices.append(parsed.get("FriendlyName", ""))
                elif isinstance(parsed, list):
                    for d in parsed:
                        name = d.get("FriendlyName", "")
                        if name and name not in devices:
                            devices.append(name)
        except Exception as e:
            print(f"[BluetoothService] Error querying devices: {e}")

        return {
            "status": "success",
            "bluetooth_name": bt_name,
            "is_available": is_available,
            "paired_devices": devices
        }

bluetooth_service = BluetoothService()
