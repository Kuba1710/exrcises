# Zadanie Webhook - Dron na mapie 4x4

## Opis zadania

Webhook server dla zadania z dronem, który:
1. Odbiera instrukcje ruchu drona w formacie JSON
2. Analizuje instrukcję używając OpenAI GPT-4
3. Oblicza końcową pozycję drona na mapie 4x4
4. Zwraca opis tego co znajduje się na danej pozycji

## Mapa 4x4

```
[znacznik]  [pień drzewa]  [drzewo]    [dom]
[trawa]     [wiatrak]      [trawa]     [trawa]  
[trawa]     [trawa]        [skały]     [drzewo]
[góry]      [góry]         [samochód]  [jaskinia]
```

Dron zawsze startuje z pozycji (0, 0) - lewy górny róg.

## Instalacja

1. Zainstaluj zależności:
```bash
pip install -r requirements.txt
```

2. Utwórz plik `.env` z kluczem OpenAI:
```
OPENAI_API_KEY=your_openai_api_key
PERSONAL_API_KEY=your_personal_api_key_for_centrala
```

## Uruchomienie

### Krok 1: Uruchom serwer lokalnie
```bash
python webhook_server.py
```

Serwer będzie dostępny na http://localhost:5000

### Krok 2: Przetestuj lokalnie
```bash
python test_webhook.py
```

### Krok 3: Wystaw na świat (ngrok)
```bash
# Zainstaluj ngrok jeśli nie masz
# Windows: choco install ngrok
# lub pobierz z https://ngrok.com/

ngrok http 5000
```

Skopiuj HTTPS URL z ngrok (np. https://abc123.ngrok.io)

### Krok 4: Zgłoś URL do Centrali
```bash
python report_webhook.py
```

Podaj pełny URL z endpoint: `https://abc123.ngrok.io/webhook`

## Testowanie

### Endpoint testowy
```bash
curl http://localhost:5000/test
```

### Przykładowe żądanie webhook
```bash
curl -X POST http://localhost:5000/webhook \
  -H "Content-Type: application/json" \
  -d '{"instruction": "poleciałem jedno pole w prawo"}'
```

Oczekiwana odpowiedź:
```json
{"description": "pień drzewa"}
```

## Struktura plików

- `webhook_server.py` - główny serwer Flask z API
- `test_webhook.py` - skrypt do testowania lokalnego
- `report_webhook.py` - skrypt do zgłaszania URL do Centrali
- `requirements.txt` - zależności Python
- `README.md` - ta instrukcja

## Rozwiązywanie problemów

1. **Błąd "description field missing"** - Sprawdź czy zwracasz JSON z kluczem "description"
2. **Timeout 15s** - Upewnij się że LLM odpowiada szybko, może użyj gpt-3.5-turbo
3. **Błędne pozycje** - Sprawdź logikę ruchu w prompts dla LLM
4. **ngrok nie działa** - Sprawdź czy serwer Flask działa na porcie 5000

## Logika ruchu

- Prawo: zwiększ kolumnę (y)  
- Lewo: zmniejsz kolumnę (y)
- Dół: zwiększ wiersz (x)
- Góra: zmniejsz wiersz (x)

Pozycje są ograniczone do 0-3 w obu wymiarach. 