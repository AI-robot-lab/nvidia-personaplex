# Przewodnik Integracji PersonaPlex z Robotem Unitree G1 EDU

## Spis treści
1. [Wprowadzenie](#wprowadzenie)
2. [Przegląd systemu](#przegląd-systemu)
3. [Architektura integracji](#architektura-integracji)
4. [Konfiguracja sprzętowa](#konfiguracja-sprzętowa)
5. [Instalacja oprogramowania](#instalacja-oprogramowania)
6. [Integracja z robotem](#integracja-z-robotem)
7. [Przykłady praktyczne](#przykłady-praktyczne)
8. [Rozwiązywanie problemów](#rozwiązywanie-problemów)

## Wprowadzenie

Ten przewodnik opisuje jak zintegrować model konwersacyjny PersonaPlex z robotem humanoidalnym **Unitree G1 EDU**. Integracja umożliwia robotowi prowadzenie naturalnych rozmów głosowych w czasie rzeczywistym, reagowanie na przerwania użytkownika oraz utrzymywanie spójnej osobowości.

### Dlaczego PersonaPlex dla robota humanoidalnego?

**Zalety modelu full-duplex w robotyce:**
- 🤖 **Naturalne interakcje**: Robot może słuchać i odpowiadać jednocześnie, tak jak ludzie
- ⚡ **Niskie opóźnienia**: Odpowiedzi w czasie rzeczywistym (< 200ms)
- 🎭 **Kontrola osobowości**: Możliwość zaprogramowania różnych charakterów dla różnych zadań
- 🔊 **Różnorodność głosów**: Wybór głosu dostosowanego do kontekstu użycia
- 🗣️ **Obsługa przerw**: Robot potrafi naturalnie reagować gdy użytkownik mu przerywa

### Unitree G1 EDU - Podstawowe informacje

Unitree G1 EDU to zaawansowany robot humanoidalny z:
- 23+ stopniami swobody
- Systemem operacyjnym ROS 2 (Robot Operating System)
- Możliwością integracji z zewnętrznymi systemami AI
- Mikrofony i głośniki do komunikacji audio
- Procesor ARM lub x86 do przetwarzania

## Przegląd systemu

### Komponenty systemu

```
┌─────────────────┐      ┌──────────────────┐      ┌─────────────────┐
│  Unitree G1     │      │  PersonaPlex     │      │  Serwer GPU     │
│                 │◄────►│  Interface       │◄────►│  (opcjonalnie)  │
│  - Mikrofony    │      │  - Audio I/O     │      │  - Model AI     │
│  - Głośniki     │      │  - WebSocket     │      │  - CUDA         │
│  - ROS 2        │      │  - Kontrola      │      │                 │
└─────────────────┘      └──────────────────┘      └─────────────────┘
```

### Przepływ danych

1. **Wejście audio**: Mikrofony robota → Przetwarzanie → Kodowanie Opus
2. **Przetwarzanie**: PersonaPlex → Generowanie odpowiedzi (tekst + audio)
3. **Wyjście audio**: Dekodowanie Opus → Głośniki robota
4. **Wyjście tekstowe**: Transkrypcja → System kontroli robota

## Architektura integracji

### Scenariusz 1: Obliczenia lokalne na robocie

Jeśli robot ma wystarczającą moc obliczeniową (GPU):

```bash
# Uruchomienie serwera PersonaPlex lokalnie na robocie
SSL_DIR=$(mktemp -d)
python -m moshi.server --ssl "$SSL_DIR" --host 0.0.0.0 --port 8998
```

**Zalety**: Niskie opóźnienie, brak zależności od sieci  
**Wady**: Wymaga mocnego GPU na robocie

### Scenariusz 2: Serwer zdalny

Obliczenia na zewnętrznym serwerze GPU:

```bash
# Na serwerze GPU:
SSL_DIR=$(mktemp -d)
python -m moshi.server --ssl "$SSL_DIR" --host 0.0.0.0 --port 8998

# Na robocie: połączenie do serwera poprzez IP
```

**Zalety**: Nie wymaga mocnego sprzętu na robocie  
**Wady**: Wymaga stabilnego połączenia sieciowego, większe opóźnienie

### Scenariusz 3: Tryb offline (dla demonstracji)

Dla scenariuszy gdzie nie jest wymagana interakcja w czasie rzeczywistym:

```bash
python -m moshi.offline \
  --voice-prompt "NATM1.pt" \
  --text-prompt "You are a helpful humanoid robot assistant." \
  --input-wav "user_question.wav" \
  --output-wav "robot_response.wav" \
  --output-text "robot_response.json"
```

## Konfiguracja sprzętowa

### Wymagania minimalne

**Dla obliczeń lokalnych na robocie:**
- GPU: NVIDIA RTX 3060 lub lepsze (min. 8GB VRAM)
- RAM: 16GB
- CPU: 8 rdzeni
- Dysk: 20GB wolnej przestrzeni

**Dla trybu z serwerem zdalnym:**
- Robot: Wystarczy podstawowy procesor ARM/x86
- Serwer: GPU NVIDIA (RTX 3090, A100, H100 lub lepsze)
- Sieć: Połączenie minimum 10 Mbps, opóźnienie < 50ms

### Konfiguracja audio

**Mikrofony:**
- Zintegrowane mikrofony Unitree G1 EDU lub
- Zewnętrzny mikrofon USB (zalecane dla lepszej jakości)
- Sample rate: 24000 Hz (zgodnie z wymaganiami PersonaPlex)

**Głośniki:**
- Zintegrowane głośniki robota lub
- Zewnętrzne głośniki Bluetooth/USB

## Instalacja oprogramowania

### Krok 1: Przygotowanie środowiska Python

```bash
# Utwórz środowisko wirtualne
python -m venv personaplex_env
source personaplex_env/bin/activate  # Linux/Mac
# lub personaplex_env\Scripts\activate  # Windows

# Zainstaluj zależności systemowe
sudo apt install libopus-dev  # Wymagane dla kompresji audio
```

### Krok 2: Instalacja PersonaPlex

```bash
# Sklonuj repozytorium
git clone https://github.com/AI-robot-lab/nvidia-personaplex.git
cd nvidia-personaplex

# Zainstaluj pakiet
pip install moshi/.

# Dla GPU Blackwell (opcjonalnie)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu130
```

### Krok 3: Konfiguracja Huggingface

```bash
# Zaloguj się do Huggingface
pip install huggingface_hub
huggingface-cli login

# Ustaw token jako zmienną środowiskową
export HF_TOKEN=<twój_token_huggingface>
```

**Uwaga**: Musisz zaakceptować licencję modelu na https://huggingface.co/nvidia/personaplex-7b-v1

### Krok 4: Instalacja ROS 2 Bridge (opcjonalnie)

Jeśli chcesz zintegrować z systemem kontroli robota przez ROS 2:

```bash
# Zainstaluj rclpy (Python client library dla ROS 2)
pip install rclpy
```

## Integracja z robotem

### Plik przykładowy: robot_audio_interface.py

Pełny przykład integracji znajduje się w repozytorium jako wzorzec do adaptacji dla Twojego robota.

**Kluczowe elementy interfejsu:**

1. **Inicjalizacja audio** - Połączenie z mikrofonami i głośnikami robota
2. **Połączenie WebSocket** - Komunikacja z serwerem PersonaPlex
3. **Pętla komunikacji** - Jednoczesne wysyłanie i odbieranie strumieni audio
4. **Kodowanie/dekodowanie** - Kompresja audio przez kodek Opus

## Przykłady praktyczne

### Scenariusz 1: Robot-przewodnik muzealny

```python
# Konfiguracja dla robota-przewodnika
TEXT_PROMPT = """You are G1, a museum guide robot at the National Museum. 
You provide engaging explanations about exhibits in a friendly and educational manner. 
You know about art history, science, and cultural artifacts.
Available exhibits: Egyptian mummies, Renaissance paintings, Space exploration, Dinosaur fossils."""

VOICE_PROMPT = "NATF2.pt"  # Naturalny głos kobiecy - przyjazny i wyraźny
```

### Scenariusz 2: Robot-asystent w laboratorium

```python
# Konfiguracja dla asystenta laboratoryjnego
TEXT_PROMPT = """You are G1, a laboratory assistant robot. 
You help researchers by providing information about experimental procedures, 
safety protocols, and equipment usage. You speak clearly and precisely.
Always prioritize safety in your responses."""

VOICE_PROMPT = "NATM0.pt"  # Naturalny głos męski - profesjonalny
```

### Scenariusz 3: Robot do ćwiczeń językowych

```python
# Konfiguracja dla nauczyciela języków
TEXT_PROMPT = """You are G1, an English language practice robot.
You help students practice conversational English by engaging in natural dialogues.
You correct mistakes gently and encourage students to speak.
You adapt your speaking speed to the student's level."""

VOICE_PROMPT = "NATF0.pt"  # Naturalny głos kobiecy - nauczycielski
```

## Rozwiązywanie problemów

### Problem 1: "CUDA out of memory"

**Rozwiązanie:**
```bash
# Użyj CPU offload
python -m moshi.server --ssl "$SSL_DIR" --cpu-offload
```

### Problem 2: Wysokie opóźnienie w odpowiedziach

**Możliwe przyczyny i rozwiązania:**

1. **Słabe połączenie sieciowe** (dla zdalnego serwera)
   - Sprawdź ping: `ping <adres_serwera>`
   - Użyj kabla Ethernet zamiast WiFi

2. **Niewystarczająca moc GPU**
   - Użyj mniejszego batch size
   - Zaktualizuj sterowniki NVIDIA

3. **Problemy z audio**
   - Sprawdź sample rate (powinno być 24000 Hz)
   - Zmniejsz rozmiar bufora

### Problem 3: Brak połączenia WebSocket

**Rozwiązanie:**
```python
# Dla testów lokalnych, wyłącz weryfikację SSL:
ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE
```

## Podsumowanie

Integracja PersonaPlex z robotem Unitree G1 EDU umożliwia:
- ✅ Naturalne rozmowy głosowe w czasie rzeczywistym
- ✅ Kontrolę osobowości i głosu robota
- ✅ Obsługę przerywania przez użytkownika
- ✅ Elastyczne scenariusze zastosowań (przewodnik, asystent, nauczyciel)

**Kolejne kroki:**
1. Zacznij od prostego demo w trybie offline
2. Przetestuj interfejs WebSocket lokalnie
3. Zintegruj z systemem kontroli robota (ROS 2)
4. Dostosuj prompty do konkretnego zastosowania
5. Optymalizuj wydajność dla swojego sprzętu

**Pytania i wsparcie:**
- Discord: https://discord.gg/5jAXrrbwRb
- Issues: https://github.com/AI-robot-lab/nvidia-personaplex/issues

---

*Ostatnia aktualizacja: Luty 2026*
