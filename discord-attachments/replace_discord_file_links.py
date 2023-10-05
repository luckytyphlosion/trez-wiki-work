import re
import pathlib
import requests
from natsort import natsorted
import yaml
import requests

discord_attachment_regex = re.compile(r"https://(cdn\.discordapp\.com|media.discordapp.net)/attachments/([0-9]+)/([0-9]+)/([A-Za-z0-9_\-\.]+)")

glitch_talk_filenames = [
    #"bn1_glitch_talk.dump",
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

def upload_images():
    pass

def main():
    MODE = 0

    if MODE == 0:
        download_attachments()
    else:
        print("No mode selected!")


if __name__ == "__main__":
    main()
