# 🖼️ Wagtail Image From URL

[![PyPI version](https://badge.fury.io/py/wagtail-image-from-url.svg)](https://pypi.org/project/wagtail-image-from-url/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![Django Version](https://img.shields.io/badge/django-4.2%2B-green.svg)](https://www.djangoproject.com/)
[![Wagtail Version](https://img.shields.io/badge/wagtail-5.0%2B-teal.svg)](https://wagtail.org/)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/wagtail-image-from-url)](https://pypi.org/project/wagtail-image-from-url/)

A powerful and user-friendly Wagtail plugin that enables you to import images directly from URLs into your Wagtail image library without the need to manually download them first. Perfect for content editors who need to quickly add images from external sources.

---

## ✨ Features

### 🚀 Core Functionality
- **Bulk URL Import**: Add multiple images simultaneously by providing multiple URLs in a single form submission.
- **Direct Integration**: Seamlessly integrates into the Wagtail admin interface
- **Real-time Feedback**: Inline status indicators show success/failure for each URL
- **Beautiful UI**: Modern, responsive design with smooth animations and transitions
- **Smart Validation**: Client-side and server-side URL validation
- **File size limit**: Each imported image is limited to a maximum size of 10 MB (to avoid excessively large downloads and memory usage).


### 🎨 User Experience
- **Intuitive Interface**: Clean, modern UI that follows Wagtail design patterns
- **Batch Processing**: Submit multiple URLs with a single click
- **Dynamic Field Management**: Add or remove URL fields on the fly
- **Visual Feedback**: Success/error messages with icons
- **Responsive Design**: Works perfectly on desktop and mobile devices
- **No Page Reload**: AJAX-based submission for smooth user experience

---

## 📋 Requirements

- **Python**: 3.10 or higher
- **Django**: 4.2 or higher
- **Wagtail**: 5.0 or higher
- **Additional Dependencies**:
  - `requests` - For HTTP operations
  - `Pillow` - For image validation and processing
- **Max image size**: 10 MB per image (the plugin validates file sizes and will reject images larger than this limit)

---

## 📦 Installation

### Step 1: Install the Package

Install from PyPI:

```bash
pip install wagtail-image-from-url
```

Alternatively, install from GitHub:

```bash
pip install git+https://github.com/awais786/wagtail-image-from-url.git@main
```

### Step 2: Add to Installed Apps

Add `image_url_upload` to your Django `INSTALLED_APPS` in `settings.py`:

```python
INSTALLED_APPS = [
    # ... other apps
    'wagtail.images',
    'wagtail.search',
    'wagtail.admin',
    'wagtail',
    
    'image_url_upload',  # ← Add this line
    
    # ... other apps
]
```

That's it! The package is ready to use. Static files will be automatically discovered by Django's staticfiles system.
---

## 🎯 Usage

### Quick Start

1. **Navigate to Images**: Go to the Wagtail admin and click on "Images" in the sidebar

2. **Click "Add an Image from URL"**: You'll see a new button in the images index page header

   ![Add Image Button](docs/images/add-url.png)

3. **Enter Image URLs**: 
   - Enter one or more image URLs (you can add multiple URLs in the same form to perform a bulk import).
   - Each image must be 10 MB or smaller — larger files will be rejected by the plugin.
   - Click "Add Another URL" to add more fields
   - Remove unwanted fields using the trash icon

4. **Fetch Images**: Click the "Fetch All Images" button to import all images at once

   ![Add Images Form](docs/images/add-form.png)

5. **View Results**: See real-time status updates next to each URL field


## 🧪 Testing

The project includes comprehensive tests. To run them:

```bash
# Install test dependencies separately
pip install pytest pytest-django

# Run tests
pytest
```

---

## 🛠️ Development Setup

```bash
# Clone the repository
git clone https://github.com/awais786/wagtail-image-from-url.git
cd wagtail-image-from-url

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install package in editable mode
pip install -e .

# Install test/development tools (optional)
pip install pytest pytest-django black flake8

# Run tests
pytest
```


---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.


## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/awais786/wagtail-image-from-url/issues)
- **Discussions**: [GitHub Discussions](https://github.com/awais786/wagtail-image-from-url/discussions)
- **Wagtail Slack**: Find us in the [#packages channel](https://wagtail.org/slack/)


## 📊 Changelog

### Version 1.0.1 (Current)
- ✨ Production-ready release
- ✅ Bulk URL import functionality
- ✅ Real-time status feedback
- ✅ Support for JPEG, PNG, GIF, BMP, and WEBP formats
- ✅ 10 MB file size limit
- ✅ Smart filename extraction with fallbacks
- ✅ Content-type validation
- ✅ Timeout protection (10 seconds)
- ✅ Comprehensive error handling

For detailed changelog, see [CHANGELOG.md](CHANGELOG.md)

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

---

<div align="center">

[⭐ Star on GitHub](https://github.com/awais786/wagtail-image-from-url) | [🐛 Report Bug](https://github.com/awais786/wagtail-image-from-url/issues) | [💡 Request Feature](https://github.com/awais786/wagtail-image-from-url/issues)

**Made with ❤️ for the Wagtail community**

</div>


