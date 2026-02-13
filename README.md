# OpenClaw Conversation Agent für Home Assistant

Home Assistant Custom Integration, die Kaspar (OpenClaw) als Conversation Agent registriert.

## 🎯 Architektur

```
ESPHome Device
    ↓ (Voice Assistant)
Home Assistant
    ↓ (Conversation Agent)
OpenClaw Manager API
    ↓ (WebSocket/HTTP)
OpenClaw Gateway
    ↓
Kaspar (DU!)
```

## ⚙️ Installation

### 1. Voice Device im Manager registrieren

**Wichtig:** Home Assistant muss als Voice Device im OpenClaw Manager registriert werden!

1. Öffne **OpenClaw Manager**: https://openclaw-manager.eulencode.de
2. Gehe zu **Voice Devices**
3. **Add Device**:
   - **Instance**: Wähle deine Kaspar-Instanz
   - **Name**: "Home Assistant"
   - **Location**: "home-assistant" (oder dein Standort)
4. **Kopiere den API Token** (wird nur einmal angezeigt!)

### 2. Custom Component installieren

```bash
# Kopiere das Verzeichnis nach Home Assistant
cp -r custom_components/openclaw_conversation /config/custom_components/

# Oder via HACS (wenn published):
# HACS → Integrations → Custom Repositories → Add Repository
```

### 3. Home Assistant neu starten

### 4. Integration hinzufügen

1. **Einstellungen → Geräte & Dienste**
2. **Integration hinzufügen**
3. Suche nach **"OpenClaw Conversation Agent"**
4. Eingeben:
   - **Manager URL**: `https://openclaw-manager.eulencode.de`
   - **Device Token**: *(Token aus Schritt 1)*

### 4. Voice Assistant Pipeline erstellen

1. **Einstellungen → Voice Assistants**
2. **Pipeline hinzufügen**
3. Konfigurieren:
   - **Name**: "Kaspar"
   - **Conversation Agent**: OpenClaw Conversation Agent
   - **Speech-to-Text**: *(Home Assistant Whisper, etc.)*
   - **Text-to-Speech**: *(Home Assistant Piper, Google, etc.)*

### 5. ESPHome Device zuweisen

1. **Einstellungen → Geräte & Dienste → ESPHome**
2. Wähle dein Voice Device (z.B. "Kaspar Voice Assistant")
3. **Voice Assistant Pipeline**: "Kaspar" auswählen

## 🎤 Verwendung

### Mit ESPHome Voice Assistant

```yaml
# In deiner ESPHome Config
voice_assistant:
  microphone: kaspar_mic
  # Home Assistant wählt automatisch die Pipeline
```

### Manuell via Service

```yaml
service: conversation.process
data:
  text: "Wie ist das Wetter?"
  agent_id: <OpenClaw Agent ID>
```

## 🔧 Wie es funktioniert

1. **User spricht** → ESPHome Voice Assistant
2. **STT** → Home Assistant wandelt Sprache in Text
3. **Conversation Agent** → OpenClaw Manager API wird aufgerufen
   - `POST /api/v1/voice/sessions/{sessionId}/message`
   - Body: `{"text": "Wie ist das Wetter?"}`
4. **OpenClaw Manager** → Fügt Context hinzu und sendet an Gateway:
   ```
   [Voice Assistant | Device: Home Assistant | Location: Wohnzimmer | Method: Speech-to-Text | Time: 2026-02-13 20:42:00 UTC]
   Wie ist das Wetter?
   ```
5. **OpenClaw Gateway** → Kaspar Session erhält Message mit Context
6. **Kaspar antwortet** → Text zurück an Manager (mit vollem Context!)
7. **Manager** → Gibt Antwort an Home Assistant zurück
8. **TTS** → Home Assistant spricht Antwort über ESPHome Speaker

## 🐛 Debugging

```bash
# Home Assistant Logs ansehen
tail -f /config/home-assistant.log | grep openclaw

# Oder in HA UI:
# Einstellungen → System → Logs → Nach "openclaw" filtern
```

## 📋 TODO (OpenClaw Manager Side)

Der Manager braucht noch:

1. ✅ **Message Endpoint**: `POST /api/v1/voice/sessions/{sessionId}/message`
2. ⏳ **Gateway Communication**: Manager → Gateway Sessions Send
3. ⏳ **Response Handling**: Warten auf Kaspar's Antwort
4. ⏳ **Optional TTS**: Audio-File generieren für offline playback

## 🦉 Vorteile

- ✅ **Kaspar als Voice Assistant** in Home Assistant
- ✅ **Volle Kontext-Awareness** (Kaspar kennt dein Setup)
- ✅ **Multi-Room Support** (verschiedene ESPHome Devices)
- ✅ **Location-aware** (Kaspar weiß aus welchem Raum die Frage kommt)
- ✅ **Home Assistant Integration** (Kaspar kann Geräte steuern via HA)

## 🔗 Links

- **OpenClaw Manager**: https://openclaw-manager.eulencode.de
- **OpenClaw Docs**: https://docs.openclaw.ai
- **GitHub**: https://github.com/eulennest/ha-openclaw-conversation
