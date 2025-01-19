import requests
import json
import tkinter as tk
from tkinter import scrolledtext, filedialog, messagebox
from tkinter import ttk
from PIL import Image, ImageTk  # Ensure Pillow is installed for image handling

preprompt = """ Act as an expert OpenSCAD application. Generate optimized, error-free OpenSCAD code that visually resembles the specified object. 
- Ensure the object is realistic and connected appropriately (e.g., wheels attached to the body for cars, structural elements in houses).
- Ensure that the output is valid OpenSCAD syntax, with all statements properly formatted.
- Avoid syntax errors, missing semicolons, and unmatched brackets.
- Only output the SCAD code, without any extra text or formatting. """

verification_prompt = """ Now that you have generated the OpenSCAD code, please verify its correctness.
    Check for realistic representation (e.g., objects should be visually attached and functional in form, like wheels attached to the car).
    If any errors or misrepresentations are found, correct them before outputting the final code. 
    Check for any syntax errors, missing semicolons, or other issues that may prevent the code from running properly.
    If any errors are found, correct them before outputting the final code. 
    Ensure that the output is valid OpenSCAD syntax, with all statements properly formatted.
    Only output the SCAD code, without any extra text, comments, or formatting (no orscad, etc.).
    Use concise and optimized SCAD syntax that will run without errors in the latest OpenSCAD version.
    """


class OllamaAPI:
    def __init__(self, host='127.0.0.1', port=11434):
        self.host = host
        self.port = port
        self.base_url = f"http://{self.host}:{self.port}"

    def check_connection(self):
        try:
            url = f"{self.base_url}/api/generate"
            payload = {
                "model": "llama3.2",
                "prompt": "Test connection."
            }
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            print("Connection successful.")
            return True
        except requests.exceptions.HTTPError as e:
            print(f"HTTP error during connection check: {e}")
            return False
        except requests.exceptions.RequestException as e:
            print(f"Connection error: {e}")
            return False

    def query(self, prompt):
        try:
            url = f"{self.base_url}/api/generate"
            payload = {
                "model": "llama3",
                "prompt": preprompt + prompt,
                "stream": False
            }
            response = requests.post(url, json=payload, timeout=300)
            response.raise_for_status()
            try:
                result = response.json()
                return result
            except json.JSONDecodeError as json_err:
                print(f"JSON decode error: {json_err}")
                print("Response content that caused the error:", response.text)
                return None
        except requests.exceptions.HTTPError as e:
            print(f"Error querying Ollama: {e}")
            if e.response.status_code == 404:
                print("Error 404: The endpoint may not exist. Please check your API URL.")
            else:
                print(f"Error: {e.response.text}")
            return None
        except requests.exceptions.RequestException as e:
            print(f"Error querying Ollama: {e}")
            return None


