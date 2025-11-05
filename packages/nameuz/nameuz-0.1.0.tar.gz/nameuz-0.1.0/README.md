# nameuz

![PyPI Version](https://img.shields.io/pypi/v/nameuz)
![Python Version](https://img.shields.io/pypi/pyversions/nameuz)
![License](https://img.shields.io/badge/license-MIT-green)

**nameuz** — bu CLI va Python kutubxona bo‘lib, o‘zbek ismlarining ma’nosini [ismlar.com](https://ismlar.com) saytidan topishga yordam beradi.
Kutubxona Python loyihalarda ham, terminal buyruqlari orqali ham ishlaydi.

---

## O‘rnatish

```bash
pip install nameuz
```

---

## CLI ishlatish

Terminalda quyidagicha ishlatish mumkin:

```bash
# Ism ma'nosini qidirish
nameuz --search Ali

# Agar keyingi sahifa natijalarini olish kerak bo‘lsa
nameuz --search Ali --page 2
```

Natija shunday ko‘rinishda chiqadi:

```json
[
    {
        "name": "Ali",
        "meaning": "Eng yuksak, eng ulug‘, oliy, yuqori martabali. Bu nom Muhammad payg‘ambarning kuyovi, to‘rtinchi xalifaning ismidir."
    }
]
```

---

## Python kodida ishlatish

Python skriptida quyidagicha ishlatish mumkin:

```python
from nameuz.meaning import Meaning

# Ma'lum ismning ma'nosini olish
m = Meaning("Ali")
result = m.response()

if result:
    for item in result:
        print(f"{item['name']}: {item['meaning']}")
else:
    print("Natija topilmadi.")
```

Natija:

```
Ali: Eng yuksak, eng ulug‘, oliy, yuqori martabali. Bu nom Muhammad payg‘ambarning kuyovi, to‘rtinchi xalifaning ismidir.
```

---

### JSON sifatida formatlash

Agar natijani chiroyli formatlangan JSON ko‘rinishida olish kerak bo‘lsa:

```python
import json
from nameuz.meaning import Meaning

m = Meaning("Ali")
result = m.response()

if result:
    print(json.dumps(result, indent=4, ensure_ascii=False))
```

Natija:

```json
[
    {
        "name": "Ali",
        "meaning": "Eng yuksak, eng ulug‘, oliy, yuqori martabali. Bu nom Muhammad payg‘ambarning kuyovi, to‘rtinchi xalifaning ismidir."
    }
]
```