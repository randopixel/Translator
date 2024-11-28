# Content Translator

A Python-based GUI application for translating large text files using Claude AI, with support for chunking, progress tracking, and error recovery.

## Features

- Translate large text files while preserving formatting
- Support for multiple languages
- Intelligent text chunking to handle large files
- Progress tracking and save/resume capability
- Error recovery and retry mechanism
- Debug output window
- Clean, modern GUI interface

## Requirements

- Python 3.11+
- Anthropic API key
- Required Python packages:
  ```
  anthropic
  tkinter (comes with Python)
  ```

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/content-translator.git
   cd content-translator
   ```

2. Install required packages:
   ```bash
   pip install anthropic
   ```

3. Run the application:
   ```bash
   python contranapp.py
   ```

## Usage

1. Launch the application
2. Select your input file (supports .txt, .md, and other text files)
3. Choose source and target languages
4. Enter your Anthropic API key
5. Set chunk size (default: 1000 tokens)
6. Click "Start Translation"

### Controls

- **Start Translation**: Begins the translation process
- **Pause**: Temporarily stops translation and saves progress
- **Resume**: Continues translation from last saved point
- **Save Results**: Exports completed translation to JSON file

### Progress Recovery

The application automatically saves progress during:
- Manual pausing
- Error conditions
- Application closure

To resume a previous translation:
1. Select the same input file
2. The application will detect the progress file and offer to resume
3. Choose yes to continue from the last saved point

## Features in Detail

### Language Support

Currently supports translation between:
- Arabic
- Chinese (Simplified)
- Dutch
- English
- French
- German
- Hindi
- Italian
- Japanese
- Korean
- Portuguese
- Russian
- Spanish
- Swedish
- Turkish
- Vietnamese

### Error Handling

- Automatic retry on failed translations (up to 3 attempts)
- 5-second delay between retries
- Progress auto-save on errors
- Detailed error logging in debug window

### Debug Output

The debug window shows:
- Translation progress
- Chunk information
- Error messages
- Connection status
- API responses

## Output Format

The application saves translations in JSON format:
```json
{
  "source_file": "path/to/input.txt",
  "source_language": "English",
  "target_language": "Spanish",
  "translated_content": [
    "Translated chunk 1...",
    "Translated chunk 2...",
    "..."
  ]
}
```

## Known Limitations

- Maximum recommended file size depends on available memory
- Translation quality depends on Claude AI capabilities
- Internet connection required
- API rate limits may affect translation speed

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

Distributed under the MIT License. See `LICENSE` for more information.

## Acknowledgments

- Built using the Anthropic Claude AI API
- Uses Python's tkinter for GUI
- Inspired by the need for reliable large-scale translation tools

## Support

For support, please open an issue in the GitHub repository or contact the maintainers.
