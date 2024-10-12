import requests
import urllib.parse
from Crypto.Cipher import AES
import os
import subprocess

# Function to download the .ts files
def download_ts_files(base_url, headers, cookies, start_number, end_number):
    for number in range(start_number, end_number + 1):
        ts_url = f"{base_url}{number}.ts"
        response = requests.get(ts_url, headers=headers, cookies=cookies)
        
        if response.status_code == 200:
            with open(f"video_{number}.ts", "wb") as f:
                f.write(response.content)
            print(f"Downloaded segment {number} successfully.")
        else:
            print(f"Failed to download segment {number}. Status code: {response.status_code}")

# Function to download the AES decryption key
def download_key(key_url, headers, cookies, key_file):
    response = requests.get(key_url, headers=headers, cookies=cookies)
    
    if response.status_code == 200:
        with open(key_file, "wb") as f:
            f.write(response.content)
        print("Downloaded decryption key successfully.")
    else:
        print(f"Failed to download key. Status code: {response.status_code}")

# Function to read the AES key from the file
def read_key_from_file(key_file):
    with open(key_file, 'rb') as f:
        key = f.read(16)  # AES-128 uses a 16-byte key
    return key

# Function to decrypt the .ts files
def decrypt_ts_files(start_number, end_number, key):
    for i in range(start_number, end_number + 1):
        input_file = f'video_{i}.ts'
        output_file = f'decrypted_{i}.ts'
        
        if os.path.exists(input_file):
            iv = bytes.fromhex(f'{i:032x}')  # Derive IV from the segment number
            decrypt_ts_file(input_file, output_file, key, iv)
        else:
            print(f"{input_file} does not exist.")

# Function to decrypt a single .ts file
def decrypt_ts_file(input_file, output_file, key, iv):
    with open(input_file, 'rb') as f_in:
        encrypted_data = f_in.read()

    cipher = AES.new(key, AES.MODE_CBC, iv)
    decrypted_data = cipher.decrypt(encrypted_data)

    with open(output_file, 'wb') as f_out:
        f_out.write(decrypted_data)

    print(f"Decrypted {input_file} to {output_file}")

# Function to create a list of decrypted files for FFmpeg
def generate_file_list(start_number, end_number, file_list):
    with open(file_list, 'w') as f:
        for number in range(start_number, end_number + 1):
            ts_file = f"decrypted_{number}.ts"
            if os.path.exists(ts_file):
                f.write(f"file '{ts_file}'\n")
            else:
                print(f"{ts_file} does not exist.")

# Function to merge the decrypted .ts files using FFmpeg
def merge_ts_files(file_list, output_file):
    ffmpeg_command = [
        'ffmpeg',
        '-f', 'concat',
        '-safe', '0',
        '-i', file_list,
        '-c', 'copy',
        output_file
    ]
    try:
        subprocess.run(ffmpeg_command, check=True)
        print(f"Successfully merged into {output_file}.")
    except subprocess.CalledProcessError as e:
        print(f"Error occurred: {e}")

# The main function to orchestrate the entire process
def main(root_url):
    base_url = root_url + "_1080p_playList"
    key_url = root_url + "_1080p.key"
    key_file = 'decrypt.key'
    file_list = 'file_list.txt'
    output_file = 'output_video.mp4'
    start_number = 0
    # ! 100 is around 15 minutes of video
    end_number = 100  # Adjust according to the available playlist segments
    
    # The encoded cookie string you provided
    encoded_cookie = "auth_token_json"
    decoded_cookie = urllib.parse.unquote(encoded_cookie)
    
    # Set the headers and cookies
    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
        "authorization": "Bearer your_token_here",
        "dnt": "1",
        "origin": "https://www.example.com",
        "referer": "https://www.example.com/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"
    }
    
    cookies = {
        "styleMode": "%22light%22",
        "_ga": "GA1.1.832753514.1681640269",
        "local-cookie-accept": '{"status":true}',
        "isSideClose": "false",
        "confirmAdult": '{"isConfirm":true,"normalDialog18Age":"1927/01/01"}',
        "auth": decoded_cookie,
        "_ga_Q4XDSLQE2E": "GS1.1.1728567616.59.1.1728567717.0.0.0"
    }
    
    # Step 1: Download the .ts files
    download_ts_files(base_url, headers, cookies, start_number, end_number)

    # Step 2: Download the decryption key
    download_key(key_url, headers, cookies, key_file)

    # Step 3: Read the decryption key from the file
    key = read_key_from_file(key_file)

    # Step 4: Decrypt the downloaded .ts files
    decrypt_ts_files(start_number, end_number, key)

    # Step 5: Generate the file list for FFmpeg
    generate_file_list(start_number, end_number, file_list)

    # Step 6: Merge the decrypted .ts files into an .mp4 file
    merge_ts_files(file_list, output_file)

# Run the main function when this script is executed
if __name__ == "__main__":
    main(root_url = "target_url_here"
)
