import re
import pathlib
import requests
from natsort import natsorted
import yaml
import time

discord_attachment_regex = re.compile(r"https://(cdn\.discordapp\.com|media.discordapp.net)/attachments/([0-9]+)/([0-9]+)/([A-Za-z0-9_\-\.]+)")

glitch_talk_filenames = [
    "bn1_glitch_talk.dump",
    "bn2_glitch_talk.dump",
    "bn3_glitch_talk.dump",
    "bn4_glitch_talk.dump",
    "bn5_glitch_talk.dump",
    "bn6_glitch_talk.dump",
    "exe45_glitch_talk.dump",
    "bnlc_glitch_talk.dump"
]

def download_attachments():
    for glitch_talk_filename in glitch_talk_filenames:
        output = ""
        glitch_talk_filestem = pathlib.Path(glitch_talk_filename).stem

        with open(glitch_talk_filename, "r") as f:
            contents = f.read()

        all_discord_attachment_parts = discord_attachment_regex.findall(contents)
        output_basenames = []

        pathlib.Path(glitch_talk_filestem).mkdir(exist_ok=True, parents=True)

        for discord_attachment_parts in all_discord_attachment_parts:
            host_name, numbers_pt1, numbers_pt2, attachment_filename = discord_attachment_parts
            discord_attachment_url = f"https://{host_name}/attachments/{numbers_pt1}/{numbers_pt2}/{attachment_filename}"
            print(f"Downloading {discord_attachment_url}!")

            r = requests.get(discord_attachment_url)

            output_basename = f"{host_name}&{numbers_pt1}&{numbers_pt2}&{attachment_filename}"
            output_basenames.append(output_basename)

            with open(f"{glitch_talk_filestem}/{output_basename}", "wb+") as f:
                f.write(r.content)

        sorted_output_basenames = natsorted(output_basenames)

        output += "".join(f"{output_basename}: \n" for output_basename in sorted_output_basenames)

        with open(f"{glitch_talk_filestem}_attachment_info.dump", "w+") as f:
            f.write(output)

class Attachment:
    __slots__ = ("filename", "upload_filename", "suffix", "imgur_link", "discord_attachment_url")

    def __init__(self, filename, imgur_link):
        self.filename = filename
        discord_attachment_parts = filename.split("&", maxsplit=3)
        self.upload_filename = discord_attachment_parts[3]
        self.suffix = pathlib.Path(filename).suffix
        self.imgur_link = imgur_link
        host_name, numbers_pt1, numbers_pt2, attachment_filename = discord_attachment_parts
        self.discord_attachment_url = f"https://{host_name}/attachments/{numbers_pt1}/{numbers_pt2}/{attachment_filename}"

def write_attachment_info(attachment_info, attachment_info_filename):
    output = ""
    output += "".join(f"{attachment.filename}: {attachment.imgur_link}\n" for attachment in attachment_info)
    with open(attachment_info_filename, "w+") as f:
        f.write(output)

def read_in_attachment_info(glitch_talk_filestem):
    attachment_info_filename = f"{glitch_talk_filestem}_attachment_info.dump"
    with open(attachment_info_filename, "r") as f:
        lines = f.readlines()

    attachment_info = []
    for line in lines:
        line = line.strip()
        if line == "":
            continue

        attachment_filename, attachment_imgur_link = line.split(":", maxsplit=1)
        attachment_info.append(Attachment(attachment_filename, attachment_imgur_link))

    return attachment_info, attachment_info_filename

