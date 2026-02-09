# Przewodnik Startowy dla Studentów - PersonaPlex + Unitree G1

## 🎓 Witajcie Studenci Politechniki Rzeszowskiej!

To repozytorium zostało specjalnie przygotowane dla Was, aby ułatwić naukę i pracę z systemem PersonaPlex w kontekście projektu z robotem humanoidalnym Unitree G1 EDU.

## 📚 Dostępne Materiały w Języku Polskim

### 1. README.pl.md - Podstawy
**Lokalizacja:** `/README.pl.md`

**Co znajdziesz:**
- Wprowadzenie do PersonaPlex
- Instrukcje instalacji krok po kroku
- Podstawowe użycie (serwer i tryb offline)
- Dostępne głosy i prompty
- Przykłady użycia

**Kiedy czytać:** Zacznij tutaj! To Twój pierwszy krok.

### 2. UNITREE_G1_GUIDE.pl.md - Integracja z Robotem
**Lokalizacja:** `/docs/UNITREE_G1_GUIDE.pl.md`

**Co znajdziesz:**
- Architektura integracji PersonaPlex + Unitree G1
- Wymagania sprzętowe
- Instrukcje instalacji dla robota
- **Przykłady kodu** do integracji
- Różne scenariusze użycia (przewodnik, asystent, nauczyciel)
- Rozwiązywanie problemów

**Kiedy czytać:** Gdy już zrozumiesz podstawy i chcesz zintegrować z robotem.

### 3. ARCHITECTURE.pl.md - Jak to Działa
**Lokalizacja:** `/docs/ARCHITECTURE.pl.md`

**Co znajdziesz:**
- Szczegółowa architektura systemu
- Wyjaśnienie wszystkich komponentów (Mimi, Moshi, LM, etc.)
- Przepływ danych w systemie
- Kluczowe koncepty (streaming, ramki, codebooki)
- Pytania i odpowiedzi (FAQ)

**Kiedy czytać:** Gdy chcesz dogłębnie zrozumieć jak działa system od środka.

### 4. client/README.pl.md - Interfejs Webowy
**Lokalizacja:** `/client/README.pl.md`

**Co znajdziesz:**
- Jak uruchomić klienta webowego
- Struktura projektu frontend
- Konfiguracja dla różnych środowisk
- Wskazówki dla eksperymentowania

**Kiedy czytać:** Gdy chcesz pracować z interfejsem webowym lub go modyfikować.

## 💻 Kod z Polskimi Komentarzami

### server.py - Serwer Real-Time
**Lokalizacja:** `/moshi/moshi/server.py`

**Polskie komentarze wyjaśniają:**
- Inicjalizację serwera
- Połączenie WebSocket
- Pętle komunikacji (recv, opus, send)
- Przetwarzanie audio w czasie rzeczywistym
- Każdy krok generowania odpowiedzi

**Kluczowe funkcje z komentarzami:**
- `torch_auto_device()` - wybór GPU/CPU
- `seed_all()` - ustawienie seed dla reprodukowalności
- `ServerState.__init__()` - inicjalizacja komponentów
- `warmup()` - rozgrzewka modeli
- `handle_chat()` - główna obsługa rozmowy
- `recv_loop()` - odbieranie audio
- `opus_loop()` - przetwarzanie i generowanie
- `send_loop()` - wysyłanie audio

### offline.py - Tryb Offline
**Lokalizacja:** `/moshi/moshi/offline.py`

**Polskie komentarze wyjaśniają:**
- Różnice vs tryb real-time
- Przetwarzanie plików WAV
- Pipeline generowania odpowiedzi
- Zapisywanie wyników

**Kluczowe funkcje z komentarzami:**
- `run_inference()` - główna funkcja przetwarzania
- `decode_tokens_to_pcm()` - konwersja tokenów → audio
- `main()` - parsowanie argumentów i uruchomienie

## 🚀 Szybki Start - Twoje Pierwsze Kroki

### Krok 1: Przeczytaj podstawy (15 min)
```bash
# Otwórz w edytorze lub przeglądarce
cat README.pl.md
```

