import tkinter as tk
from tkinter import ttk, messagebox
import threading
import os

class GameDownloaderGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Eastwood Games Downloader")
        self.root.geometry("600x400")
        
        # Sample games data
        self.games = [
            {"name": "Demo Game 1", "description": "A fun demo game"},
            {"name": "Demo Game 2", "description": "Another exciting demo"},
            {"name": "Demo Game 3", "description": "Sample game prototype"}
        ]
        
        self.setup_ui()
        
    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title_label = ttk.Label(main_frame, text="Available Games", font=("Helvetica", 16, "bold"))
        title_label.grid(row=0, column=0, pady=10, sticky=tk.W)
        
        # Games listbox
        self.games_listbox = tk.Listbox(main_frame, height=10)
        self.games_listbox.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        # Populate games list
        for game in self.games:
            self.games_listbox.insert(tk.END, game["name"])
        
        # Description label
        self.description_label = ttk.Label(main_frame, text="Select a game to see description")
        self.description_label.grid(row=2, column=0, pady=10)
        
        # Download button
        self.download_button = ttk.Button(main_frame, text="Download Demo", 
                                        command=self.simulate_download)
        self.download_button.grid(row=3, column=0, pady=5)
        
        # Bind selection event
        self.games_listbox.bind('<<ListboxSelect>>', self.on_select)
        
    def on_select(self, event):
        if not self.games_listbox.curselection():
            return
        
        selection = self.games_listbox.curselection()[0]
        game = self.games[selection]
        self.description_label.config(text=game['description'])
        
    def simulate_download(self):
        if not self.games_listbox.curselection():
            messagebox.showwarning("Warning", "Please select a game first")
            return
            
        selection = self.games_listbox.curselection()[0]
        game = self.games[selection]
        messagebox.showinfo("Demo", f"This is a demo. In a full version, {game['name']} would be downloaded.")
    
    def run(self):
        self.root.mainloop()