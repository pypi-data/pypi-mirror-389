# 📦 Guida: Pubblicare Shellog su PyPI

Questa guida ti aiuta a pubblicare shellog su PyPI così che tutti possano installarlo con `pip install shellog`.

---

## ✅ Pre-requisiti

Prima di pubblicare, verifica:

- [ ] Server backend è online e funzionante
- [ ] Bot Telegram risponde a `/id`
- [ ] Hai testato la libreria e funziona
- [ ] Hai deciso come comunicare l'URL del server agli utenti
- [ ] README.md è aggiornato con istruzioni chiare

---

## 📋 Step 1: Crea Account PyPI

### 1.1 Registrati su PyPI

Vai su: https://pypi.org/account/register/

- Crea un account
- Verifica l'email
- **Abilita 2FA (Obbligatorio!)**: https://pypi.org/manage/account/

### 1.2 Crea API Token

1. Vai su: https://pypi.org/manage/account/token/
2. Clicca "Add API token"
3. Nome: `shellog-upload`
4. Scope: `Entire account` (prima pubblicazione) o `Project: shellog` (aggiornamenti)
5. **Copia il token** (inizia con `pypi-...`)
6. **Salvalo in un posto sicuro!** (non lo vedrai più)

---

## 🔧 Step 2: Installa gli Strumenti

```bash
cd /Users/danielemargiotta/Downloads/shellog-main

# Installa build tools
pip install --upgrade build twine
```

---

## 🏗️ Step 3: Build del Pacchetto

```bash
# Pulisci build precedenti (se esistono)
rm -rf build/ dist/ *.egg-info

# Build
python -m build
```

Dovresti vedere:
```
Successfully built shellog-1.0.5.tar.gz and shellog-1.0.5-py3-none-any.whl
```

I file saranno in `dist/`:
```
dist/
├── shellog-1.0.5-py3-none-any.whl
└── shellog-1.0.5.tar.gz
```

---

## 🧪 Step 4: Test su TestPyPI (Opzionale ma Raccomandato)

Prima di pubblicare su PyPI ufficiale, testa su TestPyPI:

### 4.1 Registrati su TestPyPI

https://test.pypi.org/account/register/

### 4.2 Upload su TestPyPI

```bash
twine upload --repository testpypi dist/*
```

Ti chiederà:
- Username: `__token__`
- Password: (incolla il token di TestPyPI che inizia con `pypi-...`)

### 4.3 Testa l'Installazione

```bash
# Crea un ambiente pulito
python -m venv test_env
source test_env/bin/activate  # Su Windows: test_env\Scripts\activate

# Installa da TestPyPI
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ shellog

# Testa
python -c "import shellog; print('Success!')"

# Pulisci
deactivate
rm -rf test_env
```

---

## 🚀 Step 5: Pubblica su PyPI Ufficiale

### 5.1 Upload

```bash
twine upload dist/*
```

Ti chiederà:
- **Username:** `__token__`
- **Password:** (incolla il tuo API token che inizia con `pypi-...`)

**IMPORTANTE:** Usa `__token__` come username, NON il tuo username PyPI!

### 5.2 Verifica

1. Vai su: https://pypi.org/project/shellog/
2. Dovresti vedere la tua libreria pubblicata! 🎉

---

## ✅ Step 6: Testa l'Installazione

```bash
# In un nuovo terminale
pip install shellog

# Verifica
python -c "import shellog; print(shellog.__version__)"
# Output: 1.0.5
```

---

## 📝 Step 7: Testa che Funzioni End-to-End

```python
import shellog

# IMPORTANTE: Sostituisci con il TUO URL del server
bot = shellog.Bot(server_url="https://IL_TUO_SERVER.com")

# Aggiungi il tuo ChatId
bot.addChatId("180612499")

# Invia un messaggio di test
bot.sendMessage("🎉 Shellog v1.0.5 è live su PyPI!")
```

Se ricevi il messaggio su Telegram, **tutto funziona!** 🎊

---

## 🔄 Aggiornare una Versione Esistente

Quando vuoi pubblicare un aggiornamento:

### 1. Aggiorna la Versione

**In `setup.py`:**
```python
version='1.0.5',  # Incrementa la versione
```

**In `shellog/__init__.py`:**
```python
__version__ = "1.0.5"
```

### 2. Documenta i Cambiamenti

Crea/aggiorna `CHANGELOG.md`:
```markdown
# Changelog

## [1.0.5] - 2025-11-04
### Fixed
- Risolto problema rate limiting Telegram

## [1.0.5] - 2025-11-04
### Added
- Nuova architettura con backend server
### Changed
- Token rimosso dalla libreria
```

### 3. Build e Upload

```bash
# Pulisci
rm -rf build/ dist/ *.egg-info

# Build
python -m build

# Upload
twine upload dist/*
```

Gli utenti potranno aggiornare con:
```bash
pip install --upgrade shellog
```

---

## 🔐 Sicurezza del Token PyPI

### Metodo 1: File `.pypirc` (Più Comodo)

```bash
nano ~/.pypirc
```

