# moshi-client - Interfejs użytkownika PersonaPlex

Frontend dla demo PersonaPlex - interfejs webowy umożliwiający interakcję z modelem konwersacyjnym.

## Co to jest?

Ten klient webowy to interfejs użytkownika, który:
- Umożliwia rozmowy głosowe z modelem PersonaPlex przez przeglądarkę
- Obsługuje mikrofon i głośniki komputera
- Komunikuje się z serwerem PersonaPlex przez WebSocket
- Pozwala na konfigurację głosu i osobowości

## Uruchomienie klienta

### Wymagania wstępne

- **Node.js** jest wymagany. Zalecam użycie [NVM](https://github.com/nvm-sh/nvm) aby zarządzać wersją Node.js i upewnić się, że używasz zalecanej wersji dla tego projektu.
  
  ```bash
  # Zainstaluj NVM (jeśli nie masz)
  curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
  
  # Użyj zalecanej wersji Node.js z pliku .nvmrc
  nvm use
  ```

### Krok po kroku

1. **Wygeneruj parę kluczy publiczny/prywatny** (`cert.pem` i `key.pem`) i skopiuj je do głównego katalogu tego pakietu

   ```bash
   # Przykład generowania self-signed certificate dla testów lokalnych
   openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem -days 365 -nodes
   ```

   **Wyjaśnienie**: Certyfikaty SSL są wymagane, ponieważ przeglądarki wymagają HTTPS dla dostępu do mikrofonu.

2. **Utwórz plik `.env.local`** i dodaj wpis dla `VITE_QUEUE_API_PATH` (domyślnie powinno być `/api`)

   ```bash
   echo "VITE_QUEUE_API_PATH=/api" > .env.local
   ```

3. **Zainstaluj zależności** przed pierwszym uruchomieniem lub po aktualizacji dependencies:

   ```bash
   npm install
   ```

4. **Uruchom projekt w trybie deweloperskim**:

   ```bash
   npm run dev
   ```

   Klient będzie dostępny domyślnie pod adresem `https://localhost:5173`

5. **Zbuduj projekt do produkcji** (opcjonalnie):

   ```bash
   npm run build
   ```

   Zbudowane pliki znajdą się w katalogu `dist/`

## Pomijanie kolejki (standalone use)

Aby pominąć kolejkę dla samodzielnego użycia, po uruchomieniu projektu przejdź do:

```
https://localhost:5173/?worker_addr={WORKER_ADDR}
```

gdzie `WORKER_ADDR` to adres Twojej instancji serwera PersonaPlex.

**Przykład:**
```
https://localhost:5173/?worker_addr=localhost:8998
```

**Wyjaśnienie**: 
- `worker_addr` to parametr URL wskazujący bezpośrednio na serwer PersonaPlex
- Użyj tego gdy uruchamiasz własny serwer lokalnie
- Pomija system kolejkowania (jeśli jest używany)

## Struktura projektu

```
client/
├── src/                    # Kod źródłowy TypeScript/React
│   ├── app.tsx            # Główny komponent aplikacji
│   ├── audio-processor.ts # Przetwarzanie strumieni audio
│   ├── components/        # Komponenty UI
│   ├── decoder/           # Dekodery audio/tekstu
│   ├── pages/             # Strony aplikacji
│   └── protocol/          # Protokół komunikacji WebSocket
├── public/                # Pliki statyczne
├── index.html            # Główny plik HTML
├── package.json          # Zależności Node.js
├── vite.config.ts        # Konfiguracja Vite (build tool)
└── tsconfig.json         # Konfiguracja TypeScript
```

## Konfiguracja dla różnych środowisk

### Rozwój lokalny

```bash
# W pliku .env.local
VITE_QUEUE_API_PATH=/api
VITE_WORKER_ADDR=localhost:8998
```

### Produkcja

Dla produkcji, zbuduj projekt i serwuj statyczne pliki z serwera PersonaPlex:

```bash
# Zbuduj klienta
npm run build

# Serwer PersonaPlex automatycznie serwuje pliki z dist/
python -m moshi.server --static client/dist
```

## Licencja

Obecny kod jest dostarczany na licencji MIT.

---

## Dla studentów - Jak działa interfejs?

### 1. Inicjalizacja połączenia

Gdy otwierasz stronę w przeglądarce:
1. Klient żąda dostępu do mikrofonu (musisz zaakceptować)
2. Nawiązuje połączenie WebSocket z serwerem (`wss://...`)
3. Wysyła parametry konfiguracji (głos, prompt tekstowy)
4. Oczekuje na potwierdzenie (handshake)

### 2. Pętla komunikacji

Po nawiązaniu połączenia:

**Strumień wyjściowy (ty → serwer):**
```
Mikrofon → Przechwytywanie audio → Kodowanie Opus → WebSocket → Serwer
```

**Strumień wejściowy (serwer → ty):**
```
Serwer → WebSocket → Dekodowanie Opus → Odtwarzanie audio → Głośniki
```

Oba strumienie działają **jednocześnie** (full-duplex).

### 3. Komponenty kluczowe

- **audio-processor.ts**: Obsługa Web Audio API, przechwytywanie i odtwarzanie
- **protocol/**: Definicje protokołu komunikacji (formaty wiadomości)
- **decoder/**: Dekodowanie audio (Opus) i tekstu
- **components/**: Komponenty UI (przyciski, kontrolki, wizualizacje)

### 4. Eksperymentowanie

Możesz modyfikować:
- **Prompty tekstowe** w UI lub w kodzie
- **Parametry audio** (sample rate, buffer size) w `audio-processor.ts`
- **UI** - dodaj własne kontrolki, wizualizacje, efekty
- **Logowanie** - dodaj console.log() aby zobaczyć co się dzieje

**Przykład**: Dodaj licznik wypowiedzianych słów w `app.tsx`