### Krok 2: Zainstaluj system (30 min)
```bash
# Zainstaluj zależności
sudo apt install libopus-dev
pip install moshi/.

# Skonfiguruj Huggingface
export HF_TOKEN=<twój_token>
```

### Krok 3: Przetestuj tryb offline (10 min)
```bash
# Prosty test z przykładowym plikiem
python -m moshi.offline \
  --voice-prompt "NATM1.pt" \
  --input-wav "assets/test/input_assistant.wav" \
  --output-wav "test_output.wav" \
  --output-text "test_output.json" \
  --seed 42424242
```

### Krok 4: Uruchom serwer (10 min)
```bash
# Uruchom serwer WebSocket
SSL_DIR=$(mktemp -d)
python -m moshi.server --ssl "$SSL_DIR"

# Otwórz przeglądarkę: https://localhost:8998
```

### Krok 5: Przeczytaj przewodnik robota (30 min)
```bash
cat docs/UNITREE_G1_GUIDE.pl.md
```

### Krok 6: Zrozum architekturę (45 min)
```bash
cat docs/ARCHITECTURE.pl.md
```

### Krok 7: Eksperymentuj! (∞)
- Zmień prompty tekstowe
- Wypróbuj różne głosy
- Zmodyfikuj kod
- Zintegruj z robotem

## 🎯 Ścieżki Nauki

### Ścieżka A: "Chcę szybko zacząć"
1. README.pl.md - sekcja "Instalacja"
2. Uruchom tryb offline z przykładem
3. UNITREE_G1_GUIDE.pl.md - przykłady kodu
4. Zacznij integrację z robotem

### Ścieżka B: "Chcę dogłębnie zrozumieć"
1. README.pl.md - całość
2. ARCHITECTURE.pl.md - całość
3. Przeczytaj komentarze w server.py
4. Przeczytaj komentarze w offline.py
5. Eksperymentuj z kodem
6. UNITREE_G1_GUIDE.pl.md
7. Zaawansowana integracja

### Ścieżka C: "Mam konkretny problem"
1. Sprawdź FAQ w ARCHITECTURE.pl.md
2. Sprawdź "Rozwiązywanie problemów" w UNITREE_G1_GUIDE.pl.md
3. Przeczytaj komentarze w relevantnej funkcji
4. Zobacz Issues na GitHubie

## 🛠️ Typowe Zadania

### Zmiana osobowości robota
**Gdzie:** Text prompt w wywołaniu
```python
text_prompt = "You are G1, a friendly museum guide robot..."
```

### Zmiana głosu
**Gdzie:** Voice prompt w wywołaniu
```python
voice_prompt = "NATF2.pt"  # Naturalny głos kobiecy 2
```

### Debugowanie problemów
1. Sprawdź logi serwera
2. Użyj trybu offline do izolacji problemu
3. Sprawdź GPU: `nvidia-smi`
4. Przetestuj audio: `arecord` / `aplay`

### Dostosowanie parametrów
**Temperatura i Top-K:**
```python
lm_gen = LMGen(
    lm,
    temp=0.8,        # Wyższe = bardziej kreatywne
    temp_text=0.7,   # Niższe = bardziej konserwatywne
    top_k=250,       # Dla audio
    top_k_text=25    # Dla tekstu
)
```

## 📖 Słownik Terminów

| Termin | Wyjaśnienie |
|--------|-------------|
| **Full-duplex** | Jednoczesne słuchanie i mówienie |
| **Streaming** | Przetwarzanie małymi fragmentami (ramkami) |
| **Frame** | Mały fragment audio (~80ms) |
| **Codes** | Skompresowana reprezentacja audio |
| **Tokens** | Liczby reprezentujące słowa/audio |
| **Codebook** | "Słownik" dla kompresji audio |
| **LM** | Language Model - model językowy |
| **Mimi** | Model kompresji/dekompresji audio |
| **Moshi** | Model językowy PersonaPlex |
| **PCM** | Raw audio (Pulse Code Modulation) |
| **Opus** | Kodek kompresji audio dla sieci |
| **WebSocket** | Protokół komunikacji real-time |
| **Warmup** | Rozgrzewka modelu przed użyciem |
| **Seed** | Ziarno dla reprodukowalnych wyników |
| **Prompt** | Instrukcja dla modelu (text/voice) |

