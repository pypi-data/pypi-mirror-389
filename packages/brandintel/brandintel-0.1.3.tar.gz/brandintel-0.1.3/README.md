
# brandintel

**BrandIntel** helps you identify competitor brands and get brand summaries using Google Gemini AI.

## Installation
```bash
pip install brandintel
```

## Usage
```bash
import brandintel

summary = brandintel.get_brand_summary("Dove")
competitors = brandintel.get_competitors_for_brand("Dove")

print("Summary:", summary)
print("Competitors:", competitors)
```

### CLI Mode
```bash
python -m brandintel.core --brand "Dove"
```

---

Developed by Vivek Gupta.
