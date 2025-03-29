import os
import time

def wait_until_file_is_ready(path, check_interval=3, required_stable_checks=2, max_wait=1800):
    print(f"⏳ Warte auf stabile Datei: {path}")
    last_size = -1
    stable_count = 0
    waited = 0

    while waited < max_wait:
        if os.path.exists(path):
            current_size = os.path.getsize(path)

            if current_size == last_size:
                stable_count += 1
                if stable_count >= required_stable_checks:
                    print(f"✅ Datei ist stabil mit {current_size} Bytes.")
                    return True
            else:
                stable_count = 0
                last_size = current_size

        time.sleep(check_interval)
        waited += check_interval

    print(f"❌ Datei war nach {max_wait} Sekunden nicht stabil.")
    return False