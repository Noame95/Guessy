import io
import tkinter as tk
from tkinter import filedialog, Label, Canvas, Frame, messagebox
import win32clipboard
from PIL import Image, ImageTk, ImageDraw
import os
import pygame


class MainWindow:
    def __init__(self):
        self.window = tk.Tk()
        pygame.mixer.init()
        self.PRESS_SOUND = "press.wav"
        self.FOLDER_IMG = "folder.png"
        self.window.title("Guessy")
        self.window.geometry("1200x1000")
        self.window.config(bg="#121858")

        self.INSTRUCTIONS_CHANNEL = "Instructions 📜📜"
        self.GUESS_UPLOAD_CHANNEL = "Guess-Upload 💾🖼️"
        self.GUESS_PAINT_CHANNEL = "Guess-Paint 🎨🖌"
        self.MY_FOLDER_CHANNEL = "My Folder 🗂🔒"
        self.OTHERS_FOLDERS_CHANNEL = "Other's Folders 🗂🌍"

        self.NO_FILES_AVAILABLE = "No files here."
        self.NO_FOLDERS_AVAILABLE = "No folders here."

        self.INSTRUCTIONS_CONTENT = (
            "Welcome to Guessy! 🧠✍️\n"
            "Guessy will try to recognize the letter or number you've written.\n"
            "Before using Guessy, make sure your handwriting is as clear and readable as possible.\n"
            "If you're uploading a photo from a notebook, we recommend scanning it first for better accuracy.\n"
            "Guessy might not always get your character right — and that's okay!\n"
            "You're welcome to leave feedback to let us know.\n"
            "By the way, the name of your files work like that: character-guessed_number-of-character-guessed\n"

            "Have fun and enjoy using Guessy! 😊\n\n"
        )

        main_frame = tk.Frame(self.window, bg="#1A237E")
        main_frame.pack(fill="both", expand=True)

        self.sidebar = tk.Frame(main_frame, bg="#0E144E", width=220)
        self.sidebar.pack(side="left", fill="y")

        content_frame = tk.Frame(main_frame, bg="#1A237E")
        content_frame.pack(side="right", fill="both", expand=True)

        self.canvas = Canvas(content_frame, bg="#1A237E")
        scrollbar = tk.Scrollbar(content_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = Frame(self.canvas, bg="#1A237E")

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.window.bind("<MouseWheel>", self.mouse_wheel)
        self.file_label = None
        self.paint_canvas = None
        self.brush_size = tk.IntVar(value=20)  # עוצמת ברירת מחדל
        self.send_button = None
        self.upload_button = None
        self.paint_canvas = None
        self.uploaded_file_data = None  # המידע של הקובץ שעלה
        self.current_channel = None  # הערוץ הנוכחי שהלקוח נמצא בו
        self.files_list = None  # רשימת הקבצים שצריכים לראות בגרפיקה
        self.has_loaded_files = False  # האם הקבצים נטענו כך שנוכל להעתיק או להוריד אותם?
        self.folders_list = None  # התיקיות שצריכים לראות בגרפיקה
        self.has_loaded_folders = False  # האם התיקיות נטענו כך שנוכל להכנס אליהם?
        self.selected_other_folder_name = None  # איזו תיקייה הלקוח בחר מבין שאר המשתמשים?
        self.deleted_file = None  # מהו הקובץ שהלקוח רוצה להגיד לשרת למחוק?
        self.waiting_for_reaction = False  # האם הלקוח צריך להגיד לשרת אם צדק או לא? כלומר, האם אסור לו לעבור ערוצים ברגע זה?

        self.channels = {
            self.INSTRUCTIONS_CHANNEL: self.show_instructions,
            self.GUESS_UPLOAD_CHANNEL: self.show_guess_upload,
            self.GUESS_PAINT_CHANNEL: self.show_guess_paint,
            self.MY_FOLDER_CHANNEL: self.show_file_thumbnails,
            self.OTHERS_FOLDERS_CHANNEL: self.show_other_folders
        }

        for name, command in self.channels.items():
            button = tk.Button(self.sidebar, text=name, command=lambda cmd=command, channel_name=name: (
                pygame.mixer.Sound(self.PRESS_SOUND).play(),
                self.set_current_channel(channel_name) if not self.waiting_for_reaction else messagebox.showwarning(
                    "Hold up!", "You need to react (like/dislike) before switching channels!"),
                cmd() if not self.waiting_for_reaction else None),
                               font=("Segoe UI", 12, "bold"), bg="#1C2C68", fg="white", relief="flat", padx=12, pady=8,
                               activebackground="#3949AB", activeforeground="white", bd=0)
            button.pack(fill="x", pady=5, padx=5)

        self.set_current_channel(self.INSTRUCTIONS_CHANNEL)
        self.show_instructions()
        self.reaction_var = tk.StringVar()

    def set_current_channel(self, name):
        if name != self.current_channel:
            self.has_loaded_files = False
            self.has_loaded_folders = False
        self.current_channel = name

    def refresh_current_channel(self):
        if self.current_channel and self.current_channel in self.channels:
            self.channels[self.current_channel]()

    def mouse_wheel(self, event):
        self.canvas.yview_scroll(-1 * (event.delta // 120), "units")

    def show_instructions(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        label = tk.Label(self.scrollable_frame, text=self.INSTRUCTIONS_CONTENT, font=("Helvetica", 16), bg="#1A237E", fg="#E3F2FD",
                         anchor="w", justify="left")
        label.pack(pady=20, padx=20)

    def show_guess_upload(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        title_label = tk.Label(self.scrollable_frame, text="Check Your Letter", font=("Segoe UI", 22, "bold"),
                               bg="#1A237E", fg="#00E676")
        title_label.pack(pady=20)
        frame = tk.Frame(self.scrollable_frame, bg="#004D40", bd=2, relief="ridge")
        frame.pack(pady=20, padx=20, fill="both", expand=True)
        self.upload_button = tk.Button(frame, text="Upload File", command=self.upload_click, bg="#00C853", fg="white", activebackground="#66BB6A",
                             font=("Segoe UI", 12, "bold"), relief="flat", padx=12, pady=6)
        self.upload_button.pack(pady=20)
        self.file_label = tk.Label(frame, text="No file selected", font=("Helvetica", 12), bg="#004D40", fg="#E0F2F1")
        self.file_label.pack()
        self.image_label = Label(frame, bg="#004D40")
        self.image_label.pack(pady=10)

    def show_guess_paint(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        title_label = tk.Label(self.scrollable_frame, text="Draw Your Letter", font=("Helvetica", 20, "bold"),
                               bg="#1A237E", fg="#4CAF50")
        title_label.pack(pady=20)
        self.paint_canvas = Canvas(self.scrollable_frame, width=400, height=300, bg="#FAFAFA", bd=2, relief="sunken")
        self.paint_canvas.pack(pady=10)
        slider_frame = tk.Frame(self.scrollable_frame, bg="#1A237E")
        slider_frame.pack(pady=5)

        slider_label = tk.Label(slider_frame, text="Brush Size:", bg="#1A237E", fg="#E3F2FD", font=("Segoe UI", 12))
        slider_label.pack(side="left", padx=(0, 10))

        brush_slider = tk.Scale(
            slider_frame, from_=5, to=50, orient="horizontal",
            variable=self.brush_size, bg="#3949AB", fg="white",
            troughcolor="#7986CB", highlightthickness=0,
            sliderrelief="flat", length=200
        )
        brush_slider.pack(side="left")
        self.paint_canvas.bind("<B1-Motion>", self.paint)
        clear_button = tk.Button(self.scrollable_frame, text="Clear", command=self.clear_canvas, bg="#D32F2F",
                                 fg="white", activebackground="#F44336", font=("Segoe UI", 12, "bold"), relief="flat",
                                 padx=12, pady=6)

        clear_button.pack(pady=10)
        self.send_button = tk.Button(self.scrollable_frame, text="Send", command=self.send_click,
                                     bg="#00C853", fg="white", activebackground="#66BB6A",
                                     font=("Segoe UI", 12, "bold"), relief="flat", padx=12, pady=6)
        self.send_button.pack(pady=10)

    def paint(self, event):
        brush_size = self.brush_size.get()
        x, y = event.x, event.y
        self.paint_canvas.create_oval(
            x - brush_size // 2, y - brush_size // 2,
            x + brush_size // 2, y + brush_size // 2,
            fill="black", outline="black"
        )

    def clear_canvas(self):
        self.paint_canvas.delete("all")

    def save_paint(self):
        width = self.paint_canvas.winfo_width()
        height = self.paint_canvas.winfo_height()
        img = Image.new("RGB", (width, height), color="white")
        draw = ImageDraw.Draw(img)
        self.paint_canvas.update_idletasks()
        for item in self.paint_canvas.find_all():
            coords = self.paint_canvas.coords(item)
            if len(coords) == 4:
                x1, y1, x2, y2 = coords
                draw.ellipse([x1, y1, x2, y2], outline="black", fill="black")
        paint_name = "drawn_image.png"
        img.save(paint_name, format="PNG")
        with open(paint_name, "rb") as f:
            self.uploaded_file_data = f.read()
        os.remove(paint_name)
        print("Drawing saved and deleted!")
        print(f"File size (before deletion): {len(self.uploaded_file_data)} bytes")

    def upload_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Images", "*.png;*.jpg;*.jpeg;*.gif;*.bmp")])
        if file_path:
            with open(file_path, "rb") as f:
                self.uploaded_file_data = f.read()
            print(f"Uploaded file: {file_path}")
            print(f"File size: {len(self.uploaded_file_data)} bytes")
            self.file_label.config(text=os.path.basename(file_path))
            self.display_image(file_path)

    def display_image(self, file_path):
        image = Image.open(file_path)
        image = image.resize((250, 250), Image.LANCZOS)
        img = ImageTk.PhotoImage(image)
        self.image_label.config(image=img)

    def check_char(self, char):
        if not self.uploaded_file_data:
            return None
        if self.current_channel == self.GUESS_PAINT_CHANNEL:
            self.send_button.config(state="disabled")
        if self.current_channel == self.GUESS_UPLOAD_CHANNEL:
            self.upload_button.config(state="disabled")
        self.reaction_var.set("")
        self.show_typing_effect(f"✔️ The letter/number is: {char}", font=("Courier", 20), fg="#76FF03")
        self.show_like_dislike_buttons()
        self.waiting_for_reaction = True
        self.window.wait_variable(self.reaction_var)
        self.waiting_for_reaction = False
        return self.reaction_var.get()

    def show_file_thumbnails(self):
        self.clear_scrollable_frame()

        if isinstance(self.files_list, str):
            self.display_empty_message()
            return

        thumb_size = 150
        padding = 18
        columns = 5

        for idx, (filename, filedata) in enumerate(self.files_list):
            row, col = divmod(idx, columns)
            container = self.create_thumbnail_container(row, col, padding)

            photo = self.create_thumbnail_image(filedata, thumb_size)
            self.add_image_to_container(container, photo, filedata, filename)
            self.add_filename_label(container, filename)
            self.bind_image_events(container, filedata, filename)

    def show_other_folders(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        if not self.folders_list:
            label = tk.Label(self.scrollable_frame, text=self.NO_FOLDERS_AVAILABLE, font=("Helvetica", 16),
                             bg="#1A237E", fg="white")
            label.pack(pady=20)
            return

        thumb_size = 100
        padding = 20
        folder_icon = Image.open(self.FOLDER_IMG)
        folder_icon.thumbnail((thumb_size, thumb_size))
        folder_photo = ImageTk.PhotoImage(folder_icon)

        for idx, folder_name in enumerate(self.folders_list):
            row = idx // 4
            col = idx % 4

            container = tk.Frame(self.scrollable_frame, bd=2, relief="groove", bg="#0D47A1")
            container.grid(row=row, column=col, padx=padding, pady=padding)

            img_label = tk.Label(container, image=folder_photo, bg="#0D47A1")
            img_label.image = folder_photo
            img_label.pack()
            img_label.bind(
                "<Button-1>",
                lambda event, folder=folder_name: self.folder_clicked(folder)
            )

            name_label = tk.Label(container, text=folder_name, font=("Helvetica", 10), bg="#0D47A1", fg="white")
            name_label.pack()
            name_label.bind(
                "<Button-1>",
                lambda event, folder=folder_name: self.folder_clicked(folder)
            )

    def folder_clicked(self, folder_name):
        self.selected_other_folder_name = folder_name
        print(self.selected_other_folder_name)

    def clear_scrollable_frame(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

    def display_empty_message(self):
        label = tk.Label(
            self.scrollable_frame,
            text=self.NO_FILES_AVAILABLE,
            font=("Helvetica", 16),
            bg="#1A237E",
            fg="white"
        )
        label.pack(pady=20)

    def create_thumbnail_container(self, row, col, padding):
        print(row)
        print(col)
        container = tk.Frame(self.scrollable_frame, bd=2, relief="groove", bg="#0D47A1")
        container.grid(row=row, column=col, padx=padding, pady=padding)
        return container

    def create_thumbnail_image(self, filedata, size):
        img = Image.open(io.BytesIO(filedata))
        img.thumbnail((size, size))
        return ImageTk.PhotoImage(img)

    def add_image_to_container(self, container, photo, filedata, filename):
        img_label = tk.Label(container, image=photo, bg="#0D47A1")
        img_label.image = photo
        img_label.pack()

        img_label.bind(
            "<Button-1>",
            lambda e: self.open_image_window(filedata, filename)
        )
        img_label.bind(
            "<Button-3>",
            lambda e: self.show_context_menu(e, filename)
        )

    def add_filename_label(self, container, filename):
        label = tk.Label(container, text=filename, font=("Helvetica", 10), bg="#0D47A1", fg="white")
        label.pack()

    def open_image_window(self, img_data, name):
        top = tk.Toplevel(self.window)
        top.title(name)
        img = Image.open(io.BytesIO(img_data))
        photo = ImageTk.PhotoImage(img)
        label = tk.Label(top, image=photo)
        label.image = photo
        label.pack()

    def show_context_menu(self, event, filename):
        menu = tk.Menu(self.window, tearoff=0)
        menu.add_command(label="Copy", command=lambda: self.copy_image(filename))
        menu.add_command(label="Download", command=lambda: self.download_image(filename))
        if self.current_channel == self.MY_FOLDER_CHANNEL:
            menu.add_command(label="Delete", command=lambda: self.delete_image(filename))
        menu.post(event.x_root, event.y_root)

    def bind_image_events(self, container, filedata, filename):
        for widget in container.winfo_children():
            widget.bind("<Button-1>", lambda e: self.open_image_window(filedata, filename))
            widget.bind("<Button-3>", lambda e: self.show_context_menu(e, filename))

    def copy_image(self, name):
        for filename, filedata in self.files_list:
            if filename == name:
                try:
                    image = Image.open(io.BytesIO(filedata))
                    output = io.BytesIO()
                    image.convert("RGB").save(output, "BMP")
                    data = output.getvalue()[14:]  # removing a header
                    output.close()
                    win32clipboard.OpenClipboard()
                    win32clipboard.EmptyClipboard()
                    win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
                    win32clipboard.CloseClipboard()
                    messagebox.showinfo("Success", f"Image {name} copied to clipboard.")
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to copy image: {e}")
                return

        messagebox.showerror("Error", f"File {name} not found.")

    def delete_image(self, name):
        self.files_list = [file for file in self.files_list if file[0] != name]
        messagebox.showinfo("Success", f"Image {name} deleted successfully.")
        self.deleted_file = name

    def download_image(self, name):
        try:
            for filename, filedata in self.files_list:
                if filename == name:
                    file_path = filedialog.asksaveasfilename(defaultextension=".png", initialfile=name)
                    if file_path:
                        with open(file_path, 'wb') as f:
                            f.write(filedata)
                        messagebox.showinfo("Success", f"Image {name} downloaded successfully.")
                    return
            messagebox.showerror("Error", f"File {name} not found.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to download {name}: {e}")

    def show_typing_effect(self, text, font, fg):
        label = tk.Label(self.scrollable_frame, text="", font=font, bg="#1A237E", fg=fg)
        label.pack(pady=20)
        self.type_text(label, text, 0)

    def type_text(self, label, text, i):
        if i <= len(text):
            label.config(text=text[:i])
            self.window.after(50, lambda: self.type_text(label, text, i + 1))

    def show_like_dislike_buttons(self):
        like_button = tk.Button(self.scrollable_frame, text="👍 Like", command=self.like, font=("Helvetica", 12),
                                bg="#66BB6A", fg="white")
        like_button.pack(pady=10)

        dislike_button = tk.Button(self.scrollable_frame, text="👎 Dislike", command=self.dislike,
                                   font=("Helvetica", 12), bg="#EF5350", fg="white")
        dislike_button.pack(pady=10)

    def send_click(self):
        self.send_button.config(state="disabled")
        self.save_paint()

    def upload_click(self):
        self.upload_button.config(state="disabled")
        self.upload_file()

    def like(self):
        self.reaction_var.set("Like")
        if self.current_channel == self.GUESS_PAINT_CHANNEL:
            self.send_button.config(state="normal")
        if self.current_channel == self.GUESS_UPLOAD_CHANNEL:
            self.upload_button.config(state="normal")
        self.refresh_current_channel()

    def dislike(self):
        self.reaction_var.set("Dislike")
        if self.current_channel == self.GUESS_PAINT_CHANNEL:
            self.send_button.config(state="normal")
        if self.current_channel == self.GUESS_UPLOAD_CHANNEL:
            self.upload_button.config(state="normal")
        self.refresh_current_channel()
