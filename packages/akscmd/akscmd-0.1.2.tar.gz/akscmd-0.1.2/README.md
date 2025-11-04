# akscmd

Natural language → shell command using AI models.  
Works as:
- `akscmd "<create a folder named apple>"` → prints & (optionally) runs `mkdir apple`
- Optional shell hook so typing `<create a folder named apple>` and pressing **Enter** runs the command directly.

## Quick start
```bash
pip install akscmd
export AKSCMD_API_KEY="YOUR_API_KEY"
export AKSCMD_MODEL="YOUR_MODEL_NAME"
akscmd "<create a folder named apple>" --yes
```

## Configuration

You need to set up two environment variables:

1. **AKSCMD_API_KEY**: Your API key for the AI service
2. **AKSCMD_MODEL**: The model name you want to use

Example:
```bash
export AKSCMD_API_KEY="your-api-key-here"
export AKSCMD_MODEL="gpt-4"
```

## Usage

```bash
# Basic usage
akscmd "<create a folder named apple>"

# Auto-execute the command
akscmd "<create a folder named apple>" --yes

# Get help
akscmd --help
```

## Development

Developed by **Amit Kumar Singh**. You can contact him at: aksmlibts@gmail.com

## License

MIT License
