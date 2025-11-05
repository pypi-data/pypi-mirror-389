# 🏗️ Shellog Architecture

## 📊 Panoramica del Sistema

Shellog è composto da 3 componenti principali che lavorano insieme per fornire un sistema sicuro di notifiche Telegram per applicazioni Python.

```
┌─────────────────┐
│  User's Python  │
│      Code       │
└────────┬────────┘
         │
         │ import shellog
         │ bot.sendMessage()
         ▼
┌─────────────────┐
│     shellog     │  ← Libreria installata via pip
│     Library     │     (NO token visibile)
└────────┬────────┘
         │
         │ HTTP POST
         │ /api/send_message
         ▼
┌─────────────────┐
│  Backend Server │  ← server.py (con il token)
│   (server.py)   │     Hosted su tuo server
└────────┬────────┘
         │
         │ Telegram Bot API
         ▼
┌─────────────────┐
│   Telegram API  │
│                 │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   User's Chat   │  📱
│    on Telegram  │
└─────────────────┘

┌─────────────────┐
│   Bot Server    │  ← bot_server.py (per comando /id)
│ (bot_server.py) │     Hosted su tuo server
└─────────────────┘
```

---

## 🔐 Sicurezza: Perché questa Architettura?

### ❌ Problema dell'Architettura Vecchia

```python
# shellog/__init__.py (VECCHIO - INSICURO)
class Bot:
    def __init__(self):
        self.bot = telebot.TeleBot('6300373442:AAEe...')  # ⚠️ TOKEN VISIBILE!
```

**Problemi:**
1. ✗ Chiunque fa `pip install shellog` vede il token
2. ✗ Il token può essere estratto con `pip show -f shellog`
3. ✗ Abuso del bot (spam illimitato)
4. ✗ Token compromesso se pubblicato su GitHub/PyPI

### ✅ Soluzione con Backend Server

```python
# shellog/__init__.py (NUOVO - SICURO)
class Bot:
    def __init__(self, server_url=None):
        self.server_url = server_url or os.environ.get('SHELLOG_SERVER_URL')
        # NO TOKEN nel codice!
```

**Vantaggi:**
1. ✓ Token rimane sul server (mai esposto)
2. ✓ Rate limiting per prevenire abusi
3. ✓ Controllo centralizzato
4. ✓ Facilmente aggiornabile/revocabile

---

## 📂 Struttura dei File

```
shellog-main/
├── shellog/                    # Libreria Python (per pip install)
│   └── __init__.py            # Client che chiama il backend
│
├── server.py                  # Backend API (tiene il token)
├── bot_server.py              # Bot Telegram (gestisce /id)
│
├── setup.py                   # Configurazione pip
├── requirements-server.txt    # Dipendenze server
├── requirements-client.txt    # Dipendenze libreria
│
├── example.py                 # Esempi di utilizzo
├── README.md                  # Documentazione utenti
├── DEPLOYMENT.md              # Guida deploy per admin
├── QUICKSTART.md              # Test locale rapido
├── ARCHITECTURE.md            # Questo file
│
├── Dockerfile                 # Docker build
├── docker-compose.yml         # Docker orchestration
├── Procfile                   # Heroku/Railway deploy
├── runtime.txt                # Versione Python
├── gunicorn_config.py         # Configurazione production
│
└── .gitignore                 # File da ignorare
```

---

## 🔄 Flusso di Comunicazione

### 1️⃣ Ottenere il ChatId

```
User → Telegram App → @shellogbot
User: "/id"
                      ↓
              bot_server.py riceve comando
                      ↓
              Telegram → User: "Your ChatId is: 123456789"
```

### 2️⃣ Inviare un Messaggio

```
User's Python Code:
  bot = shellog.Bot(server_url="https://your-server.com")
  bot.addChatId("123456789")
  bot.sendMessage("Hello!")
                      ↓
              shellog library (locale)
                      ↓
              HTTP POST → https://your-server.com/api/send_message
              {
                "chat_ids": ["123456789"],
                "text": "Hello!"
              }
                      ↓
              server.py riceve richiesta
                      ↓
              Verifica rate limit
                      ↓
              Chiama Telegram Bot API con token
                      ↓
              Telegram invia messaggio al chat 123456789
                      ↓
              User riceve notifica su Telegram 📱
```

---

## 🛡️ Componente: Backend Server (`server.py`)

### Responsabilità

