# 🚀 Quick Start Guide - Test Shellog in 5 Minutes

Questa guida ti aiuta a testare Shellog localmente prima del deploy.

## ✅ Prerequisiti

```bash
pip install flask pyTelegramBotAPI requests
```

## 📝 Step by Step

### 1️⃣ Avvia il Backend Server

Apri un terminal e avvia il server backend:

```bash
cd /Users/danielemargiotta/Downloads/shellog-main
python server.py
```

Dovresti vedere:
```
🚀 Shellog Backend Server starting on port 5005...
📡 API endpoint: http://localhost:5005/api/send_message
❤️  Health check: http://localhost:5005/health
```

**✅ Lascia questo terminal aperto!**

---

### 2️⃣ Avvia il Bot Server (opzionale per /id)

Apri un NUOVO terminal e avvia il bot:

```bash
cd /Users/danielemargiotta/Downloads/shellog-main
python bot_server.py
```

Dovresti vedere:
```
🤖 Shellog Bot is starting...
Bot is ready and listening for messages!
```

**✅ Lascia anche questo terminal aperto!**

---

### 3️⃣ Ottieni il tuo ChatId

1. Apri Telegram (web o app)
2. Cerca il tuo bot (quello con token `6300373442:AAE...`)
3. Invia il comando: `/id`
4. Il bot ti risponderà con il tuo ChatId (es: `180612499`)

**💡 Il tuo ChatId è già in `example.py` → `180612499`**

---

### 4️⃣ Testa la Libreria

Apri un TERZO terminal e prova:

```bash
cd /Users/danielemargiotta/Downloads/shellog-main

# Installa la libreria in modalità development
pip install -e .

# Esegui l'esempio
python example.py
```

**🎉 Dovresti ricevere i messaggi su Telegram!**

---

## 🧪 Test Manuale con curl

Se vuoi testare solo il backend senza Python:

```bash
# Test health check
curl http://localhost:5005/health

# Test invio messaggio
curl -X POST http://localhost:5005/api/send_message \
  -H "Content-Type: application/json" \
  -d '{
    "chat_ids": ["180612499"],
    "text": "Test message from curl! 🚀"
  }'
```

---

## 🐛 Troubleshooting

### "Cannot connect to Shellog server"

**Problema:** Il backend server non è in esecuzione.

**Soluzione:**
```bash
# Verifica che il server sia attivo
curl http://localhost:5005/health

# Se non risponde, avvia server.py
python server.py
```

---

### "No chat IDs registered"

**Problema:** Non hai aggiunto un ChatId.

**Soluzione:**
```python
bot = shellog.Bot()
bot.addChatId("180612499")  # Usa il TUO ChatId!
```

---

### "Chat not found" su Telegram

**Problema:** Non hai mai avviato una conversazione con il bot.

**Soluzione:**
1. Cerca il bot su Telegram
2. Premi **START** o invia un messaggio qualsiasi
3. Riprova a inviare il messaggio

---

### Bot non risponde a /id

**Problema:** `bot_server.py` non è in esecuzione.

**Soluzione:**
```bash
python bot_server.py
```

---

## 🎯 Test Completo

Script di test completo:

```python
import shellog
import time

# Connetti al server locale
bot = shellog.Bot(server_url="http://localhost:5005")

# Aggiungi il tuo ChatId
bot.addChatId("180612499")  # <-- CAMBIA CON IL TUO!

# Test 1: Messaggio semplice
print("Test 1: Sending simple message...")
bot.sendMessage("✅ Test 1: Simple message works!")
time.sleep(2)

# Test 2: Emoji e caratteri speciali
print("Test 2: Testing emojis...")
bot.sendMessage("🚀 Test 2: Emojis work! 🎉")
time.sleep(2)

# Test 3: Messaggio lungo
print("Test 3: Testing long message...")
long_text = "Test 3: " + "Long message! " * 50
bot.sendMessage(long_text)
time.sleep(2)

# Test 4: Multiple chat IDs
print("Test 4: Testing multiple recipients...")
bot.addChatId("180612499")  # Aggiungi lo stesso ID due volte (no duplicati)
bot.sendMessage("Test 4: Multiple IDs (no duplicates)")
time.sleep(2)

# Test 5: Error handling
print("Test 5: Testing error handling...")
try:
    bot.clearChatId()  # Rimuovi tutti gli ID
    bot.sendMessage("This should fail")
except ValueError as e:
    print(f"✅ Caught expected error: {e}")
    bot.addChatId("180612499")  # Re-aggiungi l'ID

print("\n✅ All tests completed! Check your Telegram chat.")
```

Salva come `test_all.py` ed esegui:

```bash
python test_all.py
```

---

## 📊 Riepilogo Terminali

Dovresti avere **3 terminal aperti**:

1. **Terminal 1**: `python server.py` (Backend API)
2. **Terminal 2**: `python bot_server.py` (Bot Telegram)
3. **Terminal 3**: `python example.py` (Test della libreria)

---

## ✅ Checklist Funzionante

- [ ] `server.py` in esecuzione
- [ ] `bot_server.py` in esecuzione  
- [ ] Bot risponde a `/id` su Telegram
- [ ] `curl http://localhost:5005/health` ritorna `{"status": "ok"}`
- [ ] `python example.py` invia messaggi su Telegram
- [ ] Ricevi i messaggi sul tuo chat Telegram

---

## 🎉 Prossimi Passi

Una volta che tutto funziona in locale:

1. **Deploy in Produzione** → Leggi [DEPLOYMENT.md](DEPLOYMENT.md)
2. **Ottieni un dominio/server** → Es: `https://shellog.yourdomain.com`
3. **Aggiorna README.md** → Inserisci l'URL del tuo server
4. **Pubblica su PyPI** → `python -m build && twine upload dist/*`

Buon coding! 🚀