```ini
[pypi]
username = __token__
password = pypi-TUO_TOKEN_QUI

[testpypi]
username = __token__
password = pypi-TUO_TOKEN_TESTPYPI_QUI
```

```bash
chmod 600 ~/.pypirc
```

Poi puoi fare upload senza inserire credenziali:
```bash
twine upload dist/*
```

### Metodo 2: Variabile d'Ambiente

```bash
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-TUO_TOKEN_QUI

twine upload dist/*
```

---

## 🆘 Troubleshooting

### Error: "File already exists"

Hai già pubblicato questa versione. **Non puoi sovrascrivere!**

Soluzione:
1. Incrementa la versione in `setup.py` e `__init__.py`
2. Rebuilda: `python -m build`
3. Riprova l'upload

---

### Error: "Invalid or non-existent authentication information"

Soluzione:
- Verifica che Username sia `__token__` (con doppio underscore!)
- Verifica che il token inizi con `pypi-`
- Rigenera il token su PyPI se necessario

---

### Error: "403 Forbidden"

Cause possibili:
- Account non verificato (controlla email)
- 2FA non abilitato
- Token scaduto o revocato

Soluzione: Vai su PyPI e verifica il tuo account

---

### Warning: "long_description has syntax errors"

Il README.md ha errori di markdown.

Verifica con:
```bash
twine check dist/*
```

---

### Il pacchetto non include README/LICENSE

Assicurati di avere `MANIFEST.in` con:
```
include README.md
include LICENSE
```

---

## 📊 Statistiche e Monitoring

Dopo la pubblicazione, puoi vedere:

### PyPI Dashboard
https://pypi.org/manage/project/shellog/

Mostra:
- Download totali
- Versioni pubblicate
- Statistiche per versione

### PyPI Stats (Esterno)
https://pypistats.org/packages/shellog

Mostra grafici dettagliati dei download.

---

## 🎯 Checklist Finale

Prima di pubblicare, verifica:

- [ ] `setup.py` ha versione corretta
- [ ] `__init__.py` ha versione corretta
- [ ] README.md è completo e aggiornato
- [ ] LICENSE esiste
- [ ] `python -m build` funziona senza errori
- [ ] `twine check dist/*` passa senza warning
- [ ] Hai testato su TestPyPI
- [ ] Server backend è online e accessibile
- [ ] Bot Telegram funziona
- [ ] Hai comunicato l'URL del server (README, email, docs)

---

## 🎉 Post-Pubblicazione

### Comunica agli Utenti

**1. GitHub Release**

Se hai un repo GitHub:
1. Vai su: https://github.com/danmargs/shellog/releases
2. Crea un nuovo release
3. Tag: `v1.0.5`
4. Descrivi i cambiamenti

**2. Social Media / Email**

```
🎉 Shellog v1.0.5 è ora disponibile su PyPI!

Installa con: pip install shellog

Novità:
- ✅ Nuova architettura sicura (token non esposto)
- ✅ Backend server con rate limiting
- ✅ Supporto multi-piattaforma

Docs: https://github.com/danmargs/shellog
PyPI: https://pypi.org/project/shellog/
```

**3. README Badge**

Aggiungi al README.md:
```markdown
[![PyPI version](https://badge.fury.io/py/shellog.svg)](https://badge.fury.io/py/shellog)
[![Downloads](https://pepy.tech/badge/shellog)](https://pepy.tech/project/shellog)
```

---

## 📚 Risorse Utili

- [PyPI Help](https://pypi.org/help/)
- [Python Packaging Guide](https://packaging.python.org/)
- [Twine Documentation](https://twine.readthedocs.io/)
- [Semantic Versioning](https://semver.org/)

---

## 💡 Best Practices

### Versioning (Semantic Versioning)

```
MAJOR.MINOR.PATCH

1.0.5
│ │ │
│ │ └─ Patch: Bug fixes (backward compatible)
│ └─── Minor: New features (backward compatible)
└───── Major: Breaking changes

Esempi:
1.0.5 → 1.0.5  (bug fix)
1.0.5 → 1.1.0  (nuova feature)
1.1.0 → 2.0.0  (breaking change)
```

### Testing

Prima di ogni pubblicazione:
```bash
# Test automatici (se li hai)
pytest

# Test manuale
python example.py

# Verifica import
python -c "import shellog; bot = shellog.Bot(); print('OK')"
```

### Documentazione

Mantieni aggiornati:
- README.md (istruzioni base)
- CHANGELOG.md (cosa è cambiato)
- DEPLOYMENT.md (per admin)
- Examples (codice funzionante)

---

## 🎊 Congratulazioni!

Ora shellog è pubblico su PyPI! Chiunque nel mondo può:

```bash
pip install shellog
```

E usare la tua libreria per ricevere notifiche Telegram! 🚀

---

**Prossimi Step Suggeriti:**

1. ⭐ Chiedi agli utenti di mettere una stella su GitHub
2. 📝 Scrivi un blog post / tutorial
3. 🐛 Monitora gli issue su GitHub
4. 🔄 Continua a migliorare e rilasciare updates
5. 📊 Controlla le statistiche di download

Buona fortuna! 🎉

