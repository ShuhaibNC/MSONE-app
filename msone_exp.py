import tkinter as tk
from tkinter import Listbox, messagebox, Menu, filedialog
import requests
import bs4
import threading
import re


def msonescrap(query, key):
    resultlist = []
    if " " in query:
        query = query.replace(' ', '+')
    try:
        resp = requests.get(f'https://malayalamsubtitles.org/?s={query}')
        soup = bs4.BeautifulSoup(resp.content, 'html.parser')
    except:
        listbox.delete(0, tk.END)
        listbox.insert(tk.END, "Couldn't connect to the internet...")
        return 'Nothing'
    
    if key == 'link':
        title_links = soup.find_all('a', class_='entry-title-link')
        for links in title_links:
            resultlist.append(links['href'])
        return resultlist if resultlist else 'Nothing'
        
    elif key == 'title':
        total_titles = soup.find_all('a', class_='entry-title-link')
        for titles in total_titles:
            resultlist.append(titles.get_text())
        return resultlist if resultlist else 'Nothing'


def get_download_link(page_url):
    try:
        resp = requests.get(page_url)
        soup = bs4.BeautifulSoup(resp.content, 'html.parser')
        download_link = soup.find('a', class_='wpdm-download-link')
        if download_link:
            download_url = download_link.get('data-downloadurl')
            return download_url
        return None
    except:
        return None


def search_in_background(query):
    titles = msonescrap(query, 'title')
    links = msonescrap(query, 'link')

    
    titles, links = remove_duplicates(titles, links)

    
    download_links = []
    for link in links:
        download_url = get_download_link(link)
        if download_url:
            download_links.append(download_url)
        else:
            download_links.append('Download link not found')

    
    if titles == 'Nothing' or links == 'Nothing':
        update_listbox(["No results found."], [])
    else:
        update_listbox(titles, download_links)


def search_names(event=None):
    query = search_var.get().strip()
    
    
    if query == "Enter a movie name" or not query:
        messagebox.showwarning("Input Error", "Please enter a search query.")
        return
    
    
    listbox.delete(0, tk.END)
    listbox.insert(tk.END, "Loading...")
    
    
    search_thread = threading.Thread(target=search_in_background, args=(query,))
    search_thread.start()


def remove_duplicates(titles, links):
    unique_titles = []
    unique_links = []
    for i, title in enumerate(titles):
        if title not in unique_titles:  
            unique_titles.append(title)
            unique_links.append(links[i])
    return unique_titles, unique_links


def update_listbox(titles, download_links):
    listbox.delete(0, tk.END)  
    for i, title in enumerate(titles):
        listbox.insert(tk.END, title)
        listbox.itemconfig(i, {'fg': 'blue'})  
    
    
    listbox.download_links = download_links


def sanitize_filename(filename):
    # Replace invalid characters with an underscore or remove them
    return re.sub(r'[\/:*?"<>|]', '_', filename)

def get_filename_from_cd(response):
    """
    Extracts filename from Content-Disposition header if present.
    """
    if 'Content-Disposition' in response.headers:
        cd = response.headers['Content-Disposition']
        filename = re.findall('filename="(.+)"', cd)
        if filename:
            return filename[0]
    return None

def on_listbox_click(event):
    selection = listbox.curselection()
    if selection:
        index = selection[0]
        if hasattr(listbox, 'download_links'):
            download_link = listbox.download_links[index]
            if download_link != 'Download link not found':
                try:
                    # Fetch the file from the URL
                    response = requests.get(download_link, stream=True)
                    response.raise_for_status()  # Check for any HTTP errors

                    # Try to get the original filename from the Content-Disposition header
                    filename = get_filename_from_cd(response)
                    
                    if not filename:
                        # Fallback: Extract the filename from the URL if no Content-Disposition header
                        filename = download_link.split('/')[-1]

                    # Sanitize the filename to remove invalid characters
                    filename = sanitize_filename(filename)
                    
                    save_path = filedialog.asksaveasfilename(defaultextension=".txt", initialfile=filename)
                    if save_path:
                        with open(save_path, 'wb') as file:
                            for chunk in response.iter_content(chunk_size=8192):
                                file.write(chunk)
                    
                        messagebox.showinfo("Success", f"Downloaded {filename} successfully.")
                    else:
                        messagebox.showwarning("Cancelled", "Download was cancelled.")
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to download: {e}")
            else:
                messagebox.showerror("Error", "No valid download link available.")


