# Ancient Scripts Converter

📜 A Python package for converting text to ancient writing systems

## Installation
```bash
pip install --upgrade  ancientlinesoftheworld
```

## Usage
```python
from   ancient import AncientScripts

converter = AncientScripts()

#  تبدیل  متن به خط باستانی میخی
cuneiform_text = converter.cuneiform("سلام")

# تبدیل متن به خط باستانی مصری 
hieroglyph_text = converter.hieroglyph("خدا")

# تبدیل متن  تاریخی اوستایی

avesta = converter.avestan("hiسلام")
print(avesta)
```

## Supported Scripts
- Cuneiform
- Egyptian Hieroglyphs
- Pahlavi script
- Manichaean script
- Linear B
-avestan

- And more...

