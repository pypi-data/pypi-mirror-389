# Shellog Deployment Guide

Questa guida spiega come rimettere in piedi l'intero sistema Shellog con la nuova architettura sicura.

## 🏗️ Architettura del Sistema

Il sistema è composto da **3 componenti**:

```
[Utenti Python] → [Libreria shellog] → [Backend Server] → [Telegram Bot API]
                                          ↓
                                    [Bot Server (/id)]
```

1. **Backend Server** (`server.py`) - API REST che gestisce l'invio messaggi (contiene il token)
2. **Bot Server** (`bot_server.py`) - Gestisce il comando `/id` su Telegram
3. **Libreria Python** (`shellog`) - Installata dagli utenti, chiama il backend server

### 🔒 Perché questa architettura?

- ✅ **Il token del bot rimane SEGRETO** sul server
- ✅ Gli utenti **non vedono mai il token** nel codice della libreria
- ✅ Previene abusi con **rate limiting** e validazione
- ✅ Gli utenti possono fare `pip install shellog` in sicurezza

---

## 🚀 Setup Completo

### 1️⃣ Setup del Backend Server + Bot Server

Devi hostare **entrambi** i server (possono stare sulla stessa macchina):

#### Installazione Dipendenze

```bash
# Installa le dipendenze del server
pip install -r requirements-server.txt
```

#### Avvio dei Server

**Terminal 1 - Backend Server:**
```bash
# Opzionale: usa variabile d'ambiente per il token
export SHELLOG_BOT_TOKEN="6300373442:AAEeMHpIq_ttEGdmQzE04706UR0rJISCSHM"

# Avvia il backend server
python server.py
```

**Terminal 2 - Bot Server:**
```bash
# Avvia il bot per gestire /id
python bot_server.py
```

---

### 2️⃣ Deploy in Produzione

#### Opzione A: Deploy su VPS/Server Linux (Raccomandato)

##### 1. Crea servizi systemd

**Backend Server:**
```bash
sudo nano /etc/systemd/system/shellog-backend.service
```

```ini
[Unit]
Description=Shellog Backend Server
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/path/to/shellog
Environment="SHELLOG_BOT_TOKEN=6300373442:AAEeMHpIq_ttEGdmQzE04706UR0rJISCSHM"
Environment="PORT=5005"
ExecStart=/usr/bin/python3 /path/to/shellog/server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Bot Server:**
```bash
sudo nano /etc/systemd/system/shellog-bot.service
```

```ini
[Unit]
Description=Shellog Telegram Bot
After=network.target

[Service]
Type=simple
User=youruser
WorkingDirectory=/path/to/shellog
ExecStart=/usr/bin/python3 /path/to/shellog/bot_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

##### 2. Attiva i servizi

```bash
sudo systemctl daemon-reload
sudo systemctl enable shellog-backend shellog-bot
sudo systemctl start shellog-backend shellog-bot
sudo systemctl status shellog-backend shellog-bot
```

##### 3. Setup Nginx come Reverse Proxy (raccomandato)

```bash
sudo nano /etc/nginx/sites-available/shellog
```

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5005;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/shellog /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# Aggiungi SSL con Let's Encrypt
sudo certbot --nginx -d your-domain.com
```

#### Opzione B: Deploy con Docker

**docker-compose.yml:**

```yaml
version: '3.8'

services:
  backend:
    build: .
    container_name: shellog-backend
    ports:
      - "5005:5005"
    environment:
      - SHELLOG_BOT_TOKEN=6300373442:AAEeMHpIq_ttEGdmQzE04706UR0rJISCSHM
      - PORT=5005
    restart: always
    command: python server.py

  bot:
    build: .
    container_name: shellog-bot
    environment:
      - SHELLOG_BOT_TOKEN=6300373442:AAEeMHpIq_ttEGdmQzE04706UR0rJISCSHM
    restart: always
    command: python bot_server.py
```

**Dockerfile:**

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements-server.txt .
RUN pip install --no-cache-dir -r requirements-server.txt

COPY server.py bot_server.py ./

EXPOSE 5005

# Command will be specified in docker-compose.yml
```

**Avvia con:**
```bash
docker-compose up -d
```

#### Opzione C: Deploy su Heroku

**Procfile:**
```
web: gunicorn server:app
worker: python bot_server.py
```

**Deploy:**
```bash
heroku create shellog-backend
heroku config:set SHELLOG_BOT_TOKEN="6300373442:AAEeMHpIq_ttEGdmQzE04706UR0rJISCSHM"
git push heroku main
heroku ps:scale web=1 worker=1
```

**Ottieni l'URL del server:**
```bash
heroku info
# Usa l'URL (es: https://shellog-backend.herokuapp.com)
```

#### Opzione D: Deploy su Railway / Render

1. Collega il repository GitHub
2. Crea 2 servizi:
   - **Backend**: Comando `gunicorn server:app`, porta 5005
   - **Bot**: Comando `python bot_server.py`
3. Aggiungi variabile d'ambiente: `SHELLOG_BOT_TOKEN`
4. Deploy automatico

---

### 3️⃣ Pubblicazione della Libreria su PyPI

Una volta che il server è online, puoi pubblicare la libreria:

```bash
# Installa gli strumenti
pip install build twine

# Aggiorna l'URL del server nel README.md per gli utenti
# Esempio: Gli utenti dovranno usare bot = shellog.Bot(server_url="https://your-server.com")

# Build del pacchetto
python -m build

# Pubblica su PyPI
twine upload dist/*
```

