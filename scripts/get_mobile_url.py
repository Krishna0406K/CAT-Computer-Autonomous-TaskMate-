import socket

def get_local_ip():
    try:
        # Create a dummy socket to determine the local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except Exception:
        return "127.0.0.1"

if __name__ == "__main__":
    ip = get_local_ip()
    url = f"http://{ip}:8000/mobile"
    print("==================================================")
    print("📱 CAT MOBILE COMPANION APP is ready!")
    print("==================================================")
    print("Ensure your Python backend (main.py) is running.")
    print("Make sure your phone is connected to the same Wi-Fi network as this PC.")
    print(f"\nOpen this exact URL in your phone's web browser:\n\n{url}\n")
    print("==================================================")
