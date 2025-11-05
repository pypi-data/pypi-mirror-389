# 📊 Telegram API Rate Limits

## ⚠️ Limiti Importanti da Conoscere

Quando usi Shellog, devi rispettare i limiti delle API di Telegram per evitare che i messaggi vengano scartati.

### 🚦 Rate Limits Principali

| Limite | Valore | Note |
|--------|--------|------|
| **Messaggi per secondo (stesso chat)** | 1 msg/sec | ⚠️ PIÙ IMPORTANTE |
| **Messaggi per minuto (stesso chat)** | ~20-30 msg/min | Limite "soft" |
| **Messaggi globali** | ~30 msg/sec | Per tutti i chat combinati |
| **Lunghezza messaggio** | 4096 caratteri | Limite hard |
| **Timeout risposta** | ~10 secondi | Dopo questo Telegram chiude la connessione |

### 🔴 Cosa Succede Se Superi i Limiti?

**1. Rate Limit Superato:**
```
Telegram restituisce errore 429 "Too Many Requests"
Il bot viene temporaneamente bloccato (da pochi secondi a minuti)
```

**2. Messaggi Scartati Silenziosamente:**
```
A volte Telegram accetta la richiesta (200 OK) ma NON invia il messaggio
Nessun errore visibile, il messaggio semplicemente sparisce
```

---

## ✅ Come il Server Gestisce i Limiti

Il nostro `server.py` implementa **due livelli di protezione**:

### 1️⃣ Rate Limiter Interno
```python
MAX_MESSAGES_PER_MINUTE = 10  # Per chat
```
- Blocca richieste se superi 10 messaggi/minuto per chat
- Protegge il bot da abusi

### 2️⃣ Delay Automatico Telegram
```python
time.sleep(1.1)  # Dopo ogni messaggio inviato
```
- Garantisce **1 messaggio al secondo** massimo
- Aggiunto automaticamente dal server
- Tu non devi fare nulla!

---

## 💡 Best Practices

### ✅ GIUSTO - Con Delay

```python
import shellog
import time

bot = shellog.Bot(server_url="https://your-server.com")
bot.addChatId("123456789")

# Invia messaggi con pausa
for i in range(10):
    bot.sendMessage(f"Step {i+1}/10")
    time.sleep(2)  # Fai qualcosa, poi manda il prossimo
```

**Risultato:** ✅ Tutti i 10 messaggi arrivano

---

### ❌ SBAGLIATO - Troppo Veloce

```python
import shellog

bot = shellog.Bot(server_url="https://your-server.com")
bot.addChatId("123456789")

# Invia 10 messaggi istantaneamente
for i in range(10):
    bot.sendMessage(f"Step {i+1}/10")  # NO DELAY!
```

**Risultato:** ❌ Solo alcuni messaggi arrivano, altri vengono scartati

**Nota:** Anche se il server ha il delay automatico, invii troppo veloci possono causare timeout della connessione HTTP.

---

## 🎯 Raccomandazioni per Caso d'Uso

### Notifiche Occasionali (< 5 msg/ora)
```python
# Nessun problema, invia liberamente
bot.sendMessage("Task completato!")
```

### Progress Updates (10-20 msg in sequenza)
```python
# Aggiungi delay di 2-3 secondi tra i messaggi
for i in range(20):
    bot.sendMessage(f"Progress: {i*5}%")
    time.sleep(2)  # ✅ IMPORTANTE
```

### Monitoraggio Continuo (100+ msg/giorno)
```python
# Accumula messaggi e inviali in batch
messages = []
for i in range(100):
    messages.append(f"Log {i}")
    
# Invia ogni 10 messaggi o ogni 5 minuti
if len(messages) >= 10:
    combined = "\n".join(messages[-10:])
    bot.sendMessage(combined)
    time.sleep(3)
```

### Team Notifications (più chat IDs)
```python
# Se hai 5 persone nel team e invii 1 messaggio:
# = 5 messaggi totali (1 per persona)
# Tempo totale: ~5.5 secondi (con delay automatico)

bot.addListChatIds(["123", "456", "789", "101", "112"])
bot.sendMessage("Deploy completato!")  # Ci vogliono ~5.5 secondi
```

---

## 🔍 Debug - Messaggi Non Arrivano?

### Checklist:

1. **✓ Server è online?**
   ```bash
   curl https://your-server.com/health
   ```

2. **✓ Hai avviato conversazione con il bot?**
   - Apri Telegram
   - Cerca il bot
   - Premi START
   - Invia un messaggio qualsiasi

3. **✓ ChatId è corretto?**
   - Invia `/id` al bot
   - Verifica che il numero corrisponda

4. **✓ Stai inviando troppo velocemente?**
   - Aggiungi `time.sleep(2)` tra i messaggi
   - Il server aggiunge già 1.1 sec di delay, ma tu devi comunque fare pause

5. **✓ Guarda i log del server:**
   ```bash
   # Sul server
   # Dovresti vedere errori se Telegram rifiuta messaggi
   ```

---

## 📈 Limiti del Nostro Sistema

### Rate Limiter Interno (Configurabile)

**Default:**
```python
MAX_MESSAGES_PER_MINUTE = 10  # Per chat
```

**Per modificare** (in `server.py`):
```python
# Più permissivo (ma rischi errori Telegram)
MAX_MESSAGES_PER_MINUTE = 20

# Più restrittivo (più sicuro)
MAX_MESSAGES_PER_MINUTE = 5
```

### Delay Telegram (Configurabile)

**Default:**
```python
time.sleep(1.1)  # Dopo ogni messaggio
```

**Per modificare** (in `server.py`):
```python
# Più veloce (rischio maggiore di perdere messaggi)
time.sleep(0.5)  # NON RACCOMANDATO

# Più sicuro
time.sleep(2.0)  # Più lento ma 100% affidabile
```

---

## 🆘 Errori Comuni

### Error 429: Too Many Requests
```
{'error': 'A TelegramBotAPIException occurred: Error code: 429. 
Description: Too Many Requests: retry after 5'}
```

**Soluzione:**
- Aspetta 5 secondi
- Riduci la frequenza dei messaggi
- Aumenta il delay tra i messaggi

### Messaggi Non Arrivano (No Error)
```
Server: 200 OK ✅
Telegram: (nessun messaggio) ❌
```

**Cause:**
- Troppi messaggi troppo veloci
- Chat non inizializzata (utente non ha mai parlato col bot)
- Bot bloccato dall'utente

**Soluzione:**
- Aggiungi delay più lunghi
- Verifica che l'utente abbia avviato il bot
- Controlla i log del server per errori Telegram

---

## 📚 Riferimenti

- [Telegram Bot API - Rate Limits](https://core.telegram.org/bots/faq#my-bot-is-hitting-limits-how-do-i-avoid-this)
- [Flood Control](https://core.telegram.org/bots/faq#how-can-i-message-all-of-my-bot-39s-subscribers-at-once)

---

## 🎓 Riepilogo

1. ✅ **Il server aggiunge automaticamente delay di 1.1 sec** tra i messaggi
2. ✅ **Tu devi comunque aggiungere delay nel tuo codice** (2-3 sec) tra chiamate successive
3. ✅ **Max ~20-30 messaggi/minuto** per chat è sicuro
4. ✅ **Accumula e invia in batch** per monitoraggio ad alta frequenza
5. ⚠️ **Non inviare mai > 1 messaggio/secondo** allo stesso chat

**Segui queste regole e tutti i messaggi arriveranno! 🎯**

