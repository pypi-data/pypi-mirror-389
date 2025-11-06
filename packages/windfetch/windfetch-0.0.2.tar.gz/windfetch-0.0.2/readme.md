# WindFetch 🌀

[中文](https://github.com/starwindv/windfetch/blob/main/readme_cn.md)

An elegant Python system information tool, inspired by `neofetch`.

## ✨ Features

### 🎯 Core Features
- **System Information Display** - Comprehensive hardware and software system information.
- **Automatic Logo Matching** - Automatically displays the corresponding ASCII Logo based on the system name and aligns the output format.
- **Colorful Output** - Beautiful terminal color support.
- **Smart Detection** - Automatically detects desktop environment, theme, icons, etc.
- **Highly Customizable** - Supports custom logos and configurations.

### 🎨 Logo System

#### Default Logo Examples
The project has built-in links providing ASCII Logos for several common systems:
- **Red Hat** - Classic Red Hat Logo
- **Ubuntu** - Iconic Ubuntu Logo
- **Windows** - Colorful Windows Logo (Logo support only, system detection not yet supported)
- **Debian** - Debian Swirl Logo
- **CentOS** - CentOS Geometric Logo
- **Arch Linux** - Iconic Arch Logo
- **Android** - Android Robot Logo

#### Custom Logos
You can create custom logos for any system:

**Method 1: JSON Format (Recommended)**
```json
{
    "mysystem": "Your ASCII Art Text",
    "ubuntu": "\u001b[38;5;123mCustom Ubuntu Logo\u001b[0m"
}
```

**Method 2: Python Format (Requires enabling unsafe loading)**
```python
logo = {
    "mysystem": "Colorful ASCII Art"
}
```

### ⚙️ Configuration Management
- Online Logo download and update
- Custom Logo support
- Safe loading control
- Flexible configuration management

## 🚀 Quick Start

### Installation

```bash
pip install windfetch
```

### Basic Usage

```bash
windfetch
```

## 📋 Displayed Information

WindFetch displays the following system information:

| Category          | Information Content            |
|-------------------|--------------------------------|
| **User Info**     | Username@Hostname              |
| **System Info**   | OS, Kernel Version, Uptime     |
| **Software Info** | Package Count, Shell, Terminal |
| **Desktop Env.**  | DE, Theme, Icon Theme          |
| **Hardware Info** | CPU, GPU, Memory Usage, etc.   |

## ⚠️ Platform Support Note

**Currently only supports Linux systems**
- ✅ Full support for common Linux distributions
- ❌ Windows system detection not yet adapted
- ❌ macOS system detection not yet adapted

On unsupported platforms, some system information may display as "Unknown".

## ⚙️ Configuration

### Configuration File Location
`~/.windfetch/config.json`

### Default Configuration

```json
{
    "logo_path": "~/.windfetch/logo.py",
    "custom_logo_path": null,
    "logo_url": "https://windfetch.starwindv.top/api/logo",
    "download_default_logo": true,
    "overwrite_default_logo": true,
    "load_customLogo_unsafe": false,
    "need_update_logo": false
}
```

### Configuration Explanation

- **`logo_path`** - Default Logo file path (not recommended to modify manually)
- **`custom_logo_path`** - Custom Logo file path
- **`logo_url`** - Logo data source URL
- **`download_default_logo`** - Whether to automatically download the default Logo
- **`load_customLogo_unsafe`** - Whether to allow loading custom Logos in Python format

## 🔧 Custom Logo Guide

### Security Recommendations
1. **Prefer JSON format** - Safer, no code execution needed.
2. **Use Python format with caution** - Only use from trusted sources.
3. **Do not modify the default logo.py** - The tool updates it automatically; manual modifications may be overwritten.

### Creating a Custom Logo

1. **Create a Logo file in JSON or .py format**

2. **Update the configuration file**
```json
{
    "custom_logo_path": "/path/to/your/logo.json",
    "load_customLogo_unsafe": true
}
```
Note: Regardless of whether a .py format custom logo is used, `load_customLogo_unsafe` must be `true` to load it correctly.

## 🛠️ Development

### Project Structure
```
.
├── ExampleLogos/
│   ├── logo.json
│   └── logo.py
├── pyproject.toml
└── src/
    └── windfetch/
        ├── __init__.py
        ├── loader.py
        └── windfetch.py
```

### Dependencies
- `requests` - HTTP request handling
- `stv_utils>=0.0.8` - Utility functions and color output
- `psutil` - System information retrieval

## Security Reminder
- When enabling `load_customLogo_unsafe`, ensure the custom Logo file comes from a trusted source.
- Periodically check if the default Logo file has been modified unexpectedly.

## 📄 License

This project is licensed under the [MIT License](https://github.com/starwindv/windfetch).

## 🤝 Contributing

Issues and Pull Requests are welcome!

## 📞 Contact

- Author: StarWindv
- Email: starwindv.stv@gmail.com
- Project Homepage: https://github.com/StarWindv/windfetch