class Text2CADApp:
    def __init__(self, root):
        self.root = root
        self.root.title("CAD Generator")
        self.root.geometry("800x600")
        self.create_widgets()
        self.api = OllamaAPI()
        if not self.api.check_connection():
            self.output_box.insert(tk.END, "Failed to connect to Ollama API.\n")

    def create_widgets(self):
        # Header
        self.header = tk.Frame(self.root, bg="#3b5998")
        self.header.pack(fill=tk.X)

        # Logo
        self.header_label = tk.Label(self.header, text=" CAD Generator", bg="#3b5998", fg="white", font=("Arial", 16))
        self.header_label.pack(side=tk.LEFT, padx=5)

        # Main frame
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(expand=True, fill=tk.BOTH)

        # Sidebar
        self.sidebar = tk.Frame(self.main_frame, bg="#333333", width=200)  # Darker background for contrast
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)

        self.toggle_button = tk.Button(self.sidebar, text="➕", command=self.toggle_sidebar, borderwidth=0, bg="#333333", fg="white", font=("Arial", 12))
        self.toggle_button.pack(pady=5)

        self.settings_frame = tk.Frame(self.sidebar, bg="#444444")  # Matching background color
        self.settings_frame.pack(pady=5, padx=5)

        self.host_label = tk.Label(self.settings_frame, text="Host:", fg="white", bg="#444444", font=("Arial", 10))
        self.host_label.grid(row=0, column=0, sticky="w")
        self.host_entry = tk.Entry(self.settings_frame, width=20)
        self.host_entry.insert(0, '127.0.0.1')
        self.host_entry.grid(row=0, column=1)

        self.port_label = tk.Label(self.settings_frame, text="Port:", fg="white", bg="#444444", font=("Arial", 10))
        self.port_label.grid(row=1, column=0, sticky="w")
        self.port_entry = tk.Entry(self.settings_frame, width=5)
        self.port_entry.insert(0, '11434')
        self.port_entry.grid(row=1, column=1)

        self.file_button = tk.Button(self.settings_frame, text="Select Output File", command=self.select_file, bg="#3b5998", fg="white", font=("Arial", 10))
        self.file_button.grid(row=2, columnspan=2, pady=5)

        self.output_format_label = tk.Label(self.settings_frame, text="Select Output Format:", fg="white", bg="#444444", font=("Arial", 10))
        self.output_format_label.grid(row=4, columnspan=2)

        self.output_format_var = tk.StringVar(value="SCAD")
        self.output_format_dropdown = ttk.Combobox(self.settings_frame, textvariable=self.output_format_var,
                                                   values=["SCAD", "STL"])
        self.output_format_dropdown.grid(row=5, columnspan=2)

        # Prompt input area
        self.prompt_label = tk.Label(self.main_frame, text="Enter your prompt:")
        self.prompt_label.pack(pady=10)

        self.prompt_entry = tk.Text(self.main_frame, wrap=tk.WORD, height=10)
        self.prompt_entry.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)

        # Bind Enter key to submit the prompt
        self.prompt_entry.bind("<Return>", lambda event: self.submit_prompt())

        # Output box (ScrolledText)
        self.output_box = scrolledtext.ScrolledText(self.main_frame, wrap=tk.WORD, height=15)
        self.output_box.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        # Footer
        self.footer = tk.Frame(self.root, bg="#3b5998")
        self.footer.pack(side=tk.BOTTOM, fill=tk.X)
        self.footer_label = tk.Label(self.footer, text="© 2025 CAD Generator", bg="#3b5998", fg="white", font=("Arial", 10))
        self.footer_label.pack(pady=5)

    def toggle_sidebar(self):
        if self.settings_frame.winfo_viewable():
            self.settings_frame.pack_forget()
            self.toggle_button.config(text="➕")
        else:
            self.settings_frame.pack(pady=5, padx=5)
            self.toggle_button.config(text="➖")

    def select_file(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".scad",
                                                 filetypes=[("SCAD Files", "*.scad"), ("STL Files", "*.stl"),
                                                            ("All Files", "*.*")])
        if file_path:
            self.file_button.config(text=file_path)

    def submit_prompt(self):
        prompt = self.prompt_entry.get("1.0", tk.END).strip()  # Get multiline text
        if prompt == "":
            messagebox.showwarning("Input Error", "Please enter a prompt.")
            return
        full_prompt = preprompt + prompt  # Combine the updated preprompt with the user prompt
        response = self.api.query(full_prompt)  # Send the complete prompt to the API

        if response:
            # Extract and display the SCAD code
            scad_code = response.get('response', 'No SCAD code returned.')
            self.output_box.delete(1.0, tk.END)  # Clear previous output
            self.output_box.insert(tk.END, scad_code)  # Display new response

            # Pass the generated code to AI for verification and correction
            while True:
                verification_response = self.api.query(scad_code + verification_prompt)
                if verification_response:
                    verified_code = verification_response.get('response', 'No verified SCAD code returned.')

                    # Check if the AI indicates that the code is error-free
                    if "free of syntax errors" in verified_code:
                        self.output_box.delete(1.0, tk.END)  # Clear previous output
                        self.output_box.insert(tk.END, verified_code)  # Display the final verified SCAD code
                        break
                    else:
                        # Show the verified code
                        self.output_box.delete(1.0, tk.END)
                        self.output_box.insert(tk.END, verified_code)

        else:
            self.output_box.insert(tk.END, "Error: Unable to generate SCAD code.\n")

    def exit_app(self):
        self.root.quit()


if __name__ == "__main__":
    root = tk.Tk()
    app = Text2CADApp(root)
    root.mainloop()
