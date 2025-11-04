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

print(cuneiform_text)

# تبدیل متن به خط باستانی مصری 
hieroglyph_text = converter.hieroglyph("خدا")

print(hieroglyph_text)

# تبدیل متن  تاریخی اوستایی

avesta = converter.avestan("hiسلام")
print(avesta)

print(c.get_supported_scripts())
```

## Supported Scripts
- Cuneiform
- Egyptian Hieroglyphs
- Pahlavi script
- Manichaean script
- Linear B
-avestan

- And more...