## 🤝 Wsparcie i Pomoc

### Pytania Techniczne
- **Discord:** https://discord.gg/5jAXrrbwRb
- **GitHub Issues:** https://github.com/AI-robot-lab/nvidia-personaplex/issues

### Dokumentacja Oryginalna (Angielska)
- **Paper:** https://research.nvidia.com/labs/adlr/files/personaplex/personaplex_preprint.pdf
- **Demo:** https://research.nvidia.com/labs/adlr/personaplex/
- **Huggingface:** https://huggingface.co/nvidia/personaplex-7b-v1

### Dla Wykładowców
Jeśli jesteś wykładowcą i potrzebujesz dodatkowych materiałów lub masz sugestie ulepszeń, otwórz Issue na GitHubie.

## ✅ Checklist Przed Rozpoczęciem Projektu

- [ ] Przeczytałem README.pl.md
- [ ] Zainstalowałem wszystkie zależności
- [ ] Skonfigurowałem token Huggingface
- [ ] Przetestowałem tryb offline
- [ ] Uruchomiłem serwer lokalnie
- [ ] Przeczytałem UNITREE_G1_GUIDE.pl.md
- [ ] Zrozumiałem podstawową architekturę (ARCHITECTURE.pl.md)
- [ ] Mam dostęp do robota Unitree G1 EDU
- [ ] Znam specyfikację sprzętową środowiska

## 🎓 Zadania dla Studentów

### Zadanie 1: Podstawy (Łatwe)
Uruchom PersonaPlex w trybie offline i wygeneruj odpowiedź na własne pytanie (nagranie WAV).

**Kryteria:**
- [ ] Nagrałeś pytanie jako WAV (5-10 sekund)
- [ ] Uruchomiłeś offline.py z własnym plikiem
- [ ] Otrzymałeś odpowiedź WAV i JSON
- [ ] Zrozumiałeś wyniki

### Zadanie 2: Customizacja (Średnie)
Stwórz własną osobowość robota i przetestuj ją.

**Kryteria:**
- [ ] Napisałeś własny text prompt (rola, zachowanie)
- [ ] Wybrałeś odpowiedni głos
- [ ] Przetestowałeś z 3-5 różnymi pytaniami
- [ ] Zapisałeś wnioski o zachowaniu

### Zadanie 3: Integracja (Trudne)
Zintegruj PersonaPlex z robotem Unitree G1 EDU.

**Kryteria:**
- [ ] Uruchomiłeś serwer PersonaPlex
- [ ] Napisałeś interfejs audio dla robota
- [ ] Robot może prowadzić rozmowę głosową
- [ ] Przetestowałeś w scenariuszu rzeczywistym
- [ ] Udokumentowałeś problemy i rozwiązania

### Zadanie 4: Zaawansowane (Bardzo Trudne)
Rozszerz funkcjonalność systemu.

**Pomysły:**
- Dodaj ROS 2 bridge
- Zaimplementuj rozpoznawanie gestów
- Dodaj persistence rozmów (zapisywanie historii)
- Zintegruj z systemem nawigacji robota
- Dodaj multimodal feedback (LED, ruchy)

## 🌟 Powodzenia!

Ten system jest potężny i skomplikowany, ale z tymi materiałami jesteście dobrze przygotowani. Nie zniechęcajcie się jeśli na początku jest trudno - to normalne!

**Pamiętajcie:**
- Uczcie się krok po kroku
- Eksperymentujcie
- Zadawajcie pytania
- Dzielcie się wiedzą z kolegami

**Miłej nauki i powodzenia w projekcie! 🤖🎓**

---

*Materiały przygotowane specjalnie dla studentów Politechniki Rzeszowskiej*  
*Luty 2026*