def on_enter(e):
    search_button['background'] = "#0052cc"  
    search_button['foreground'] = "white"

def on_leave(e):
    search_button['background'] = "#3385ff"  
    search_button['foreground'] = "black"


def set_placeholder(event=None):
    if search_var.get() == "":
        search_entry.config(fg="grey")
        search_var.set("Enter a movie name")

def remove_placeholder(event=None):
    if search_var.get() == "Enter a movie name":
        search_entry.config(fg="black")
        search_var.set("")


def toggle_dark_mode():
    current_bg = root.cget('bg')
    if current_bg == "#f7f7f7":  
        root.config(bg="#333")
        search_entry.config(bg="#555", fg="white")
        listbox.config(bg="#444", fg="white", selectbackground="#007acc", selectforeground="white")
        search_button.config(bg="#0052cc", fg="white")
        menu_bar.config(bg="#555", fg="white")
    else:  
        root.config(bg="#f7f7f7")
        search_entry.config(bg="white", fg="black")
        listbox.config(bg="#e6f7ff", fg="#333", selectbackground="#007acc", selectforeground="black")
        search_button.config(bg="#3385ff", fg="black")
        menu_bar.config(bg="white", fg="black")


def exit_app():
    root.quit()


def show_about():
    messagebox.showinfo("About", "MSONE Search App\nVersion 1.0\nDeveloped by ShuhaibNC")


root = tk.Tk()
root.title("MSONE Search App")


root.geometry("1020x550")
root.config(bg="#f7f7f7")  


menu_bar = Menu(root)


view_menu = Menu(menu_bar, tearoff=0)
view_menu.add_command(label="Toggle theme", command=toggle_dark_mode)
menu_bar.add_cascade(label="View", menu=view_menu)


tools_menu = Menu(menu_bar, tearoff=0)
tools_menu.add_command(label="Exit", command=exit_app)
menu_bar.add_cascade(label="Tools", menu=tools_menu)


help_menu = Menu(menu_bar, tearoff=0)
help_menu.add_command(label="About", command=show_about)
menu_bar.add_cascade(label="Help", menu=help_menu)


root.config(menu=menu_bar)


search_var = tk.StringVar()
search_entry = tk.Entry(root, textvariable=search_var, font=("Helvetica", 14))
search_entry.grid(row=0, column=0, padx=10, pady=20, ipady=8, sticky="ew")


search_var.set("Enter a movie name")
search_entry.config(fg="grey")
search_entry.bind("<FocusIn>", remove_placeholder)
search_entry.bind("<FocusOut>", set_placeholder)


search_button = tk.Button(root, text="🔍", command=search_names, width=5, height=1, font=("Helvetica", 16), 
                          bg="#3385ff", fg="black", bd=0, relief="flat", cursor="hand2")
search_button.grid(row=0, column=1, padx=5, pady=20)


root.bind('<Return>', search_names)


search_button.bind("<Enter>", on_enter)
search_button.bind("<Leave>", on_leave)


listbox = Listbox(root, width=50, height=10, font=("Helvetica", 12), bd=0, fg="#333", bg="#e6f7ff", 
                  selectbackground="#007acc", selectforeground="white")
listbox.grid(row=1, column=0, columnspan=2, padx=10, pady=10, sticky="nsew")


listbox.bind('<Double-1>', on_listbox_click)


root.grid_columnconfigure(0, weight=1)
root.grid_columnconfigure(1, weight=0)
root.grid_rowconfigure(1, weight=1)


root.mainloop()