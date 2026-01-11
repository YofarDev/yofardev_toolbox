# Yofardev Toolbox

A modern, desktop automation application for batch file processing. Built with Python and CustomTkinter, it provides a sleek dark-themed interface with **AI-powered script generation** - simply describe what you want to automate, and the app writes the script for you.

![Python Version](https://img.shields.io/badge/python-3.13%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

## Features

### 🤖 AI-Powered Script Generation (Core Feature)
- **Natural Language to Code**: Simply describe what you want to automate in plain English
- **Instant Scripts**: The AI writes complete, ready-to-use Python scripts in seconds
- **OpenAI-Compatible**: Works with any LLM provider (OpenAI, Anthropic, local models via Ollama, etc.)
- **No Coding Required**: Perfect for users who want automation without writing code

### 📁 Batch File Processing
- **Process Multiple Files**: Select individual files or entire folders at once
- **Automatic Output Management**: Results saved to timestamped directories
- **Auto-Open Results**: Output folder opens automatically when processing completes
- **Real-Time Progress**: Watch your scripts run with live console output

### 🎨 Built-in Script Library
14+ pre-built scripts for common automation tasks:
- **Image Processing**: Background removal, format conversion, resizing, filters
- **Video Tools**: Extract frames, create GIFs, convert formats
- **Enhancement**: AI-powered upscaling, color correction, artistic effects
- **Utility**: Batch renaming, watermarking, metadata editing

### 💻 Modern Interface
- **Dark Theme**: Easy on the eyes during long work sessions
- **Search & Filter**: Quickly find scripts by name or description
- **Parameter UI**: Easy configuration without touching code
- **Progress Tracking**: Real-time feedback on script execution

## Screenshots

![Yofardev Toolbox Screenshot](screen.png)

The application features a two-panel layout:
- **Left Panel**: Script browser with AI generator button
- **Right Panel**: Configuration area, file selection, and live console output

## Installation

### Prerequisites

- Python 3.13 or higher
- macOS, Linux, or Windows

### Quick Start with uv

```bash
# Clone the repository
git clone https://github.com/yourusername/yofardev_toolbox.git
cd yofardev_toolbox

# Install dependencies using uv
uv sync

# Run the application
uv run python main.py
```

### Alternative: Using pip

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

## Usage

### 🚀 Creating Custom Scripts with AI (Recommended)

The easiest way to automate tasks is to let the AI write the script for you:

1. Click the **"🤖 Generate Script"** button in the sidebar
2. Click the **⚙️ settings button** to configure your LLM API (one-time setup)
3. Enter your API details (endpoint, model, API key)
4. Describe what you want to automate:
   - ✅ "Resize all images to 1920x1080 and add a watermark"
   - ✅ "Convert all PDFs to text files and extract emails"
   - ✅ "Rename files by their creation date"
   - ✅ "Apply a sepia filter and add timestamp to photos"
5. Click **"Generate Script"** - the AI writes the code instantly
6. Your new script appears in the sidebar and is ready to use!

**No programming knowledge required** - just describe what you want in plain English.

### Running Scripts

1. Select a script from the left sidebar
2. Configure parameters in the Configuration panel
3. Add input files using the "Add Files" or "Add Folder" buttons
4. Click "RUN SCRIPT" to execute
5. Output files are automatically saved to `~/Downloads/<script_name>/`
6. The output folder opens automatically when the script completes

### Search Scripts

Use the search box at the top of the sidebar to filter scripts by name or description.

**💡 Pro Tip**: Can't find a script for your task? Click "🤖 Generate Script" and let the AI create one for you!

## Configuration

### LLM Settings

The application stores LLM configurations in `~/.yofardev_toolbox/llm_config.json`. You can:

- Add multiple LLM configurations
- Switch between different providers
- Edit or delete configurations

### Application Settings

The application uses sensible defaults, but you can customize:
- Window size (`config/app_config.py`)
- Color themes (`config/themes.py`)
- Script directory location

## Architecture

The application follows a clean three-layer architecture:

```
yofardev_toolbox/
├── config/              # Configuration layer
│   ├── app_config.py    # App settings
│   ├── themes.py        # Color schemes and styling
│   └── llm_config.py    # LLM configuration management
│
├── core/                # Business logic layer
│   ├── script_manager.py    # Script discovery and loading
│   ├── script_executor.py   # Process management
│   ├── file_handler.py      # File operations
│   └── llm_generator.py     # LLM integration
│
├── ui/                  # Presentation layer
│   ├── app.py               # Main application window
│   ├── components/          # Reusable UI components
│   │   ├── sidebar.py
│   │   ├── console.py
│   │   └── generator_panel.py
│   └── dialogs/             # Modal dialogs
│       ├── settings_dialog.py
│       └── examples_dialog.py
│
└── scripts/             # User scripts
    ├── remove_bg.py
    ├── webcamify.py
    └── ...
```

## Writing Custom Scripts

You can easily add your own scripts to the `scripts/` directory. Each script must expose the following:

### Required Module Variables

```python
NAME = "My Script Name"
DESCRIPTION = "What this script does"
INPUT_TYPES = "Images (*.png *.jpg *.jpeg)"
PARAMETERS = [
    {
        "name": "param_name",
        "type": "str",  # str, int, float, bool, choice
        "default": "default_value",
        "description": "Parameter description",
        "choices": ["option1", "option2"]  # Required for type="choice"
    }
]
ACCEPTS_MULTIPLE_FILES = True  # Optional, defaults to True
```

### Required Functions

```python
def main(files, output_dir, **kwargs):
    """
    Main entry point for the script.

    Args:
        files: List of file paths
        output_dir: Directory to save outputs
        **kwargs: Parameter values from UI
    """
    # Your processing logic here
    pass

def process_files(file_paths, output_dir, **kwargs):
    """
    Process multiple files.
    Called by the executor for batch processing.
    """
    for file_path in file_paths:
        main([file_path], output_dir, **kwargs)
```

### Example Script

```python
import os
from PIL import Image

NAME = "Batch Image Resizer"
DESCRIPTION = "Resize images to a specified dimension"
INPUT_TYPES = "Images (*.png *.jpg *.jpeg)"
PARAMETERS = [
    {
        "name": "size",
        "type": "int",
        "default": 800,
        "description": "Target width/height in pixels"
    },
    {
        "name": "maintain_aspect",
        "type": "bool",
        "default": True,
        "description": "Maintain aspect ratio"
    }
]

def main(files, output_dir, size, maintain_aspect, **kwargs):
    """Process a list of image files."""
    for file_path in files:
        img = Image.open(file_path)
        if maintain_aspect:
            img.thumbnail((size, size))
        else:
            img = img.resize((size, size))

        output_path = os.path.join(output_dir, f"resized_{os.path.basename(file_path)}")
        img.save(output_path)
        print(f"✅ Resized: {os.path.basename(file_path)}")

def process_files(file_paths, output_dir, **kwargs):
    """Entry point for batch processing."""
    main(file_paths, output_dir, **kwargs)
```

**💡 Tip**: You can also use the AI generator to create this type of script automatically - just describe what you want!

See `SCRIPT_DOCUMENTATION.md` for detailed guidelines.

## Available Scripts

The app includes 14+ built-in scripts for common tasks. Remember, you can always create custom scripts with AI!

| Script | Description | File Types |
|--------|-------------|------------|
| **Background Remover** | AI-powered background removal | Images |
| **Animated WebP Creator** | Create animated WebP images | Images |
| **Anime Enhancer** | Enhance anime-style images | Images |
| **Comparison GIF** | Create before/after comparison GIFs | Images |
| **Downscale by Half** | Reduce image size by 50% | Images |
| **Downscale to Size** | Resize to specific dimensions | Images |
| **GIF to WebP** | Convert GIF to WebP format | GIF |
| **Images to GIF** | Combine images into GIF | Images |
| **JPEG Artifact Reducer** | Reduce compression artifacts | Images |
| **Manga Style Converter** | Apply manga-style effects | Images |
| **Rounded Corners** | Add rounded corners to images | Images |
| **Vibrance Saturation** | Enhance colors | Images |
| **Video to Images** | Extract frames from video | Video |
| **Webcamify** | Apply webcam-style filters | Images |

**💡 Need something different?** Use the AI generator to create custom scripts for any file type or automation task!

## Troubleshooting

### Application won't start

- Ensure Python 3.13+ is installed: `python --version`
- Reinstall dependencies: `uv sync`
- Check that tkinter is available: `python -c "import tkinter"`

### Scripts not appearing in sidebar

- Ensure scripts are in the `scripts/` directory
- Check that script files end with `.py`
- Verify scripts have required `NAME`, `DESCRIPTION`, `PARAMETERS` variables
- Check console output for loading errors

### LLM generation not working

- Verify API key is configured in Settings (⚙️)
- Check that the API endpoint is accessible
- Ensure the model name is correct for your provider
- Check console for error messages

## Development

### Project Structure

The codebase follows a modular architecture with separated concerns:

- **Config Layer**: Settings, themes, and LLM configuration
- **Core Layer**: Business logic for script management and execution
- **UI Layer**: Presentation components and dialogs

### Adding Features

1. **New UI Component**: Add to `ui/components/`
2. **New Dialog**: Add to `ui/dialogs/`
3. **New Core Functionality**: Add to `core/`
4. **New Script**: Add to `scripts/` directory

### Testing

Run scripts directly from command line:
```bash
python scripts/remove_bg.py image.jpg --alpha_matting True
```

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

MIT License - feel free to use this project for personal or commercial purposes.

## Acknowledgments

- **CustomTkinter** for the modern UI framework
- **Pillow** for image processing
- **rembg** for AI background removal
- All open-source contributors

## Contact

For issues, questions, or suggestions, please open an issue on GitHub.

---

**Version**: 1.2.0
**Last Updated**: 2025
