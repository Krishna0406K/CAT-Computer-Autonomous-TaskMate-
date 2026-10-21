import os
import time

def open_local_app(target: str) -> str:
    """
    Opens a local application, folder, or drive on the Windows computer.
    Examples: open_local_app('D:\\'), open_local_app('whatsapp'), open_local_app('calculator')
    """
    target_clean = target.strip().lower()
    
    # 1. Handle explicit drives and paths
    if target_clean in ["d", "d:", "d drive", "d drive.", "d:\\", "open d drive"]:
        try:
            os.startfile("D:\\")
            return "Successfully opened D: drive."
        except Exception as e:
            return f"Error opening D: drive: {str(e)}"
            
    if target_clean in ["c", "c:", "c drive", "c:\\", "open c drive"]:
        try:
            os.startfile("C:\\")
            return "Successfully opened C: drive."
        except Exception as e:
            return f"Error opening C: drive: {str(e)}"
            
    # 2. Handle common Windows URIs and Executables
    app_map = {
        "whatsapp": "whatsapp:",
        "spotify": "spotify:",
        "calculator": "calc",
        "calc": "calc",
        "notepad": "notepad",
        "word": "winword",
        "excel": "excel",
        "powerpoint": "powerpnt",
        "cmd": "cmd",
        "terminal": "wt",
        "settings": "ms-settings:"
    }
    
    for key, cmd in app_map.items():
        if key in target_clean:
            try:
                os.startfile(cmd)
                return f"Successfully opened {key} native application."
            except Exception:
                pass # Fallback to start menu search if it fails
                
    # 3. Fallback: Use Windows Search via PyAutoGUI (Extremely reliable for arbitrary apps)
    try:
        import pyautogui
        pyautogui.press('win')
        time.sleep(0.5)
        pyautogui.write(target, interval=0.02)
        time.sleep(0.8) # Wait for Windows search to populate the best match
        pyautogui.press('enter')
        return f"Successfully searched and launched '{target}' via Windows Start Menu."
    except Exception as e:
        return f"Error opening application: {str(e)}"
