# Zadanie mp3 - Analiza nagrań z przesłuchań

## Opis zadania

Zadanie polega na ustaleniu nazwy ulicy, na której znajduje się konkretny instytut uczelni, gdzie wykłada profesor Andrzej Maj. Informacje potrzebne do rozwiązania zadania znajdują się w nagraniach z przesłuchań świadków.

## Wymagania

- Python 3.7 lub nowszy
- OpenAI API key i AIDevs API key (w pliku .env)

## Konfiguracja

Upewnij się, że masz plik `.env` w folderze `exrcises` z następującymi kluczami API:

```
OPENAI_API_KEY=twój_klucz_openai
AIDEVS_API_KEY=twój_klucz_aidevs
```

## Instalacja zależności

```
pip install -r requirements.txt
```

## Struktura projektu

- `transcript_audio.py` - Skrypt do transkrypcji nagrań audio za pomocą OpenAI Whisper
- `analyze_transcripts.py` - Skrypt do analizy transkrypcji i ustalenia nazwy ulicy
- `run_analysis.py` - Skrypt uruchamiający cały proces analizy

## Instrukcja użycia

### Uruchomienie całego procesu

```bash
python run_analysis.py
```

### Uruchomienie poszczególnych kroków oddzielnie

#### Transkrypcja nagrań

```bash
python transcript_audio.py
```

#### Analiza transkrypcji

```bash
python analyze_transcripts.py
```

## Wyniki

Wyniki analizy zostaną wyświetlone w konsoli oraz wysłane do API AIDevs. 