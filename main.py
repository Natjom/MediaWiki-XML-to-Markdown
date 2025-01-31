import os
import time
import datetime
import re
from bs4 import BeautifulSoup
import customtkinter as ctk
import json
import requests

app_version = "B-V0.4"

app_datas_dir = os.path.join(os.getenv('APPDATA'), "MW-XML_to_MD")
os.makedirs(app_datas_dir, exist_ok=True)

def configs_updates(config: dict):
    with open(os.path.join(app_datas_dir, "config.json"), "w") as config_file:
        json.dump(config, config_file, indent=3)

config_path = os.path.join(app_datas_dir, "config.json")
if not os.path.exists(config_path):
    default_config = {"version": app_version, "remind_update": True}
    configs_updates(default_config)

configs = json.load(open(config_path, "r"))
current_version = configs["version"]

new_version_ask = False
try:
    response = requests.get("https://api.github.com/repos/Vecta6/MediaWiki-XML-to-Markdown/releases/latest")
    github_version = response.json().get("tag_name", "")
    if github_version and github_version != current_version:
        new_version_ask = True
except:
    pass

if app_version != current_version:
    configs_updates({"version": app_version, "remind_update": True})

app = ctk.CTk()

file = None
output_path = None
can_convert = 0

def enable_convert():
    if can_convert >= 2:
        convert_btn.configure(state="normal")

def ask_for_file():
    global file, can_convert
    file = ctk.filedialog.askopenfile(title="Open file", filetypes=[("XML file", "*.xml")])
    if file:
        file_pos.configure(text=file.name)
        can_convert += 1
        enable_convert()

def ask_output_directory():
    global output_path, can_convert
    output_path = ctk.filedialog.askdirectory(title="Output directory")
    if output_path:
        output_path_label.configure(text=output_path)
        can_convert += 1
        enable_convert()

def rename_files(directory, forceDelete=False):
    for filename in os.listdir(directory):
        if filename.endswith(".md"):
            file_path = os.path.join(directory, filename)
            with open(file_path, "r", encoding="utf-8") as file:
                content = file.read()
            
            new_content = content.replace("Utilisateur:", "Utilisateur-")
            new_content = new_content.replace("[[Fichier:", "").replace("[[File:", "")
            
            if forceDelete:
                new_content = re.sub(r'^.*Category:.*$', '', new_content, flags=re.MULTILINE).strip()
            
            if new_content != content:
                with open(file_path, "w", encoding="utf-8") as file:
                    file.write(new_content)
                print(f"Modifié : {filename}")
            else:
                print(f"Aucun changement : {filename}")

def convert():
    time_start = time.time()
    global file, output_path
    remove_balises = option_remove_balises.get()
    
    with open(file.name, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "xml")
    
    pages = soup.find_all("page")
    output_dir = output_path if not option_new_folder.get() else os.path.join(output_path, option_new_folder_name.get())
    os.makedirs(output_dir, exist_ok=True)
    
    for page in pages:
        soup2 = BeautifulSoup(str(page), "xml")
        title = soup2.find("title").string.split(":")[-1]
        text = soup2.find("text").string or ""
        
        if title != "Accueil":
            # Suppression des catégories au format #xxxxxx (codes hex)
            text = re.sub(r'#[^\s]{6}', '', text)
            
            categories = [cat.split("]]")[0] for cat in text.split("[[Catégorie:")[1:]]
            text_output = "\n".join(["#" + cat for cat in categories]) + "\n" + text.split("[[Catégorie:")[0]
            
            if remove_balises:
                text_output = re.sub("<[^>]+>", "", text_output)
            
            with open(os.path.join(output_dir, f"{title}.md"), "w", encoding="utf-8") as output:
                output.write(text_output)
    
    rename_files(output_dir, forceDelete=True)
    
    time_stop = time.time()
    time_delta.configure(text=str(datetime.timedelta(seconds=round(time_stop - time_start, 3))))


app.minsize(width=300, height=100)
app.title("MW-XML to MD")

if new_version_ask:
    ctk.CTkLabel(app, text="New version available", text_color="#FFC400").grid(row=0, column=0, padx=1, pady=1)


# Path
ask_file = ctk.CTkButton(app, text="File", command=ask_for_file)
ask_file.grid(row=1, column=0, padx=20, pady=20)
file_pos = ctk.CTkLabel(app, text="")
file_pos.grid(row=2, column=0, padx=20, pady=20)
output_path_ask = ctk.CTkButton(app, text="Output Directory", command=ask_output_directory)
output_path_ask.grid(row=3, column=0, padx=20, pady=20)
output_path_label = ctk.CTkLabel(app, text="")
output_path_label.grid(row=4, column=0, padx=20, pady=20)

# Param
options = ctk.CTkFrame(app)
options.grid(row=5, column=0, padx=20, pady=20, sticky="ew")
option_remove_balises = ctk.CTkCheckBox(options, text="Remove tags")
option_remove_balises.grid(row=0, column=0, padx=20, pady=20)
option_new_folder = ctk.CTkCheckBox(options, text="Create a new folder")
option_new_folder.grid(row=0, column=1, padx=20, pady=20)
option_new_folder_name = ctk.CTkEntry(options, placeholder_text="MW-XML_to_MD_output")
option_new_folder_name.insert(0, "MW-XML_to_MD_output")
convert_btn = ctk.CTkButton(app, text="Convert", command=convert, state="disabled")
convert_btn.grid(row=6, column=0, padx=20, pady=20)
time_delta = ctk.CTkLabel(app, text="")
time_delta.grid(row=7, column=0, padx=20, pady=2)

app.mainloop()