def upload_images():
    with open("config.yml", "r") as f:
        config = yaml.safe_load(f)

    access_token = config["access_token"]

    #r = requests.get("https://api.imgur.com/3/credits", headers={
    #    "Authorization": f"Bearer {access_token}"
    #})
    #
    #print(r.json())
    #return

    for glitch_talk_filename in glitch_talk_filenames:
        glitch_talk_filestem = pathlib.Path(glitch_talk_filename).stem
        print(f"Uploading files from {glitch_talk_filestem}!")

        attachment_info, attachment_info_filename = read_in_attachment_info(glitch_talk_filestem)

        for i, attachment in enumerate(attachment_info):
            if attachment.imgur_link != "":
                print(f"Skipped {attachment.upload_filename}!")
                continue

            if attachment.suffix in {".png", ".jpg", ".webp"}:
                file_type = "image"
            elif attachment.suffix in {".mp4", ".mov"}:
                file_type = "video"
            else:
                print(f"Unknown extension for file {attachment.filename}!")
                continue

            print(f"file_type: {file_type}")

            expected_upload_time = time.time()

            with open(f"{glitch_talk_filestem}/{attachment.filename}", "rb") as f:
                r = requests.post("https://api.imgur.com/3/upload/", data={
                    "type": "file",
                    "name": attachment.upload_filename
                }, headers={
                    "Authorization": f"Bearer {access_token}"
                }, files={
                    file_type: f
                })

            if r.status_code != 200:
                print(f"Upload of {attachment.filename} failed with status {r.status_code}: {r.reason}. response_data: {r.json()}")
                continue

            response_data = r.json()
            if not response_data["success"]:
                print(f"Upload of {attachment.filename} failed. response_data: {response_data}")
                continue

            try:
                attachment.imgur_link = response_data["data"]["link"]
            except KeyError as e:
                print(f"Attachment {attachment.filename} does not have a link, looking up manually. response_data: {response_data}")

                query_images_count = 0

                while True:
                    time.sleep(5)
                    r = requests.get(f"https://api.imgur.com/3/account/luckytyphlosion/images/0.json?perPage=1", headers={
                        "Authorization": f"Bearer {access_token}"
                    })

                    response_data = r.json()

                    if r.status_code != 200:
                        print(f"Looking at images failed with status {r.status_code}: {r.reason}. response_data: {response_data}")
                        continue
                    
                    image_entry = response_data["data"][0]
                    image_datetime = image_entry.get("datetime")
                    if image_datetime is None:
                        print(f"Warning: datetime was None. response_data: {response_data}")
                        image_datetime = 0

                    if expected_upload_time <= image_datetime:
                        imgur_link = image_entry.get("link")
                        if imgur_link is None:
                            raise RuntimeError(f"Attachment {attachment.filename} does not have a link! response_data: {response_data}")

                        attachment.imgur_link = imgur_link
                        break
                    else:
                        query_images_count += 1
                        if query_images_count >= 5:
                            break

                        print(f"Could not find attachment, sleeping for another 5 seconds [{query_images_count}]")

                if query_images_count >= 5:
                    raise RuntimeError(f"Timed out when looking for attachment {attachment.filename} via images endpoint. last response_data: {response_data}")

            write_attachment_info(attachment_info, attachment_info_filename)
            print(f"Successfully uploaded {attachment.upload_filename} to {attachment.imgur_link}! Sleeping for 10 seconds.")
            time.sleep(10)

def replace_links():
    for glitch_talk_filename in glitch_talk_filenames:
        output = ""
        glitch_talk_filestem = pathlib.Path(glitch_talk_filename).stem
        print(f"Replacing links in {glitch_talk_filestem}!")

        with open(glitch_talk_filename, "r") as f:
            glitch_talk_contents = f.read()

        attachment_info, attachment_info_filename = read_in_attachment_info(glitch_talk_filestem)

        for attachment in attachment_info:
            if attachment.imgur_link == "":
                print(f"Error: attachment {attachment.filename} has no link!")
                continue

            glitch_talk_contents = re.sub(fr"\b{re.escape(attachment.discord_attachment_url)}\b", attachment.imgur_link, glitch_talk_contents)

        with open(f"{glitch_talk_filestem}_out.dump", "w+") as f:
            f.write(glitch_talk_contents)

def main():
    MODE = 1

    if MODE == 0:
        download_attachments()
    elif MODE == 1:
        upload_images()
    elif MODE == 2:
        replace_links()
    else:
        print("No mode selected!")


if __name__ == "__main__":
    main()
