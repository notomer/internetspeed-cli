import socket
import time
import requests
import xml.etree.ElementTree as ET
import math

# URL of the raw server list
server_list_url = 'https://gist.githubusercontent.com/epixoip/2b8696ed577d584a7f484c006d945051/raw/d6f15e84d9496d5b95c3fe8df706764fb16de1e7/SpeedTest.Net%2520Server%2520List'

# Fetch the server list
def fetch_server_list(url):
    response = requests.get(url)
    response.raise_for_status()
    return response.text

# Parse the server list
def parse_servers(server_list):
    root = ET.ElementTree(ET.fromstring(server_list))
    servers = []
    for server in root.iter('server'):
        servers.append({
            'url': server.get('url'),
            'lat': float(server.get('lat')),
            'lon': float(server.get('lon')),
            'name': server.get('name'),
            'country': server.get('country'),
            'sponsor': server.get('sponsor')
        })
    return servers

# Test if the server is responsive
def test_server(server):
    parsed_url = server['url'].replace("http://", "").replace("https://", "").split('/')[0]
    port = 80
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2)  # Set timeout to 2 seconds
    try:
        sock.connect((parsed_url, port))
        sock.close()
        return True
    except socket.error:
        return False

# Get user's location based on IP
def get_user_location():
    response = requests.get('http://ip-api.com/json/')
    data = response.json()
    return (data['lat'], data['lon'])

# Calculate distance between two points using Haversine formula
def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371  # Radius of the Earth in km
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    a = math.sin(dlat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c
    return distance

# Measure download speed
def measure_download_speed(server):
    parsed_url = server['url'].replace("http://", "").replace("https://", "").split('/')[0]
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
        
        end_time = time.time()
        elapsed_time = end_time - start_time
        speed_bps = (total_data * 8) / elapsed_time
        speed_mbps = speed_bps / 1_000_000
        return speed_mbps
    except socket.error:
        return 0
    finally:
        sock.close()

# Measure upload speed
def measure_upload_speed(server):
    parsed_url = server['url'].replace("http://", "").replace("https://", "").split('/')[0]
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

        end_time = time.time()
        elapsed_time = end_time - start_time
        speed_bps = (total_data * 8) / elapsed_time
        speed_mbps = speed_bps / 1_000_000
        return speed_mbps
    except socket.error:
        return 0
    finally:
        sock.close()

# Main function to run the speed test
def speed_test(choose_server=False):
    server_list = fetch_server_list(server_list_url)
    servers = parse_servers(server_list)
    if not servers:
        print("No servers found.")
        return

    # Filter working servers
    working_servers = [server for server in servers if test_server(server)]
    if not working_servers:
        print("No working servers found.")
        return

    # Get user's location
    user_location = get_user_location()

    # Calculate distances to servers
    for server in working_servers:
        server['distance'] = calculate_distance(user_location[0], user_location[1], server['lat'], server['lon'])

    # Sort servers by distance
    working_servers.sort(key=lambda x: x['distance'])

    # Display servers and allow user to choose if choose_server is True
    if choose_server:
        print("Available servers:")
        for i, server in enumerate(working_servers):
            print(f"{i + 1}. {server['url']} - {server['name']}, {server['country']} ({server['sponsor']})")

        choice = int(input(f"Choose a server by entering a number (1-{len(working_servers)}): ")) - 1
        if choice < 0 or choice >= len(working_servers):
            print("Invalid choice.")
            return

        selected_server = working_servers[choice]
    else:
        selected_server = working_servers[0]
        print(f"Using the closest server: {selected_server['url']} - {selected_server['name']}, {selected_server['country']} ({selected_server['sponsor']})")

    download_speed = measure_download_speed(selected_server)
    upload_speed = measure_upload_speed(selected_server)

    # Printing results with colors
    print("\033[92mDownload Speed: {:.2f} Mbps\033[0m".format(download_speed))
    print("\033[94mUpload Speed: {:.2f} Mbps\033[0m".format(upload_speed))

if __name__ == '__main__':
    speed_test(choose_server=True)