- 🔐 Custodisce il token del bot (variabile d'ambiente)
- 📨 Riceve richieste HTTP da utenti
- ✅ Valida i dati (chat_ids, text)
- 🚦 Applica rate limiting (max 10 msg/min per chat)
- 📤 Inoltra messaggi a Telegram Bot API
- 📊 Ritorna risultati/errori agli utenti

### Endpoint API

#### `GET /health`
Health check del server.

**Response:**
```json
{
  "status": "ok",
  "service": "shellog-backend"
}
```

#### `POST /api/send_message`
Invia messaggi a uno o più chat.

**Request:**
```json
{
  "chat_ids": ["123456789", "987654321"],
  "text": "Your message"
}
```

**Response:**
```json
{
  "success": 2,
  "failed": 0,
  "results": [
    {"chat_id": "123456789", "status": "sent"},
    {"chat_id": "987654321", "status": "sent"}
  ]
}
```

**Error Response:**
```json
{
  "success": 1,
  "failed": 1,
  "results": [...],
  "errors": [
    {
      "chat_id": "999999",
      "error": "Chat not found"
    }
  ]
}
```

### Rate Limiting

Implementato in memoria con dict:
```python
rate_limiter = defaultdict(list)
MAX_MESSAGES_PER_MINUTE = 10

def check_rate_limit(chat_id):
    now = time.time()
    rate_limiter[chat_id] = [t for t in rate_limiter[chat_id] if now - t < 60]
    if len(rate_limiter[chat_id]) >= MAX_MESSAGES_PER_MINUTE:
        return False
    rate_limiter[chat_id].append(now)
    return True
```

---

## 🤖 Componente: Bot Server (`bot_server.py`)

### Responsabilità

- 🆔 Gestisce il comando `/id` su Telegram
- 👋 Messaggio di benvenuto con `/start` e `/help`
- 📝 Risponde con il ChatId all'utente

### Comandi Telegram

| Comando | Descrizione | Response |
|---------|-------------|----------|
| `/start` | Benvenuto | Messaggio di benvenuto + istruzioni |
| `/help` | Aiuto | Istruzioni per usare shellog |
| `/id` | Ottieni ChatId | `Your ChatId is: 123456789` |
| Altro | Messaggio generico | "Use /id to get your ChatId" |

### Esempio Interaction

```
User → Bot: /id
Bot → User: Your ChatId is: `180612499`
             Use this ChatId in your Python code with shellog!
```

---

## 📚 Componente: Libreria Client (`shellog/__init__.py`)

### Responsabilità

- 🔌 Interfaccia semplice per gli utenti
- 🌐 Chiama il backend server via HTTP
- 📋 Gestisce lista di chat_ids
- ❌ Gestisce errori e timeout
- 📖 Fornisce API pulita e documentata

### API Pubblica

```python
class Bot:
    def __init__(self, server_url=None)
    def sendMessage(self, text: str) -> dict
    def addChatId(self, id: str)
    def addListChatIds(self, ids: list)
    def removeChatId(self, id: str)
    def removeListChatIds(self, ids: list)
    def clearChatId(self)
```

### Gestione Errori

```python
try:
    bot.sendMessage("Hello")
except ValueError:
    # No chat IDs o testo vuoto
except Exception as e:
    # Server unreachable, timeout, ecc.
```

---

## 🚀 Deploy Scenarios

### Scenario 1: Single Server (Semplice)

```
server.py (Flask dev server) ← Port 5005
bot_server.py                ← Background
```

**Pro:** Semplice, veloce da testare
**Contro:** Non production-ready

---

### Scenario 2: Production con Systemd (Raccomandato)

```
server.py (gunicorn) ← systemd service
bot_server.py        ← systemd service
nginx (reverse proxy) ← Port 80/443
```

**Pro:** Stabile, restart automatico, SSL con Let's Encrypt
**Contro:** Richiede VPS Linux

---

### Scenario 3: Docker (Moderno)

```
Docker Container 1: server.py (gunicorn)
Docker Container 2: bot_server.py
```

**Pro:** Portabile, facile deploy, isolamento
**Contro:** Richiede Docker installato

---

### Scenario 4: Cloud Platform (Heroku/Railway)

```
Web Dyno: server.py
Worker Dyno: bot_server.py
```

**Pro:** Zero config server, HTTPS automatico, scaling
**Contro:** Costo mensile, cold start

---

## 📊 Confronto Dipendenze

### Server Side
```
flask              # Web framework
pyTelegramBotAPI   # Telegram Bot API
gunicorn           # WSGI server (production)
```

### Client Side (Libreria)
```
requests           # HTTP client (solo questo!)
```

**Nota:** Gli utenti NON installano flask o pyTelegramBotAPI!

---

## 🔧 Variabili d'Ambiente

### Server Side (server.py, bot_server.py)

| Variabile | Descrizione | Default | Richiesta |
|-----------|-------------|---------|-----------|
| `SHELLOG_BOT_TOKEN` | Token Telegram Bot | - | ✓ Sì |
| `PORT` | Porta server | 5005 | ✗ No |
| `DEBUG` | Debug mode | False | ✗ No |

### Client Side (utenti della libreria)

| Variabile | Descrizione | Default | Richiesta |
|-----------|-------------|---------|-----------|
| `SHELLOG_SERVER_URL` | URL backend | http://localhost:5005 | ✗ No |

---

## 🔍 Security Best Practices

### ✅ Cosa Abbiamo Implementato

1. **Token su Server Only**
   - Token mai nel codice della libreria
   - Usa variabili d'ambiente

2. **Rate Limiting**
   - Max 10 messaggi/minuto per chat
   - Previene spam

3. **Validazione Input**
   - Limita numero destinatari (max 50)
   - Limita lunghezza messaggio (max 4096)

4. **HTTPS Ready**
   - Configurazioni nginx/SSL pronte
   - Heroku/Railway hanno HTTPS automatico

### 🔒 Ulteriori Miglioramenti (Opzionali)

1. **API Key per Backend**
   ```python
   # Richiedi API key per chiamare /api/send_message
   X-API-Key: your-secret-key
   ```

2. **Database per Rate Limiting**
   - Usa Redis invece di dict in memoria
   - Persistente tra restart

3. **Monitoring & Logging**
   - Sentry per error tracking
   - Prometheus/Grafana per metriche

4. **Webhook invece di Polling**
   - Per bot_server.py usa webhook invece di polling
   - Più efficiente in produzione

---

## 🎓 Lessons Learned

### Perché NON Usare Token nel Client

```python
# ❌ BAD - Token esposto
import shellog
# -> Il token è nel file __init__.py
# -> Chiunque può leggerlo con:
#    pip show shellog
#    cat site-packages/shellog/__init__.py
```

### Perché Usare Backend Server

```python
# ✅ GOOD - Token nascosto
import shellog
bot = shellog.Bot(server_url="https://my-server.com")
# -> Il token è SOLO su my-server.com
# -> Gli utenti chiamano solo API pubbliche
# -> Impossibile estrarre il token
```

---

## 📈 Scalability

### Per Piccoli Progetti (< 100 utenti)

```python
# server.py con Flask dev server
python server.py
```

### Per Progetti Medi (100-1000 utenti)

```bash
# Gunicorn con 4 workers
gunicorn -w 4 -b 0.0.0.0:5005 server:app
```

### Per Progetti Grandi (> 1000 utenti)

```bash
# Gunicorn + Nginx + Load Balancer
# Multiple instances
# Redis per rate limiting
# Database per logs
```

---

## 🧪 Testing Strategy

### 1. Test Locale

```bash
# Terminal 1
python server.py

# Terminal 2
python bot_server.py

# Terminal 3
python example.py
```

### 2. Test Integrazione

```python
# Testa tutti i componenti insieme
curl http://localhost:5005/health
curl -X POST ... /api/send_message
```

### 3. Test Production

```bash
# Usa server remoto
export SHELLOG_SERVER_URL="https://your-server.com"
python example.py
```

---

## 📝 Changelog Architetturale

### v1.0.2 → v1.0.5 (Questa versione)

**Breaking Changes:**
- ✗ Rimosso: Token hardcoded in `__init__.py`
- ✗ Rimosso: Dipendenza `telepot`/`telebot` nel client

**New Features:**
- ✓ Aggiunto: Backend server (`server.py`)
- ✓ Aggiunto: Parametro `server_url` nel costruttore
- ✓ Aggiunto: Supporto `SHELLOG_SERVER_URL` env var
- ✓ Aggiunto: Rate limiting
- ✓ Aggiunto: Validazione input
- ✓ Cambiato: Client usa `requests` invece di `telebot`

**Migration Guide per Utenti:**
```python
# VECCHIO (v1.0.2)
import shellog
bot = shellog.Bot()  # Token era nel codice

# NUOVO (v1.0.5)
import shellog
bot = shellog.Bot(server_url="https://your-server.com")
# Oppure usa env var SHELLOG_SERVER_URL
```

---

## 🤔 FAQ Architetturali

**Q: Perché non usare Telegram webhook invece di polling?**  
A: Polling è più semplice per iniziare. In produzione si può migrare a webhook.

**Q: Perché Flask invece di FastAPI?**  
A: Flask è più maturo e stabile. FastAPI è un'ottima alternativa.

**Q: Posso usare lo stesso server per più bot?**  
A: Sì, ma devi modificare il codice per accettare bot_token come parametro.

**Q: Il rate limiter è shared tra workers di gunicorn?**  
A: No, è in memoria. Per produzione usa Redis.

**Q: Serve un database?**  
A: No per funzionalità base. Utile per logging avanzato.

---

## 📚 Risorse Aggiuntive

- [Telegram Bot API](https://core.telegram.org/bots/api)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [Gunicorn Documentation](https://docs.gunicorn.org/)
- [Docker Documentation](https://docs.docker.com/)
- [Heroku Python Guide](https://devcenter.heroku.com/categories/python-support)

---

Questa architettura bilanzia **semplicità**, **sicurezza** e **scalabilità**! 🚀

