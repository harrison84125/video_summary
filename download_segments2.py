import requests
import os
import subprocess
from Crypto.Cipher import AES


# Function to download the .m3u8 playlist
def download_m3u8(m3u8_url, headers, cookies):
    response = requests.get(m3u8_url, headers=headers, cookies=cookies)
    if response.status_code == 200:
        with open("playlist.m3u8", "wb") as f:
            f.write(response.content)
        print("Downloaded .m3u8 playlist successfully.")
    else:
        print(f"Failed to download .m3u8 playlist. Status code: {response.status_code}")


# Function to parse the .m3u8 file and extract key, IV, and segment files
def parse_m3u8(base_url):
    segments = []
    key_url = None
    iv = None
    with open("playlist.m3u8", "r") as f:
        for line in f:
            if line.startswith("#EXT-X-KEY"):
                key_uri = line.split("URI=")[1].split(",")[0].replace('"', "")
                key_url = base_url + key_uri  # Prepend the base URL to the key URI
                iv = line.split("IV=")[1].strip()
            elif line.endswith(".ts\n"):
                segments.append(
                    base_url + line.strip()
                )  # Prepend the base URL to the .ts segments
    return key_url, iv, segments


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
    with open(key_file, "rb") as f:
        key = f.read(16)  # AES-128 uses a 16-byte key
    return key


# Function to download and decrypt the .ts files
def download_and_decrypt_ts_files(segments, key, iv, headers, cookies):
    iv_bytes = bytes.fromhex(
        iv[2:]
    )  # Convert IV from hex to bytes (removing the '0x' prefix)

    for i, segment in enumerate(segments):
        response = requests.get(segment, headers=headers, cookies=cookies)

        if response.status_code == 200:
            encrypted_ts = response.content
            output_file = f"decrypted_{i}.ts"

            # Decrypt the .ts file
            cipher = AES.new(key, AES.MODE_CBC, iv_bytes)
            decrypted_ts = cipher.decrypt(encrypted_ts)

            with open(output_file, "wb") as f_out:
                f_out.write(decrypted_ts)
            print(f"Decrypted {segment} to {output_file}")
        else:
            print(
                f"Failed to download segment {segment}. Status code: {response.status_code}"
            )


# Function to create a list of decrypted files for FFmpeg
def generate_file_list(segments, file_list):
    with open(file_list, "w") as f:
        for i in range(len(segments)):
            ts_file = f"decrypted_{i}.ts"
            if os.path.exists(ts_file):
                f.write(f"file '{ts_file}'\n")
            else:
                print(f"{ts_file} does not exist.")


# Function to merge the decrypted .ts files using FFmpeg
def merge_ts_files(file_list, output_file):
    ffmpeg_command = [
        "ffmpeg",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        file_list,
        "-c",
        "copy",
        output_file,
    ]
    try:
        subprocess.run(ffmpeg_command, check=True)
        print(f"Successfully merged into {output_file}.")
    except subprocess.CalledProcessError as e:
        print(f"Error occurred: {e}")


# Main function to orchestrate the entire process
def main(m3u8_url):

    base_url = m3u8_url.rsplit("/", 1)[0] + "/"
    key_file = "decrypt.key"
    file_list = "file_list.txt"
    output_file = "output_video.mp4"

    headers = {
        "accept": "application/json, text/plain, */*",
        "accept-encoding": "gzip, deflate, br, zstd",
        "accept-language": "zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7",
        "authorization": "Bearer your_token_here",
        "dnt": "1",
        "origin": "https://www.example.com",
        "referer": "https://www.example.com/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
    }

    cookies = {
        "styleMode": "%22light%22",
        "_ga": "GA1.1.832753514.1681640269",
        "local-cookie-accept": '{"status":true}',
        "isSideClose": "false",
        "confirmAdult": '{"isConfirm":true,"normalDialog18Age":"1927/01/01"}',
        "_ga_Q4XDSLQE2E": "GS1.1.1728567616.59.1.1728567717.0.0.0",
    }

    # Step 1: Download the .m3u8 playlist
    download_m3u8(m3u8_url, headers, cookies)

    # Step 2: Parse the .m3u8 file to extract key, IV, and segments
    key_url, iv, segments = parse_m3u8(base_url)

    # Step 3: Download the decryption key
    download_key(key_url, headers, cookies, key_file)

    # Step 4: Read the decryption key from the file
    key = read_key_from_file(key_file)

    # Step 5: Download and decrypt the .ts files
    download_and_decrypt_ts_files(segments, key, iv, headers, cookies)

    # Step 6: Generate the file list for FFmpeg
    generate_file_list(segments, file_list)

    # Step 7: Merge the decrypted .ts files into an .mp4 file
    merge_ts_files(file_list, output_file)


# Run the main function when this script is executed
if __name__ == "__main__":
    main()
