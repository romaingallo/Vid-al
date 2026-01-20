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

        # Bouton ajouter vidéo
        self.add_video_button = ttk.Button(self.video_list_frame, text="+", command=self.setup_add_video_window)
        self.add_video_button.pack(fill=tk.X, expand=False)

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
            messagebox.showerror("Error", f"Failed to save thumbnail : {e}")

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
    
    def setup_add_video_window(self):
        
        self.add_video_window = tk.Toplevel(self.root)
        self.add_video_window.title("Add a video")

        # Main frames
        self.add_video_top_frame = tk.Frame(self.add_video_window)
        self.add_video_top_frame.pack(fill = tk.BOTH, expand = True)
        self.add_video_bottom_frame = tk.Frame(self.add_video_window)
        self.add_video_bottom_frame.pack(fill = tk.BOTH, expand = True, pady=15)
        # Sub-top frame
        self.add_video_video_selection_frame = tk.Frame(self.add_video_top_frame)
        self.add_video_video_selection_frame.pack(fill = tk.BOTH, expand = True)
        self.add_video_thumbnail_selection_frame = tk.Frame(self.add_video_top_frame)
        self.add_video_thumbnail_selection_frame.pack(fill = tk.BOTH, expand = True)
        self.add_video_title_selection_frame = tk.Frame(self.add_video_top_frame)
        self.add_video_title_selection_frame.pack(fill = tk.BOTH, expand = True)
        self.add_video_description_selection_frame = tk.Frame(self.add_video_top_frame)
        self.add_video_description_selection_frame.pack(fill = tk.BOTH, expand = True)
        self.add_video_author_selection_frame = tk.Frame(self.add_video_top_frame)
        self.add_video_author_selection_frame.pack(fill = tk.BOTH, expand = True)
        self.add_video_url_selection_frame = tk.Frame(self.add_video_top_frame)
        self.add_video_url_selection_frame.pack(fill = tk.BOTH, expand = True)

        # Data selection
        self.add_video_path_to_video_label = ttk.Label(self.add_video_video_selection_frame, text="Path to video : ", anchor=tk.E)
        self.add_video_path_to_video_label.pack(side = tk.LEFT, expand = True, fill = tk.BOTH)
        self.select_video_button = ttk.Button(self.add_video_video_selection_frame, text="Select video", command=self.add_video_select_path)
        self.select_video_button.pack(side = tk.LEFT, expand = True, fill = tk.BOTH)

        self.add_video_thumbnail_label = ttk.Label(self.add_video_thumbnail_selection_frame, text="Thumbnail : ", anchor=tk.E)
        self.add_video_thumbnail_label.pack(side = tk.LEFT, expand = True, fill = tk.BOTH)
        self.add_video_thumbnail_canvas = tk.Canvas(self.add_video_thumbnail_selection_frame, width=200, height=150, bg="lightgray")
        self.add_video_thumbnail_canvas.pack(side = tk.LEFT, expand = True, fill = tk.BOTH)
        self.add_video_select_thumbnail_button = ttk.Button(self.add_video_thumbnail_selection_frame, text="Select thumbnail", command=self.add_video_select_thumbnail)
        self.add_video_select_thumbnail_button.pack(side = tk.LEFT, expand = True, fill = tk.BOTH)

        self.add_video_title_label = ttk.Label(self.add_video_title_selection_frame, text="Title : ", anchor=tk.E)
        self.add_video_title_label.pack(side = tk.LEFT, expand = True, fill = tk.BOTH)
        self.select_video_title_entry = ttk.Entry(self.add_video_title_selection_frame, width=40)
        self.select_video_title_entry.pack(side = tk.LEFT, expand = True, fill = tk.BOTH)

        self.add_video_description_label = ttk.Label(self.add_video_description_selection_frame, text="Description : ", anchor=tk.E)
        self.add_video_description_label.pack(side = tk.LEFT, expand = True, fill = tk.BOTH)
        self.select_video_description_entry = tk.Text(self.add_video_description_selection_frame, width=40, height=5)
        self.select_video_description_entry.pack(side = tk.LEFT, expand = True, fill = tk.BOTH)

        self.add_video_author_label = ttk.Label(self.add_video_author_selection_frame, text="Author : ", anchor=tk.E)
        self.add_video_author_label.pack(side = tk.LEFT, expand = True, fill = tk.BOTH)
        self.select_video_author_entry = ttk.Entry(self.add_video_author_selection_frame, width=40)
        self.select_video_author_entry.pack(side = tk.LEFT, expand = True, fill = tk.BOTH)

        self.add_video_url_label = ttk.Label(self.add_video_url_selection_frame, text="Video URL : ", anchor=tk.E)
        self.add_video_url_label.pack(side = tk.LEFT, expand = True, fill = tk.BOTH)
        self.select_video_url_entry = ttk.Entry(self.add_video_url_selection_frame, width=40)
        self.select_video_url_entry.pack(side = tk.LEFT, expand = True, fill = tk.BOTH)

        self.add_video_path_to_thumbnail_img = ""
        self.add_video_path_to_video = ""

        # Validation
        self.confirm_add_video_button = ttk.Button(self.add_video_bottom_frame, text="Add video", command=self.add_video)
        self.confirm_add_video_button.pack(side = tk.LEFT, expand = True, fill = tk.BOTH)

        self.cancel_add_video_button = ttk.Button(self.add_video_bottom_frame, text="Cancel", command=self.cancel_add_video)
        self.cancel_add_video_button.pack(side = tk.LEFT, expand = True, fill = tk.BOTH)

    def add_video_select_path(self):
        file_path = filedialog.askopenfilename(filetypes=[("Vidéo", "*.mp4")])
        if file_path:
            self.add_video_path_to_video = file_path
            self.add_video_path_to_video_label['text'] = file_path
            self.add_video_window.focus()
    
    def add_video_select_thumbnail(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image", "*.png")])
        if file_path:
            try:
                self.add_video_path_to_thumbnail_img = file_path
                from PIL import Image, ImageTk
                img = Image.open(file_path)
                img.thumbnail((200, 150))
                self.add_video_thumbnail_img = ImageTk.PhotoImage(img)
                self.add_video_thumbnail_canvas.create_image(0, 0, anchor=tk.NW, image=self.add_video_thumbnail_img)
            except Exception as e:
                messagebox.showerror("Erreur", f"Impossible de charger la miniature: {e}")
            self.add_video_window.focus()
    
    def add_video(self):
        if self.add_video_path_to_video == "" :
            messagebox.showerror("Error", f"Select a video first.")
            self.add_video_window.focus()
            return
        if self.add_video_path_to_thumbnail_img == "" :
            messagebox.showerror("Error", f"Select a thumbnail first.")
            self.add_video_window.focus()
            return
        if self.select_video_title_entry.get() == "" :
            messagebox.showerror("Error", f"You need to input a title.")
            self.add_video_window.focus()
            return
        if self.select_video_author_entry.get() == "" :
            messagebox.showerror("Error", f"You need to input an author username.")
            self.add_video_window.focus()
            return
        if self.select_video_url_entry.get() == "" :
            messagebox.showerror("Error", f"You need to input an URL for the video.")
            self.add_video_window.focus()
            return
        elif self.select_video_url_entry.get().find(" ") != -1 or self.select_video_url_entry.get().find("/") != -1 or self.select_video_url_entry.get().find("\\") != -1 or self.select_video_url_entry.get().find("'") != -1 :
            messagebox.showerror("Error", f"Unauthorized characters in URL.")
            print(self.select_video_url_entry.get(), self.select_video_url_entry.get().find(" "), self.select_video_url_entry.get().find("/"), self.select_video_url_entry.get().find("\\"))
            self.add_video_window.focus()
            return
        # print(self.select_video_description_entry.get(1.0, tk.END).strip())

        self.copy_video(self.add_video_path_to_video, self.select_video_url_entry.get())
        self.copy_thumbnail(self.add_video_path_to_thumbnail_img, self.select_video_url_entry.get())
        self.add_video_save_metadata(self.select_video_url_entry.get(),
                                     self.select_video_title_entry.get(),
                                     self.select_video_description_entry.get(1.0, tk.END).strip(),
                                     self.select_video_author_entry.get())

        messagebox.showinfo("Next", "The next step is to update the database via your channel page.")

        self.add_video_window.focus()
        self.add_video_window.destroy()
    
    def cancel_add_video(self):
        self.add_video_path_to_thumbnail_img = ""
        self.add_video_path_to_video = ""
        self.add_video_window.destroy()
    
    def copy_video(self, video_path, url):
        dest_video_path = os.path.join(self.video_dir, f"{url}.mp4")
        try:
            # Copier la video vers le dossier 'Video' avec le bon nom
            shutil.copy2(video_path, dest_video_path)
            messagebox.showinfo("Success", "Video saved with success!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save video : {e}")

    def copy_thumbnail(self, thumbnail_path, url):
        dest_thumbnail_path = os.path.join(self.thumbnail_dir, f"{url}.png")
        try:
            # Copier la video vers le dossier 'Video' avec le bon nom
            shutil.copy2(thumbnail_path, dest_thumbnail_path)
            messagebox.showinfo("Success", "Thumbnail saved with success!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save thumbnail : {e}")

    def add_video_save_metadata(self, url, title, description, author):
        meta_file = os.path.join(self.meta_dir, f"{url}.json")
        metadata = {
            "title": title,
            "descritpion": description,
            "author": author
        }
        with open(meta_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=4)
        messagebox.showinfo("Success", "Métadonnées sauvegardées avec succès!")

if __name__ == "__main__":
    root = tk.Tk()
    app = VideoEditorApp(root)
    root.mainloop()
