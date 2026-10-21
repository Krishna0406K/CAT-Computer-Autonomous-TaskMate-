import pyautogui

def media_control(action: str) -> str:
    """
    Controls media playback. 
    Valid actions: 'playpause', 'nexttrack', 'prevtrack', 'volumemute', 'volumeup', 'volumedown'
    """
    valid_actions = ['playpause', 'nexttrack', 'prevtrack', 'volumemute', 'volumeup', 'volumedown']
    
    action = action.lower().strip()
    if action == 'play' or action == 'pause':
        action = 'playpause'
    elif action == 'next' or action == 'skip':
        action = 'nexttrack'
    elif action == 'prev' or action == 'previous' or action == 'back':
        action = 'prevtrack'
    elif action == 'mute':
        action = 'volumemute'
        
    if action not in valid_actions:
        return f"Error: Invalid action '{action}'. Valid actions are: {', '.join(valid_actions)}"
        
    try:
        pyautogui.press(action)
        return f"Successfully sent '{action}' media command."
    except Exception as e:
        return f"Error executing media control: {str(e)}"

def press_keys(*keys) -> str:
    """
    Simulates pressing keyboard keys.
    Examples: press_keys('space'), press_keys('ctrl', 'c'), press_keys('enter')
    """
    try:
        if len(keys) == 1:
            pyautogui.press(keys[0])
        else:
            pyautogui.hotkey(*keys)
        return f"Successfully pressed keys: {', '.join(keys)}"
    except Exception as e:
        return f"Error pressing keys: {str(e)}"
