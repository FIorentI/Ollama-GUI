import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
import ollama
import GPUtil
import psutil

# Dictionary of available models
models = {
    'llama3.1': 'llama3.1',
    'llama3.1_70b': 'llama3.1:70b',
    'llama3.1_405b': 'llama3.1:405b',
    'phi3_mini': 'phi3',
    'phi3_medium': 'phi3:medium',
    'gemma2': 'gemma2',
    'gemma2_27b': 'gemma2:27b',
    'mistral': 'mistral',
    'moondream2': 'moondream',
    'neural_chat': 'neural-chat',
    'starling': 'starling-lm',
    'codellama': 'codellama',
    'llama2_uncensored': 'llama2-uncensored',
    'llava': 'llava',
    'solar': 'solar',
    'mario': 'mario'
}


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("Ollama Interface")
        self.root.geometry("800x600")
        ctk.set_appearance_mode("system")

        self.model_var = tk.StringVar(value='llama3.1')
        self.mode_var = tk.StringVar(value='generate')
        self.conversation_history = []

        self.create_sidebar()
        self.create_main_area()
        self.create_input_area()

        self.update_status()

    def create_sidebar(self):
        self.sidebar = ctk.CTkFrame(self.root, width=200)
        self.sidebar.pack(side="left", fill="y")

        ctk.CTkButton(self.sidebar, text="Select Model", command=self.select_model).pack(pady=5, fill="x")
        ctk.CTkButton(self.sidebar, text="Select Mode", command=self.select_mode).pack(pady=5, fill="x")
        ctk.CTkButton(self.sidebar, text="Reset Context", command=self.reset_context).pack(pady=5, fill="x")
        self.dark_mode_switch = ctk.CTkSwitch(self.sidebar, text="Dark Mode", command=self.toggle_dark_mode)
        self.dark_mode_switch.pack(pady=5, fill="x")

        # Create a frame for the status labels and place it at the bottom
        self.status_frame = ctk.CTkFrame(self.sidebar)
        self.status_frame.pack(side="bottom", pady=10, padx=10, fill="x")

        self.cpu_label = ctk.CTkLabel(self.status_frame, text="CPU Usage: 0%")
        self.cpu_label.pack(anchor="w")  # Align to the left

        self.gpu_label = ctk.CTkLabel(self.status_frame, text="GPU Usage: 0%")
        self.gpu_label.pack(anchor="w")  # Align to the left

    def create_main_area(self):
        self.main_frame = ctk.CTkFrame(self.root)
        self.main_frame.pack(side="left", fill="both", expand=True, padx=20, pady=20)

        self.scroll_frame = ctk.CTkFrame(self.main_frame)
        self.scroll_frame.pack(fill="both", expand=True)

        canvas_bg = "white" if ctk.get_appearance_mode() == "Light" else "black"
        self.canvas = tk.Canvas(self.scroll_frame, bg=canvas_bg, highlightthickness=0)
        self.scrollbar = ctk.CTkScrollbar(self.scroll_frame, orientation="vertical", command=self.canvas.yview)
        self.scrollable_frame = ctk.CTkFrame(self.canvas)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="both")

    def create_input_area(self):
        self.input_frame = ctk.CTkFrame(self.main_frame)
        self.input_frame.pack(fill="x", pady=10)

        self.prompt_entry = ctk.CTkEntry(self.input_frame)
        self.prompt_entry.pack(side="left", padx=10, pady=10, fill="x", expand=True)

        self.submit_button = ctk.CTkButton(self.input_frame, text="Submit", command=self.submit)
        self.submit_button.pack(side="left", padx=10, pady=10)

    def update_status(self):
        cpu_usage = round(psutil.cpu_percent())
        gpus = GPUtil.getGPUs()
        if gpus:
            gpu_usage = round(gpus[0].load * 100)  # Assuming single GPU for simplicity
        else:
            gpu_usage = 0

        self.cpu_label.configure(text=f"CPU Usage: {cpu_usage}%")
        self.gpu_label.configure(text=f"GPU Usage: {gpu_usage}%")

        self.root.after(1000, self.update_status)  # Update status every second

    def select_model(self):
        model_window = tk.Toplevel(self.root)
        model_window.title("Select Model")

        for model in models.keys():
            ctk.CTkButton(model_window, text=model, command=lambda m=model: self.set_model(m)).pack(pady=5, padx=10,
                                                                                                    fill="x")

    def set_model(self, model):
        self.model_var.set(model)
        messagebox.showinfo("Model Selected", f"Model set to: {model}")

    def select_mode(self):
        mode_window = tk.Toplevel(self.root)
        mode_window.title("Select Mode")

        for mode in ['generate', 'chat', 'code']:
            ctk.CTkButton(mode_window, text=mode, command=lambda m=mode: self.set_mode(m)).pack(pady=5, padx=10,
                                                                                                fill="x")

    def set_mode(self, mode):
        self.mode_var.set(mode)
        messagebox.showinfo("Mode Selected", f"Mode set to: {mode}")

    def toggle_dark_mode(self):
        if self.dark_mode_switch.get() == 1:
            ctk.set_appearance_mode("dark")
        else:
            ctk.set_appearance_mode("light")

        self.update_canvas_bg()

    def update_canvas_bg(self):
        canvas_bg = "white" if ctk.get_appearance_mode() == "Light" else "black"
        self.canvas.configure(bg=canvas_bg)

    def reset_context(self):
        self.conversation_history = []
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        messagebox.showinfo("Context Reset", "Conversation context has been reset.")

    def submit(self):
        prompt = self.prompt_entry.get().strip()
        if not prompt:
            messagebox.showwarning("Input Error", "Prompt cannot be empty")
            return

        model_key = self.model_var.get()
        model_name = models[model_key]
        mode = self.mode_var.get()

        if mode == 'generate' or mode == 'code':
            combined_prompt = "\n".join([entry['content'] for entry in
                                         self.conversation_history]) + "\n" + prompt if self.conversation_history else prompt
            response = self.generate(model_name, combined_prompt)
            self.conversation_history.extend(
                [{'role': 'user', 'content': prompt}, {'role': 'assistant', 'content': response['response']}])
            self.display_output('You', prompt)
            self.display_output(f'{model_name}', response['response'], is_code=(mode == 'code'))
        else:
            self.conversation_history.append({'role': 'user', 'content': prompt})
            response = self.chat(model_name, self.conversation_history)
            self.conversation_history.append({'role': 'assistant', 'content': response['message']['content']})
            self.display_output('You', prompt)
            self.display_output(f'{model_name}', response['message']['content'])

        self.prompt_entry.delete(0, tk.END)

    def display_output(self, role, content, is_code=False):
        bg_color = "#D3D3D3"
        text_color = "black"
        anchor = "w" if role == 'Support Bot' else "e"

        bubble = ctk.CTkFrame(self.scrollable_frame, fg_color=bg_color, corner_radius=10)
        bubble.pack(anchor=anchor, pady=5, padx=10, fill="both", expand=True)

        font = ('Courier New', 10, 'bold') if is_code else ('Calibri', 10, 'bold')
        ctk.CTkLabel(bubble, text=role, font=font, text_color=text_color).pack(anchor="w", padx=10, pady=5, fill="both",
                                                                               expand=True)

        content_font = ('Courier New', 10) if is_code else ('Calibri', 10)

        text_widget = tk.Text(bubble, wrap="word", font=content_font, bg=bg_color, fg=text_color, bd=0, padx=10, pady=5)
        text_widget.insert("1.0", content)
        text_widget.config(state=tk.DISABLED)

        # Calculate required height based on content
        num_lines = content.count('\n') + 1
        text_widget.config(height=num_lines)
        text_widget.pack(fill="both", expand=True)

        self.canvas.update_idletasks()
        self.canvas.yview_moveto(1)

    def generate(self, model, prompt):
        try:
            return ollama.generate(model=model, prompt=prompt)
        except Exception as e:
            messagebox.showerror("Generation Error", str(e))
            return {'response': ''}

    def chat(self, model, messages):
        try:
            return ollama.chat(model=model, messages=messages, stream=False)
        except Exception as e:
            messagebox.showerror("Chat Error", str(e))
            return {'message': {'content': ''}}


if __name__ == "__main__":
    root = ctk.CTk()
    app = App(root)
    root.mainloop()