**⚠️ IMPORTANTE**: Prima di pubblicare, aggiorna il `README.md` per indicare agli utenti l'URL del tuo server!

---

## 📖 Istruzioni per gli Utenti Finali

Una volta pubblicato, gli utenti useranno la libreria così:

### Installazione

```bash
pip install shellog
```

### Ottenere il ChatId

1. Apri Telegram e cerca il tuo bot (es: `@shellogbot`)
2. Invia `/id` al bot
3. Ricevi il tuo ChatId

### Utilizzo

```python
import shellog

# Connettiti al tuo server (o usa variabile d'ambiente SHELLOG_SERVER_URL)
bot = shellog.Bot(server_url="https://your-server.com")

# Aggiungi il tuo ChatId
bot.addChatId("123456789")

# Invia messaggi
bot.sendMessage("Hello from my Python script!")
```

---

## 🧪 Test del Sistema

### Test Locale

**Terminal 1:**
```bash
python server.py
```

**Terminal 2:**
```bash
python bot_server.py
```

**Terminal 3:**
```bash
# Test del backend
curl -X POST http://localhost:5005/api/send_message \
  -H "Content-Type: application/json" \
  -d '{"chat_ids": ["YOUR_CHAT_ID"], "text": "Test message"}'

# Test della libreria
python example.py
```

**Telegram:**
- Invia `/id` al tuo bot per verificare che risponda

### Test in Produzione

```python
import shellog

# Usa il tuo server di produzione
bot = shellog.Bot(server_url="https://your-server.com")
bot.addChatId("YOUR_CHAT_ID")
bot.sendMessage("🎉 Production test!")
```

---

## 📊 Monitoraggio

### Log del Backend Server

```bash
# Con systemd
sudo journalctl -u shellog-backend -f

# Con Docker
docker logs -f shellog-backend
```

### Log del Bot Server

```bash
# Con systemd
sudo journalctl -u shellog-bot -f

# Con Docker
docker logs -f shellog-bot
```

### Health Check

```bash
curl http://your-server.com/health
```

Risposta attesa:
```json
{"status": "ok", "service": "shellog-backend"}
```

---

## 🔧 Configurazione Avanzata

### Rate Limiting

Il server ha rate limiting integrato (10 messaggi/minuto per chat). Per modificarlo:

```python
# In server.py
MAX_MESSAGES_PER_MINUTE = 20  # Cambia questo valore
```

### Variabili d'Ambiente

**Server:**
- `SHELLOG_BOT_TOKEN` - Token del bot Telegram
- `PORT` - Porta del server (default: 5005)
- `DEBUG` - Modalità debug (default: False)

**Client (utenti finali):**
- `SHELLOG_SERVER_URL` - URL del backend server

### Sicurezza Aggiuntiva

#### 1. API Key per il Backend (opzionale)

Aggiungi autenticazione al backend:

```python
# In server.py, aggiungi:
API_KEY = os.environ.get('SHELLOG_API_KEY')

@app.before_request
def check_api_key():
    if request.path != '/health':
        key = request.headers.get('X-API-Key')
        if key != API_KEY:
            return jsonify({'error': 'Unauthorized'}), 401
```

Poi gli utenti dovranno passare l'API key:

```python
# Modifica __init__.py per supportare API key
bot = shellog.Bot(server_url="...", api_key="your-key")
```

#### 2. HTTPS

Usa sempre HTTPS in produzione:
- Con Nginx: Usa Let's Encrypt (vedi sopra)
- Con Heroku/Railway: HTTPS automatico
- Con server custom: Ottieni un certificato SSL

---

## 🆘 Troubleshooting

### Backend non riceve richieste
- Verifica che il server sia in esecuzione: `curl http://localhost:5005/health`
- Controlla i log per errori
- Verifica firewall/porte aperte

### Bot non risponde a /id
- Verifica che `bot_server.py` sia in esecuzione
- Controlla che il token sia corretto
- L'utente deve aver avviato il bot su Telegram

### Utenti non ricevono messaggi
- L'utente deve aver avviato una conversazione con il bot almeno una volta
- Verifica il ChatId (deve essere numerico)
- Controlla i log del backend per errori

### Rate Limit

Se un utente supera il rate limit:
```json
{
  "errors": [{
    "chat_id": "123456789",
    "error": "Rate limit exceeded (max 10 messages per minute)"
  }]
}
```

Soluzione: Aumenta `MAX_MESSAGES_PER_MINUTE` o aspetta 1 minuto

---

## 📝 Checklist Deploy

- [ ] Backend server installato e in esecuzione
- [ ] Bot server installato e in esecuzione
- [ ] Server accessibile pubblicamente (URL/IP pubblico)
- [ ] HTTPS configurato (raccomandato)
- [ ] Bot Telegram funzionante (risponde a `/id`)
- [ ] Test invio messaggio completato
- [ ] README.md aggiornato con l'URL del server
- [ ] Libreria pubblicata su PyPI
- [ ] Monitoring/logs configurati
- [ ] Backup del token del bot in luogo sicuro

---

## 🎉 Conclusione

Ora hai un sistema Shellog completamente funzionante e sicuro! Gli utenti possono:

1. Installare `pip install shellog`
2. Ottenere il ChatId dal tuo bot
3. Usare la libreria senza vedere il token

Il token rimane al sicuro sul tuo server! 🔒
