import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import json
import shutil

class VideoEditorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Local video editor")

        # Chemins des dossiers
        self.current_dir = os.path.dirname(os.path.abspath(__file__))
        # self.video_dir = "Vidéos"
        self.video_dir = os.path.join(self.current_dir, 'Vidéos')
        # self.thumbnail_dir = "thumbnail"
        self.thumbnail_dir =  os.path.join(self.current_dir, 'thumbnail')
        # self.meta_dir = "meta"
        self.meta_dir = os.path.join(self.current_dir, 'meta')

        # Liste des vidéos disponibles
        self.video_files = [f for f in os.listdir(self.video_dir) if f.endswith(('.mp4', '.avi', '.mov'))]

        # Interface
        self.setup_ui()

    def setup_ui(self):
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # Liste des vidéos (à gauche)
        self.video_list_frame = ttk.LabelFrame(main_frame, text="Videos list", padding="10")
        self.video_list_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)

        self.video_listbox = tk.Listbox(self.video_list_frame, width=30, height=15)
        self.video_listbox.pack(fill=tk.BOTH, expand=True)

        # Remplir la liste des vidéos
        for video in self.video_files:
            self.video_listbox.insert(tk.END, video)

        # Zone d'édition (à droite)
        self.edit_frame = ttk.LabelFrame(main_frame, text="Edit metadata", padding="10")
        self.edit_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=5, pady=5)

        # Champs pour les métadonnées
        ttk.Label(self.edit_frame, text="Title:").grid(row=0, column=0, sticky=tk.W)
        self.title_entry = ttk.Entry(self.edit_frame, width=40)
        self.title_entry.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)

        ttk.Label(self.edit_frame, text="Description:").grid(row=1, column=0, sticky=tk.W)
        self.desc_text = tk.Text(self.edit_frame, width=30, height=5)
        self.desc_text.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)

        ttk.Label(self.edit_frame, text="Author:").grid(row=2, column=0, sticky=tk.W)
        self.author_entry = ttk.Entry(self.edit_frame, width=40)
        self.author_entry.grid(row=2, column=1, sticky=tk.W, padx=5, pady=5)

        # Zone pour la miniature
        self.thumbnail_label = ttk.Label(self.edit_frame, text="Thumbnail:")
        self.thumbnail_label.grid(row=3, column=0, sticky=tk.W, pady=10)

        self.thumbnail_canvas = tk.Canvas(self.edit_frame, width=200, height=150, bg="lightgray")
        self.thumbnail_canvas.grid(row=3, column=1, sticky=tk.W, padx=5, pady=5)

        # Boutons pour sauvegarder et charger une nouvelle miniature
        self.save_button = ttk.Button(self.edit_frame, text="Save", command=self.save_metadata)
        self.save_button.grid(row=4, column=0, pady=10)

        self.upload_button = ttk.Button(self.edit_frame, text="Load thumbnail", command=self.upload_thumbnail)
        self.upload_button.grid(row=4, column=1, pady=10)

        # Lier la sélection d'une vidéo à l'affichage des métadonnées
        self.video_listbox.bind('<<ListboxSelect>>', self.load_video_metadata)

    def load_video_metadata(self, event):
        # Récupérer la vidéo sélectionnée
        selection = self.video_listbox.curselection()
        if not selection:
            return

        video_file = self.video_listbox.get(selection[0])
        meta_file = os.path.join(self.meta_dir, f"{os.path.splitext(video_file)[0]}.json")

        # Charger les métadonnées
        if os.path.exists(meta_file):
            with open(meta_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)

            self.title_entry.delete(0, tk.END)
            self.title_entry.insert(0, metadata.get("title", ""))

            self.desc_text.delete(1.0, tk.END)
            self.desc_text.insert(1.0, metadata.get("descritpion", ""))

            self.author_entry.delete(0, tk.END)
            self.author_entry.insert(0, metadata.get("author", ""))

        # Charger la miniature
        thumbnail_file = os.path.join(self.thumbnail_dir, f"{os.path.splitext(video_file)[0]}.png")
        if os.path.exists(thumbnail_file):
            self.display_thumbnail(thumbnail_file)


    def display_thumbnail(self, thumbnail_path):
        # Afficher la miniature sur le canvas
        try:
            from PIL import Image, ImageTk
            img = Image.open(thumbnail_path)
            img.thumbnail((200, 150))
            self.thumbnail_img = ImageTk.PhotoImage(img)
            self.thumbnail_canvas.create_image(0, 0, anchor=tk.NW, image=self.thumbnail_img)
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de charger la miniature: {e}")
    

    def upload_thumbnail(self):
        # Ouvrir une boîte de dialogue pour sélectionner une nouvelle miniature
        file_path = filedialog.askopenfilename(filetypes=[("Images", "*.png")])
        if file_path:
            self.display_thumbnail(file_path)
            self.save_thumbnail(file_path)

    def save_thumbnail(self, thumbnail_path):
        selection = self.video_listbox.curselection()
        if not selection:
            return
        
        video_file = self.video_listbox.get(selection[0])
        dest_thumbnail_path = os.path.join(self.thumbnail_dir, f"{os.path.splitext(video_file)[0]}.png")
        try:
            # Copier la miniature vers le dossier 'thumbnail' avec le bon nom
            shutil.copy2(thumbnail_path, dest_thumbnail_path)
            messagebox.showinfo("Success", "Thumbnail saved with success!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to saved thumbnail : {e}")

    def save_metadata(self):
        # Sauvegarder les métadonnées et la miniature
        selection = self.video_listbox.curselection()
        if not selection:
            return

        video_file = self.video_listbox.get(selection[0])
        meta_file = os.path.join(self.meta_dir, f"{os.path.splitext(video_file)[0]}.json")

        metadata = {
            "title": self.title_entry.get(),
            "descritpion": self.desc_text.get(1.0, tk.END).strip(),
            "author": self.author_entry.get()
        }

        with open(meta_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=4)

        messagebox.showinfo("Success", "Métadonnées sauvegardées avec succès!")

if __name__ == "__main__":
    root = tk.Tk()
    app = VideoEditorApp(root)
    root.mainloop()
