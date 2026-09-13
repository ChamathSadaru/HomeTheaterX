import subprocess
import time

def _get_target_device_name(preferred_name=None):
    """Dynamically resolves the active audio device name without hardcoding."""
    if preferred_name:
        return preferred_name
    try:
        import config_manager
        saved = config_manager.get("last_device")
        if saved:
            return saved
    except Exception:
        pass
    try:
        from pycaw.pycaw import AudioUtilities
        speakers = AudioUtilities.GetSpeakers()
        if hasattr(speakers, "FriendlyName") and speakers.FriendlyName:
            return speakers.FriendlyName
    except Exception:
        pass
    return "Samsung Home Theater 5.1"


def _find_device_item(device_list, target_device_name):
    """Accurately locates the target audio device in the Sound Control Panel list."""
    clean_target = (target_device_name or "").split("(")[0].strip().lower()
    item_count = device_list.item_count()
    if item_count == 0:
        return None

    # 1. Exact or substring match with target name
    if clean_target:
        for idx in range(item_count):
            txt = device_list.get_item(idx).text().lower()
            if clean_target in txt or txt in clean_target:
                return idx

    # 2. Match common home theater keywords
    for idx in range(item_count):
        txt = device_list.get_item(idx).text().lower()
        if any(kw in txt for kw in ("samsung", "home theater", "5.1", "default")):
            return idx

    # 3. Default fallback: primary output device (index 0)
    return 0


def check_dolby_state(target_device_name=None):
    """
    Launches control mmsys.cpl, parses Sound Properties via pywinauto with
    dynamic polling retry loops, inspects the Dolby tab, and returns True if ON.
    """
    from pywinauto import Application
    
    device_name = _get_target_device_name(target_device_name)
    subprocess.Popen("control mmsys.cpl", shell=True)
    
    # Poll for Sound window
    app = None
    for _ in range(10):
        try:
            app = Application(backend="win32").connect(title="Sound", timeout=1)
            if app:
                break
        except Exception:
            time.sleep(0.3)
            
    if not app:
        print("[check_dolby_state] Could not connect to Sound window.")
        return False
        
    state = False
    sound_win = None
    prop_win = None
    try:
        sound_win = app.window(title="Sound")
        device_list = sound_win.child_window(class_name="SysListView32", control_id=1000)
        
        target_idx = _find_device_item(device_list, device_name)
        if target_idx is not None:
            device_list.get_item(target_idx).select()
            time.sleep(0.3)
            prop_btn = sound_win.child_window(title="&Properties", class_name="Button", control_id=1003)
            prop_btn.click()
            
            # Poll for Properties window
            prop_app = None
            for _ in range(10):
                try:
                    prop_app = Application(backend="win32").connect(title_re=".*Properties.*", timeout=1)
                    if prop_app:
                        break
                except Exception:
                    time.sleep(0.3)
                    
            if prop_app:
                prop_win = prop_app.window(title_re=".*Properties.*")
                tab_ctrl = prop_win.child_window(class_name="SysTabControl32")
                
                dolby_idx = None
                for t_idx in range(tab_ctrl.tab_count()):
                    if "Dolby" in tab_ctrl.get_tab_text(t_idx):
                        dolby_idx = t_idx
                        break
                        
                if dolby_idx is not None:
                    tab_ctrl.select(dolby_idx)
                    time.sleep(0.8)
                    
                    # Search descendant buttons for Dolby toggle
                    for child in prop_win.descendants():
                        if child.class_name() == "Button":
                            btn_text = child.window_text().upper()
                            if "DOLBY" in btn_text:
                                if btn_text.startswith("ON") or " ON" in btn_text:
                                    state = True
                                break
                                
                prop_win.close()
                prop_win = None
        sound_win.close()
        sound_win = None
    except Exception as e:
        print(f"[check_dolby_state] Error: {e}")
        if prop_win:
            try:
                prop_win.close()
            except Exception:
                pass
        if sound_win:
            try:
                sound_win.close()
            except Exception:
                pass
                
    return state


def toggle_dolby_in_system(target_device_name=None):
    """
    Automates clicking the Dolby Digital Plus button in the Sound Properties window
    to toggle Dolby Digital Live on/off for the active device.
    """
    from pywinauto import Application
    
    device_name = _get_target_device_name(target_device_name)
    subprocess.Popen("control mmsys.cpl", shell=True)
    
    app = None
    for _ in range(10):
        try:
            app = Application(backend="win32").connect(title="Sound", timeout=1)
            if app:
                break
        except Exception:
            time.sleep(0.3)
            
    if not app:
        return False, False

    success = False
    new_state = False
    sound_win = None
    prop_win = None
    try:
        sound_win = app.window(title="Sound")
        device_list = sound_win.child_window(class_name="SysListView32", control_id=1000)
        
        target_idx = _find_device_item(device_list, device_name)
        if target_idx is not None:
            device_list.get_item(target_idx).select()
            time.sleep(0.3)
            prop_btn = sound_win.child_window(title="&Properties", class_name="Button", control_id=1003)
            prop_btn.click()
            
            prop_app = None
            for _ in range(10):
                try:
                    prop_app = Application(backend="win32").connect(title_re=".*Properties.*", timeout=1)
                    if prop_app:
                        break
                except Exception:
                    time.sleep(0.3)
                    
            if prop_app:
                prop_win = prop_app.window(title_re=".*Properties.*")
                tab_ctrl = prop_win.child_window(class_name="SysTabControl32")
                
                dolby_idx = None
                for t_idx in range(tab_ctrl.tab_count()):
                    if "Dolby" in tab_ctrl.get_tab_text(t_idx):
                        dolby_idx = t_idx
                        break
                        
                if dolby_idx is not None:
                    tab_ctrl.select(dolby_idx)
                    time.sleep(0.8)
                    
                    dolby_btn = None
                    for child in prop_win.descendants():
                        if child.class_name() == "Button" and "DOLBY" in child.window_text().upper():
                            dolby_btn = child
                            break
                            
                    if dolby_btn:
                        dolby_btn.click()
                        time.sleep(0.5)
                        
                        new_text = dolby_btn.window_text().upper()
                        new_state = new_text.startswith("ON") or " ON" in new_text
                        
                        try:
                            apply_btn = prop_win.child_window(title="&Apply", class_name="Button")
                            if apply_btn.is_enabled():
                                apply_btn.click()
                                time.sleep(0.4)
                        except Exception:
                            pass
                            
                        try:
                            ok_btn = prop_win.child_window(title="OK", class_name="Button")
                            ok_btn.click()
                        except Exception:
                            prop_win.close()
                            
                        prop_win = None
                        success = True
                else:
                    prop_win.close()
                    prop_win = None
        sound_win.close()
        sound_win = None
    except Exception as e:
        print(f"[toggle_dolby_in_system] Error: {e}")
        if prop_win:
            try:
                prop_win.close()
            except Exception:
                pass
        if sound_win:
            try:
                sound_win.close()
            except Exception:
                pass
                
    return success, new_state


def async_check_dolby(on_complete_callback, target_device_name=None):
    """
    Runs check_dolby_state on a background thread with COM initialized,
    triggering the provided callback with the result.
    """
    import threading
    def _run():
        try:
            import comtypes
            comtypes.CoInitialize()
            state = check_dolby_state(target_device_name)
            if on_complete_callback:
                on_complete_callback(state)
            comtypes.CoUninitialize()
        except Exception as e:
            print(f"Error checking Dolby in background thread: {e}")

    threading.Thread(target=_run, daemon=True).start()

