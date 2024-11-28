from collections import deque
import datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
from tkinter import scrolledtext
import anthropic
from pathlib import Path
import re
import os
from typing import List, Dict, Any
import threading
from collections import deque
from datetime import datetime
import time

class TranslationApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Content Translator")
        self.translated_chunks = []
        self.pending_chunks = []  # Chunks waiting to be translated
        self.current_chunk_index = 0  # Track progress for resume
        self.total_tokens = 0
        self.processed_tokens = 0
        self.debug_messages = deque(maxlen=3)
        self.translation_in_progress = False
        self.paused = False
        self.retry_count = 0
        self.MAX_RETRIES = 3
        self.RETRY_DELAY = 5  # seconds
        
        # Define supported languages
        self.languages = {
            "Arabic": "ar",
            "Chinese (Simplified)": "zh",
            "Dutch": "nl",
            "English": "en",
            "French": "fr",
            "German": "de",
            "Hindi": "hi",
            "Italian": "it",
            "Japanese": "ja",
            "Korean": "ko",
            "Portuguese": "pt",
            "Russian": "ru",
            "Spanish": "es",
            "Swedish": "sv",
            "Turkish": "tr",
            "Vietnamese": "vi"
        }
        
        # Setup GUI elements
        self.setup_gui()
        
        # Initialize state variables
        self.selected_file = None

        self.translation_in_progress = False

    def add_debug_message(self, message: str):
            """Add a message to debug window with timestamp"""
            timestamp = datetime.now().strftime("%H:%M:%S")
            formatted_message = f"[{timestamp}] {message}"
            self.debug_messages.append(formatted_message)
            
            # Update debug window
            self.debug_text.delete(1.0, tk.END)
            for msg in self.debug_messages:
                self.debug_text.insert(tk.END, msg + '\n')
            self.debug_text.see(tk.END)  # Auto-scroll to bottom
        
    def setup_gui(self):
        # Create main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Left side - Controls
        controls_frame = ttk.Frame(main_frame)
        controls_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # [Previous controls remain the same but now in controls_frame]
        # File selection
        file_frame = ttk.Frame(controls_frame, padding="5")
        file_frame.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        ttk.Label(file_frame, text="File:").grid(row=0, column=0, sticky=tk.W)
        self.file_path_var = tk.StringVar()
        ttk.Entry(file_frame, textvariable=self.file_path_var, width=50).grid(row=0, column=1, padx=5)
        ttk.Button(file_frame, text="Browse", command=self.select_file).grid(row=0, column=2)
        
        # Language selection
        lang_frame = ttk.Frame(controls_frame, padding="5")
        lang_frame.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        ttk.Label(lang_frame, text="From:").grid(row=0, column=0, sticky=tk.W)
        self.source_lang_var = tk.StringVar()
        source_lang_combo = ttk.Combobox(lang_frame, textvariable=self.source_lang_var, values=list(self.languages.keys()))
        source_lang_combo.grid(row=0, column=1, padx=5)
        source_lang_combo.set("Auto-detect")
        
        ttk.Label(lang_frame, text="To:").grid(row=0, column=2, sticky=tk.W, padx=(10, 0))
        self.target_lang_var = tk.StringVar()
        target_lang_combo = ttk.Combobox(lang_frame, textvariable=self.target_lang_var, values=list(self.languages.keys()))
        target_lang_combo.grid(row=0, column=3, padx=5)
        target_lang_combo.set("English")
        
        # Token limit
        token_frame = ttk.Frame(controls_frame, padding="5")
        token_frame.grid(row=2, column=0, sticky=(tk.W, tk.E))
        
        ttk.Label(token_frame, text="Chunk Size (tokens):").grid(row=0, column=0, sticky=tk.W)
        self.token_limit_var = tk.StringVar(value="1000")
        ttk.Entry(token_frame, textvariable=self.token_limit_var, width=10).grid(row=0, column=1, padx=5)
        
        # API Key
        api_frame = ttk.Frame(controls_frame, padding="5")
        api_frame.grid(row=3, column=0, sticky=(tk.W, tk.E))
        
        ttk.Label(api_frame, text="Anthropic API Key:").grid(row=0, column=0, sticky=tk.W)
        self.api_key_var = tk.StringVar()
        ttk.Entry(api_frame, textvariable=self.api_key_var, show="*", width=50).grid(row=0, column=1, padx=5)
        
        # Progress
        progress_frame = ttk.Frame(controls_frame, padding="5")
        progress_frame.grid(row=4, column=0, sticky=(tk.W, tk.E))
        
        self.progress_var = tk.StringVar(value="Ready")
        ttk.Label(progress_frame, textvariable=self.progress_var).grid(row=0, column=0, sticky=tk.W)
        
        self.progress = ttk.Progressbar(progress_frame, length=300, mode='determinate')
        self.progress.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5)
        
        # Control buttons
        button_frame = ttk.Frame(controls_frame, padding="5")
        button_frame.grid(row=5, column=0, sticky=(tk.W, tk.E))
        
        self.translate_button = ttk.Button(button_frame, text="Start Translation", command=self.start_translation)
        self.translate_button.grid(row=0, column=0, padx=5)
        
        self.pause_button = ttk.Button(button_frame, text="Pause", command=self.pause_translation, state=tk.DISABLED)
        self.pause_button.grid(row=0, column=1, padx=5)
        
        self.save_button = ttk.Button(button_frame, text="Save Results", command=self.save_results, state=tk.DISABLED)
        self.save_button.grid(row=0, column=2, padx=5)
        
        # Right side - Debug Output
        debug_frame = ttk.LabelFrame(main_frame, text="Debug Output", padding="5")
        debug_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(10, 0))
        
        self.debug_text = scrolledtext.ScrolledText(debug_frame, width=40, height=10, wrap=tk.WORD)
        self.debug_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Add initial debug message
        self.add_debug_message("Application started")
        self.add_debug_message("Using Claude Sonnet 3.5 model")
        self.add_debug_message("Ready for translation")

    def pause_translation(self):
        if self.translation_in_progress:
            self.paused = True
            self.pause_button.configure(text="Resume", command=self.resume_translation)
            self.add_debug_message("Translation paused")
            self.save_progress()  # Auto-save on pause

    def resume_translation(self):
        self.paused = False
        self.pause_button.configure(text="Pause", command=self.pause_translation)
        self.add_debug_message("Translation resumed")
        # Start a new thread for remaining translations
        threading.Thread(target=self.translation_process, daemon=True).start()

    def save_progress(self):
        """Save current translation progress to a temporary file"""
        progress_data = {
            "source_file": self.selected_file,
            "source_language": self.source_lang_var.get(),
            "target_language": self.target_lang_var.get(),
            "translated_chunks": self.translated_chunks,
            "pending_chunks": self.pending_chunks,
            "current_index": self.current_chunk_index
        }
        
        temp_file = f"{self.selected_file}_progress.json"
        try:
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(progress_data, f, ensure_ascii=False, indent=2)
            self.add_debug_message(f"Progress saved to {temp_file}")
        except Exception as e:
            self.add_debug_message(f"Error saving progress: {str(e)}")

    def load_progress(self):
        """Load previous translation progress"""
        temp_file = f"{self.selected_file}_progress.json"
        if os.path.exists(temp_file):
            try:
                with open(temp_file, 'r', encoding='utf-8') as f:
                    progress_data = json.load(f)
                self.translated_chunks = progress_data["translated_chunks"]
                self.pending_chunks = progress_data["pending_chunks"]
                self.current_chunk_index = progress_data["current_index"]
                return True
            except Exception as e:
                self.add_debug_message(f"Error loading progress: {str(e)}")
        return False

    def select_file(self):
        filename = filedialog.askopenfilename(
            filetypes=[
                ("Text files", "*.txt"),
                ("Markdown files", "*.md"),
                ("All files", "*.*")
            ]
        )
        if filename:
            self.selected_file = filename
            self.file_path_var.set(filename)

    def chunk_content(self, content: str, chunk_size: int) -> List[str]:
        """Split content into chunks that respect sentence and paragraph boundaries."""
        chunks = []
        current_chunk = []
        current_size = 0
        
        # Split into paragraphs first
        paragraphs = content.split('\n\n')
        
        for paragraph in paragraphs:
            # Roughly estimate tokens (words + punctuation)
            paragraph_size = len(paragraph.split())
            
            if current_size + paragraph_size <= chunk_size:
                current_chunk.append(paragraph)
                current_size += paragraph_size
            else:
                # If the current chunk has content, save it
                if current_chunk:
                    chunks.append('\n\n'.join(current_chunk))
                    current_chunk = []
                    current_size = 0
                
                # If paragraph is larger than chunk_size, split by sentences
                if paragraph_size > chunk_size:
                    sentences = re.split(r'(?<=[.!?])\s+', paragraph)
                    current_sentence_chunk = []
                    current_sentence_size = 0
                    
                    for sentence in sentences:
                        sentence_size = len(sentence.split())
                        if current_sentence_size + sentence_size <= chunk_size:
                            current_sentence_chunk.append(sentence)
                            current_sentence_size += sentence_size
                        else:
                            if current_sentence_chunk:
                                chunks.append(' '.join(current_sentence_chunk))
                            current_sentence_chunk = [sentence]
                            current_sentence_size = sentence_size
                    
                    if current_sentence_chunk:
                        chunks.append(' '.join(current_sentence_chunk))
                else:
                    current_chunk = [paragraph]
                    current_size = paragraph_size
        
        # Add any remaining content
        if current_chunk:
            chunks.append('\n\n'.join(current_chunk))
        
        return chunks

    def translate_chunk(self, client: anthropic.Client, chunk: str, attempt: int = 1) -> str:
        if self.paused:
            return None
            
        target_lang = self.target_lang_var.get()
        source_lang = self.source_lang_var.get()
        
        self.add_debug_message(f"Translating chunk ({len(chunk.split())} words) to {target_lang} - Attempt {attempt}")
        
        system_prompt = (
            "You are a highly accurate translator. "
            f"Translate the text from {source_lang if source_lang != 'Auto-detect' else 'the source language'} "
            f"to {target_lang}, maintaining all formatting and structure. "
            "Output only the translated text with no additional commentary."
        )
        
        try:
            message = client.messages.create(
                model="claude-3-5-sonnet-latest ",
                max_tokens=1500,
                temperature=0,
                system=system_prompt,
                messages=[
                    {
                        "role": "user",
                        "content": f"Translate the following text: {chunk}"
                    }
                ]
            )
            translated_text = str(message.content)
            
            if translated_text:
                self.add_debug_message(f"Chunk translated successfully: {len(translated_text)} characters")
                self.retry_count = 0  # Reset retry count on success
                return translated_text
            else:
                raise Exception("Empty translation received")
                
        except Exception as e:
            self.add_debug_message(f"Translation error: {str(e)}")
            if attempt <= self.MAX_RETRIES:
                self.add_debug_message(f"Retrying in {self.RETRY_DELAY} seconds...")
                time.sleep(self.RETRY_DELAY)
                return self.translate_chunk(client, chunk, attempt + 1)
            else:
                self.retry_count += 1
                if self.retry_count >= self.MAX_RETRIES:
                    self.paused = True
                    self.add_debug_message("Maximum retries reached. Translation paused.")
                    self.save_progress()
                    self.root.after(0, lambda: messagebox.showwarning(
                        "Translation Paused",
                        "Maximum retries reached. Progress has been saved. Click Resume to continue."
                    ))
                raise

    def start_translation(self):
        if not self.selected_file or not self.api_key_var.get() or not self.target_lang_var.get():
            self.progress_var.set("Please select a file, provide API key, and select target language")
            return
        
        if self.translation_in_progress:
            return
        
        # Check for existing progress before setting any variables
        temp_file = f"{self.selected_file}_progress.json"
        if os.path.exists(temp_file):
            try:
                with open(temp_file, 'r', encoding='utf-8') as f:
                    progress_data = json.load(f)
                
                resume = messagebox.askyesno(
                    "Resume Translation", 
                    f"Previous progress found at chunk {progress_data['current_index']}. Would you like to resume?"
                )
                
                if resume:
                    self.translated_chunks = progress_data["translated_chunks"]
                    self.pending_chunks = progress_data["pending_chunks"]
                    self.current_chunk_index = progress_data["current_index"]
                    self.add_debug_message(f"Resuming from chunk {self.current_chunk_index}")
                else:
                    # If not resuming, clear everything and delete temp file
                    self.translated_chunks = []
                    self.pending_chunks = []
                    self.current_chunk_index = 0
                    os.remove(temp_file)
                    self.add_debug_message("Starting new translation")
            except Exception as e:
                self.add_debug_message(f"Error loading progress file: {str(e)}")
                # If error loading progress, start fresh
                self.translated_chunks = []
                self.pending_chunks = []
                self.current_chunk_index = 0
        else:
            # No progress file found, start fresh
            self.translated_chunks = []
            self.pending_chunks = []
            self.current_chunk_index = 0
            
        self.translation_in_progress = True
        self.paused = False
        self.translate_button.state(['disabled'])
        self.pause_button.state(['!disabled'])
        
        # Start translation in a separate thread
        threading.Thread(target=self.translation_process, daemon=True).start()

    def translation_process(self):
        try:
            # Initialize client first
            client = anthropic.Client(api_key=self.api_key_var.get())
            
            # If we don't have pending chunks (fresh start)
            if not self.pending_chunks:
                self.add_debug_message("Initializing new translation process")
                with open(self.selected_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                chunk_size = int(self.token_limit_var.get()) if self.token_limit_var.get() != "0" else float('inf')
                self.add_debug_message(f"Using chunk size: {chunk_size} tokens")
                
                self.pending_chunks = self.chunk_content(content, chunk_size)
            else:
                self.add_debug_message(f"Resuming translation from chunk {self.current_chunk_index}")
                
            total_chunks = len(self.pending_chunks)
            self.progress['maximum'] = total_chunks
            self.progress['value'] = self.current_chunk_index
            
            # Process remaining chunks
            while self.current_chunk_index < len(self.pending_chunks) and not self.paused:
                chunk = self.pending_chunks[self.current_chunk_index]
                translated_chunk = self.translate_chunk(client, chunk)
                
                if translated_chunk:
                    self.translated_chunks.append(translated_chunk)
                    self.add_debug_message(f"Stored chunk {self.current_chunk_index + 1}: {len(translated_chunk)} characters")
                
                self.current_chunk_index += 1
                self.progress['value'] = self.current_chunk_index
                self.progress_var.set(f"Processing chunk {self.current_chunk_index} of {total_chunks}")
                self.root.update_idletasks()
            
            if not self.paused:
                self.add_debug_message(f"Translation complete. Total chunks stored: {len(self.translated_chunks)}")
                self.progress_var.set("Translation complete!")
                self.save_button.state(['!disabled'])
                self.pause_button.state(['disabled'])
                # Cleanup progress file
                temp_file = f"{self.selected_file}_progress.json"
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            
        except Exception as e:
            self.progress_var.set(f"Error: {str(e)}")
            self.add_debug_message(f"Process error: {str(e)}")
            # Save progress on error
            self.save_progress()
        finally:
            if not self.paused:
                self.translation_in_progress = False
                self.translate_button.state(['!disabled'])

    def save_results(self):
        if not self.translated_chunks:
            return
            
        output_file = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")]
        )
        
        if output_file:
            # Create a result dictionary with proper structure
            result = {
                "source_file": self.selected_file,
                "source_language": self.source_lang_var.get(),
                "target_language": self.target_lang_var.get(),
                "translated_content": self.translated_chunks  # This should be a list of strings
            }
            
            # Add debug message to track content
            self.add_debug_message(f"Saving {len(self.translated_chunks)} chunks")
            
            try:
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
                
                # Verify the save
                with open(output_file, 'r', encoding='utf-8') as f:
                    saved_content = json.load(f)
                    if saved_content["translated_content"]:
                        self.add_debug_message(f"Successfully saved {len(saved_content['translated_content'])} chunks")
                    else:
                        self.add_debug_message("Warning: Saved file has empty translations")
                        
                self.progress_var.set("Results saved successfully!")
                
            except Exception as e:
                self.add_debug_message(f"Error saving file: {str(e)}")
                self.progress_var.set(f"Error saving: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = TranslationApp(root)
    root.mainloop()