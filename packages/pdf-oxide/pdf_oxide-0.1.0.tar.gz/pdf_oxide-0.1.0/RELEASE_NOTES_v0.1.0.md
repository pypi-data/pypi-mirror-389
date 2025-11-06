# pdf_oxide v0.1.0 - Initial Release

**Release Date**: November 5, 2025

We're excited to announce the first public release of **pdf_oxide** - a fast, robust PDF parsing and conversion library written in Rust with Python bindings!

## 🎉 Highlights

- **Fast & Safe**: Written in Rust for memory safety and performance
- **Full-Featured**: Comprehensive PDF parsing with encryption support
- **Well-Tested**: 522 passing tests with extensive PDF coverage
- **Python Support**: Easy-to-use Python bindings via PyO3
- **Zero Warnings**: Clean codebase with full documentation

## ✨ Features

### PDF Parsing
- ✅ PDF versions 1.0 through 1.7 support
- ✅ Full encryption support (RC4-40, RC4-128, AES-128, AES-256)
- ✅ Cross-reference table and stream parsing
- ✅ Object stream (ObjStm) support
- ✅ Robust error handling with detailed error messages

### Text Extraction
- ✅ Unicode text extraction with proper encoding handling
- ✅ Font dictionary parsing (Type 1, TrueType, CID fonts)
- ✅ ToUnicode CMap support
- ✅ Adobe Glyph List fallback
- ✅ Character positioning and bounding boxes

### Layout Analysis
- ✅ Column detection with XY-Cut algorithm
- ✅ Reading order determination
- ✅ Heading detection
- ✅ Table detection
- ✅ DBSCAN clustering for text grouping

### Conversion
- ✅ **HTML Export**: Semantic HTML with proper structure
- ✅ **Markdown Export**: Clean markdown with headings and lists
- ✅ **Plain Text Export**: Simple text extraction
- ✅ Configurable conversion options

### Structure Tree
- ✅ PDF structure tree parsing (tagged PDFs)
- ✅ Accessibility support
- ✅ Semantic element recognition

### Python Bindings
- ✅ Easy-to-use Python API
- ✅ Full feature parity with Rust library
- ✅ Type hints and documentation
- ✅ Python 3.8+ support

## 📦 Installation

### Rust

```bash
cargo add pdf_oxide
```

Or add to your `Cargo.toml`:

```toml
[dependencies]
pdf_oxide = "0.1.0"
```

### Python

```bash
pip install pdf_oxide
```

## 🚀 Quick Start

### Rust

```rust
use pdf_oxide::PdfDocument;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    // Open a PDF
    let mut doc = PdfDocument::open("document.pdf")?;

    // Extract text
    let text = doc.extract_text_simple()?;
    println!("{}", text);

    // Convert to HTML
    let html = doc.to_html_all(&Default::default())?;

    // Convert to Markdown
    let markdown = doc.to_markdown_all(&Default::default())?;

    Ok(())
}
```

### Python

```python
from pdf_oxide import PdfDocument

# Open a PDF
doc = PdfDocument.open("document.pdf")

# Extract text
text = doc.extract_text_simple()
print(text)

# Convert to HTML
html = doc.to_html_all()

# Convert to Markdown
markdown = doc.to_markdown_all()
```

## 📊 Performance

- **Fast parsing**: Optimized Rust implementation
- **Memory efficient**: Lazy loading and streaming where possible
- **Scalable**: Handles large PDFs with thousands of pages

## 🔒 Security

- No unsafe code in parser (security-critical paths)
- Comprehensive input validation
- Protection against decompression bombs
- Resource limits to prevent DoS attacks

## 📚 Documentation

- **API Documentation**: https://docs.rs/pdf_oxide
- **User Guide**: See `docs/guides/QUICK_START.md`
- **Examples**: Over 40 examples in `examples/` directory
- **Architecture**: See `docs/ARCHITECTURE.md`

## 🧪 Testing

- 522 passing tests
- Extensive regression test suite
- Real-world PDF coverage
- Continuous integration with GitHub Actions

## 🛠️ Code Quality

- **Zero compiler warnings**: Clean build
- **Configured linters**: rustfmt, clippy, ruff
- **Full documentation**: All public APIs documented
- **Type safety**: No unwrap() panics in production code

## 📝 License

Dual-licensed under MIT OR Apache-2.0 - use whichever you prefer!

## 🤝 Contributing

We welcome contributions! Please see:
- [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines
- [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) for community standards
- [DEVELOPMENT_GUIDE.md](docs/DEVELOPMENT_GUIDE.md) for technical details

## 🐛 Known Issues

- Column detection may need fine-tuning for some complex layouts
- Some rare PDF features not yet supported (see issue tracker)

## 🔮 Roadmap

Future releases will include:
- Additional export formats (XML, JSON)
- Image extraction improvements
- Form field support
- Digital signature verification
- ML-enhanced layout analysis
- WASM support for browser usage

## 📢 Community

- **GitHub**: https://github.com/yfedoseev/pdf_oxide
- **Issues**: https://github.com/yfedoseev/pdf_oxide/issues
- **Discussions**: https://github.com/yfedoseev/pdf_oxide/discussions

## 🙏 Acknowledgments

Thanks to the Rust community and all the amazing PDF libraries that inspired this project!

---

**Full Changelog**: https://github.com/yfedoseev/pdf_oxide/commits/v0.1.0
