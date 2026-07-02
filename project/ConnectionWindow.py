import tkinter as tk


class ConnectionWindow:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("GUESSY")
        self.window.geometry("400x600")
        self.window.config(bg="#f5f5f5")  # background - white
        self.make_main()
        self.username_entry = None
        self.password_entry = None
        self.email_entry = None
        self.submitted = False
        self.username_val = None
        self.password_val = None
        self.email_val = None
        self.sign_or_log = None
        self.error_message = None
        self.back_button = None

    def clear_screen(self):
        for widget in self.window.winfo_children():
            widget.destroy()

    def make_main(self):
        title = tk.Label(self.window, text="GUESSY", font=('Brush Script MT', 30, 'bold'), bg="#f5f5f5", fg="#4CAF50")
        title.pack(pady=40)
        self.sign_up_button = tk.Button(self.window, text="Sign Up", command=self.show_sign_up,
                                        width=20, height=2, font=('Helvetica', 12), bg="#4CAF50", fg="white", bd=0,
                                        relief="solid", padx=10, pady=5)
        self.sign_up_button.pack(pady=15)

        self.log_in_button = tk.Button(self.window, text="Log In", command=self.show_log_in,
                                       width=20, height=2, font=('Helvetica', 12), bg="#2196F3", fg="white", bd=0,
                                       relief="solid", padx=10, pady=5)
        self.log_in_button.pack(pady=10)

    def show_sign_up(self):
        self.sign_or_log = "SIGNUP"  # Sign Up
        self.clear_screen()
        sign_up_title = tk.Label(self.window, text="Sign Up", font=('Helvetica', 20, 'bold'), bg="#f5f5f5")
        sign_up_title.pack(pady=20)
        self.make_fields_and_buttons()

    def show_log_in(self):
        self.sign_or_log = "LOGIN"  # Log In
        self.clear_screen()
        log_in_title = tk.Label(self.window, text="Log In", font=('Helvetica', 20, 'bold'), bg="#f5f5f5")
        log_in_title.pack(pady=20)
        self.make_fields_and_buttons()

    def submit(self):
        self.username_val = self.username_entry.get()
        self.password_val = self.password_entry.get()
        self.email_val = self.email_entry.get()
        self.submitted = True
        print(f"Mode: {self.sign_or_log}, Username: {self.username_val}, Password: {self.password_val}, Email: {self.email_val}")

    def make_fields_and_buttons(self):
        self.username_label = tk.Label(self.window, text="Username:", font=('Helvetica', 12), bg="#f5f5f5")
        self.username_label.pack(pady=5)
        self.username_entry = tk.Entry(self.window, font=('Helvetica', 12), bd=2, relief="solid")
        self.username_entry.pack(pady=10, ipadx=10, ipady=5)

        self.password_label = tk.Label(self.window, text="Password:", font=('Helvetica', 12), bg="#f5f5f5")
        self.password_label.pack(pady=5)
        self.password_entry = tk.Entry(self.window, show="*", font=('Helvetica', 12), bd=2, relief="solid")
        self.password_entry.pack(pady=10, ipadx=10, ipady=5)

        self.email_label = tk.Label(self.window, text="Email:", font=('Helvetica', 12), bg="#f5f5f5")
        self.email_label.pack(pady=5)
        self.email_entry = tk.Entry(self.window, font=('Helvetica', 12), bd=2, relief="solid")
        self.email_entry.pack(pady=10, ipadx=10, ipady=5)

        submit_button = tk.Button(self.window, text="Submit", command=self.submit, width=20, height=2,
                                  font=('Helvetica', 12), bg="#4CAF50", fg="white", bd=0, relief="solid")
        submit_button.pack(pady=20)

        self.back_button = tk.Button(self.window, text="Back", command=self.back_to_main,
                                     width=20, height=2, font=('Helvetica', 12), bg="#f44336", fg="white", bd=0,
                                     relief="solid")
        self.back_button.pack(pady=10)

        self.error_message = tk.Label(self.window, text="", font=('Helvetica', 10, 'bold'),
                                      bg="#f5f5f5", fg="red", wraplength=350, justify="center")
        self.error_message.pack(pady=(20, 10), side="bottom")

    def reset_val(self, value):
        value.delete(0, tk.END)
        value.insert(0, '')

    def update(self):
        self.window.update_idletasks()
        self.window.update()

    def back_to_main(self):
        self.clear_screen()
        self.make_main()
