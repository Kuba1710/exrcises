# Speed Challenge - Lesson 23

## Opis zadania

To zadanie polega na wykonaniu sekwencji operacji API w czasie **maksymalnie 6 sekund**:

1. Wysłanie hasła `NONOMNISMORIAR` do API
2. Otrzymanie HASH i wysłanie go z powrotem
3. Otrzymanie dwóch URLs z zadaniami 
4. Równoległe pobranie danych z obu URLs
5. Przetworzenie zadań za pomocą LLM
6. Wysłanie scalonej odpowiedzi

## Pliki

- `speed_challenge.py` - podstawowa wersja z pełnym logowaniem
- `ultra_speed_challenge.py` - zoptymalizowana wersja na maksymalną prędkość
- `requirements.txt` - wymagane biblioteki

## Instalacja

```bash
cd exrcises/lesson23
pip install -r requirements.txt
```

## Konfiguracja

Ustaw zmienną środowiskową z kluczem OpenAI:

```bash
# Windows PowerShell
$env:OPENAI_API_KEY="sk-your-api-key-here"

# Linux/Mac
export OPENAI_API_KEY="sk-your-api-key-here"
```

## Uruchomienie

### Wersja podstawowa:
```bash
python speed_challenge.py
```

### Wersja ultra-szybka (zalecana):
```bash
python ultra_speed_challenge.py
```

## Optymalizacje zastosowane

1. **Asynchroniczne wywołania API** - wszystkie operacje sieciowe są nieblokujące
2. **Równoległe pobieranie danych** - oba URLs są pobierane jednocześnie
3. **Równoległe przetwarzanie LLM** - oba zadania są przetwarzane jednocześnie
4. **Minimalne prompty** - tylko najważniejsze informacje dla LLM
5. **Szybki model** - gpt-3.5-turbo zamiast gpt-4
6. **Krótkie odpowiedzi** - max_tokens=30 dla szybkości
7. **Agresywne timeouty** - maksymalnie 5s per operację
8. **Prosta struktura odpowiedzi** - tablica zamiast skomplikowanych obiektów

## Oczekiwane czasy wykonania

- Pobieranie danych: ~4-6 sekund (według opisu zadania)
- Przetwarzanie LLM: ~0.5-1 sekunda  
- Wysłanie odpowiedzi: ~0.2-0.5 sekundy
- **Całość: ~5-7 sekund** (granica to 6 sekund)

## Troubleshooting

Jeśli skrypt przekracza limit czasowy:
1. Sprawdź połączenie internetowe
2. Upewnij się, że klucz OpenAI API jest poprawny
3. Spróbuj uruchomić kilka razy (API może mieć różne opóźnienia)
4. Rozważ użycie szybszego dostawcy LLM (Groq, Claude) 