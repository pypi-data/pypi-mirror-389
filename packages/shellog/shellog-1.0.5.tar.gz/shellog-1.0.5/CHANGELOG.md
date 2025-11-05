# Changelog

All notable changes to Shellog will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.5] - 2025-11-04

### 🔒 Security
- **BREAKING CHANGE:** Bot token removed from client library
- Token now stored securely on backend server only
- Users can no longer see the bot token in the package code

### ✨ Added
- New backend server architecture (`server.py`)
- Backend API with rate limiting (10 messages/minute per chat)
- Automatic Telegram rate limit handling (1.1s delay between messages)
- Bot server for `/id` command (`bot_server.py`)
- Support for custom server URL via parameter or environment variable
- Docker support with Dockerfile and docker-compose.yml
- Comprehensive documentation:
  - `DEPLOYMENT.md` - Complete deployment guide
  - `QUICKSTART.md` - 5-minute local testing guide
  - `ARCHITECTURE.md` - System architecture details
  - `TELEGRAM_LIMITS.md` - Telegram API rate limits explained
  - `PUBLISH_TO_PYPI.md` - PyPI publishing guide
- Examples with proper rate limiting
- Health check endpoint (`/health`)
- Nginx and systemd configuration examples
- Support for ngrok, Cloudflare Tunnel, localhost.run

### 🔄 Changed
- Client library now uses `requests` instead of `pyTelegramBotAPI`
- `Bot()` constructor now accepts optional `server_url` parameter
- Removed dependency on `telepot` (replaced with server-side `pyTelegramBotAPI`)
- Updated Python compatibility: 3.6+ (removed Python 2 support)
- Improved error messages and exception handling
- Rate limiter now tracked per chat ID

### 🐛 Fixed
- Messages not arriving due to Telegram rate limits
- Silent message drops when sending too quickly
- Connection timeout issues with rapid message sending

### 📚 Documentation
- Completely rewritten README.md with comprehensive examples
- Added deployment guides for multiple platforms (VPS, Docker, Heroku, Railway)
- Added architecture documentation explaining security design
- Added troubleshooting guides

### 🔧 Technical Details
- Backend server uses Flask
- Production-ready with gunicorn configuration
- Health check endpoint for monitoring
- Request/response validation
- Proper HTTP status codes and error messages

---

## [1.0.2] - Previous Release

### Features
- Basic bot functionality with hardcoded token (insecure)
- `sendMessage()` method
- Multiple chat ID support
- Simple installation via pip

### Issues
- ⚠️ Bot token exposed in client code (security risk)
- ⚠️ No rate limiting
- ⚠️ Messages often dropped by Telegram
- ⚠️ Limited documentation

---

## Migration Guide: 1.0.2 → 1.0.5

### For Users

**Old (1.0.2):**
```python
import shellog

bot = shellog.Bot()  # Token was in the library
bot.addChatId("123456789")
bot.sendMessage("Hello!")
```

**New (1.0.5):**
```python
import shellog

# Must specify server URL
bot = shellog.Bot(server_url="https://your-server.com")
bot.addChatId("123456789")
bot.sendMessage("Hello!")

# Or use environment variable
# export SHELLOG_SERVER_URL="https://your-server.com"
bot = shellog.Bot()
```

### For Administrators

**Required:**
1. Deploy backend server (`server.py`)
2. Deploy bot server (`bot_server.py`)
3. Obtain public URL (ngrok, Cloudflare Tunnel, or VPS)
4. Share URL with users

See `DEPLOYMENT.md` for detailed instructions.

---

## Roadmap

### Planned for 1.1.0
- [ ] Message templates
- [ ] Markdown/HTML formatting support
- [ ] File/image sending
- [ ] Message editing/deletion
- [ ] Conversation history
- [ ] Webhook support for bot server

### Planned for 1.2.0
- [ ] Redis-based rate limiting (for multi-instance deployments)
- [ ] Database logging
- [ ] Admin dashboard
- [ ] User management
- [ ] API authentication (API keys)

### Planned for 2.0.0
- [ ] Multiple bot support
- [ ] Plugin system
- [ ] Advanced scheduling
- [ ] Analytics and metrics

---

## Contributing

We welcome contributions! Please:
1. Open an issue to discuss major changes
2. Follow existing code style
3. Add tests for new features
4. Update documentation

---

## Support

- 📖 Documentation: [GitHub](https://github.com/danmargs/shellog)
- 🐛 Bug Reports: [GitHub Issues](https://github.com/danmargs/shellog/issues)
- 💬 Questions: Open a GitHub Discussion
- 📧 Email: daniele.margiotta11@gmail.com

---

## License

BSD 2-Clause License - see LICENSE file for details.

