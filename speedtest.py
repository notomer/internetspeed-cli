import socket
import time
import requests
import xml.etree.ElementTree as ET

# URL of the raw server list
server_list_url = 'https://gist.githubusercontent.com/epixoip/2b8696ed577d584a7f484c006d945051/raw/d6f15e84d9496d5b95c3fe8df706764fb16de1e7/SpeedTest.Net%2520Server%2520List'

# Fetch the server list
def fetch_server_list(url):
    response = requests.get(url)
    response.raise_for_status()
    return response.text

# Parse the server list and filter by country code
def parse_and_filter_servers(server_list, country_code):
    root = ET.fromstring(server_list)
    servers = []
    for server in root.findall('server'):
        if server.get('countrycode') == country_code:
            servers.append(server.get('url'))
    return servers

# Utility function to create a progress bar
def print_progress_bar(iteration, total, prefix='', suffix='', length=50, fill='█', print_end="\r"):
    percent = ("{0:.1f}").format(100 * (iteration / float(total)))
    filled_length = int(length * iteration // total)
    bar = fill * filled_length + '-' * (length - filled_length)
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end=print_end)
    if iteration == total:
        print()

# Function to measure download speed
def measure_download_speed(server):
    parsed_url = server.replace("http://", "").replace("https://", "").split('/')[0]
    port = 80
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((parsed_url, port))
        request = 'GET / HTTP/1.1\r\nHost: {}\r\n\r\n'.format(parsed_url)
        sock.sendall(request.encode('utf-8'))

        start_time = time.time()
        total_data = 0
        chunks = 100
        for i in range(chunks):
            response = sock.recv(4096)
            total_data += len(response)
            print_progress_bar(i + 1, chunks, prefix='Downloading:', length=40)
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        speed_bps = (total_data * 8) / elapsed_time
        speed_mbps = speed_bps / 1_000_000
        return speed_mbps
    except socket.error as e:
        print("Socket error:", e)
        return 0
    finally:
        sock.close()

# Function to measure upload speed
def measure_upload_speed(server):
    parsed_url = server.replace("http://", "").replace("https://", "").split('/')[0]
    port = 80
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect((parsed_url, port))
        data = b'x' * 4096
        start_time = time.time()
        total_data = 0
        chunks = 100
        for i in range(chunks):
            sock.sendall(data)
            total_data += len(data)
            print_progress_bar(i + 1, chunks, prefix='Uploading:', length=40)

        end_time = time.time()
        elapsed_time = end_time - start_time
        speed_bps = (total_data * 8) / elapsed_time
        speed_mbps = speed_bps / 1_000_000
        return speed_mbps
    except socket.error as e:
        print("Socket error:", e)
        return 0
    finally:
        sock.close()

# Main function to run the speed test
def speed_test():
    server_list = fetch_server_list(server_list_url)
    servers = parse_and_filter_servers(server_list, country_code_filter)
    if not servers:
        print(f"No servers found for country code: {country_code_filter}")
        return
    
    server = servers[0]  # Use the first server from the filtered list

    download_speed = measure_download_speed(server)
    upload_speed = measure_upload_speed(server)

    # Printing results with colors
    print("\033[92mDownload Speed: {:.2f} Mbps\033[0m".format(download_speed))
    print("\033[94mUpload Speed: {:.2f} Mbps\033[0m".format(upload_speed))

if __name__ == '__main__':
    speed_test()