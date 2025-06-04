# Connections Task - Lesson 15

## Opis zadania

Zadanie polega na znalezieniu najkrótszej ścieżki między użytkownikami "Rafał" i "Barbara" w grafie połączeń społecznych.

## Kroki rozwiązania

1. **Pobieranie danych z MySQL** - Skrypt pobiera dane użytkowników i połączeń z bazy MySQL przez API
2. **Zapisywanie lokalnie** - Dane są zapisywane lokalnie w plikach JSON dla przyszłego użycia
3. **Ładowanie do Neo4j** - Dane są ładowane do bazy grafowej Neo4j
4. **Znajdowanie ścieżki** - Używa algorytmu najkrótszej ścieżki w Neo4j
5. **Wysyłanie odpowiedzi** - Wynik jest wysyłany do centrali

## Wymagania

### Instalacja Neo4j

#### Opcja 1: Neo4j Desktop (Zalecane)
1. Pobierz Neo4j Desktop z https://neo4j.com/download/
2. Zainstaluj i uruchom
3. Utwórz nowy projekt i bazę danych
4. Ustaw hasło (domyślnie: `neo4j`)
5. Uruchom bazę danych

#### Opcja 2: Neo4j Community Server
1. Pobierz Neo4j Community Server
2. Rozpakuj i uruchom: `./bin/neo4j start`
3. Otwórz http://localhost:7474
4. Zaloguj się (domyślnie: `neo4j`/`neo4j`)
5. Zmień hasło

#### Opcja 3: Docker
```bash
docker run \
    --name neo4j \
    -p7474:7474 -p7687:7687 \
    -d \
    -v $HOME/neo4j/data:/data \
    -v $HOME/neo4j/logs:/logs \
    -v $HOME/neo4j/import:/var/lib/neo4j/import \
    -v $HOME/neo4j/plugins:/plugins \
    --env NEO4J_AUTH=neo4j/password \
    neo4j:latest
```

### Instalacja zależności Python

```bash
cd exrcises/lesson15
pip install -r requirements.txt
```

## Konfiguracja

### Zmienne środowiskowe

Upewnij się, że plik `.env` w katalogu `exrcises` zawiera:

```env
OPENAI_API_KEY=your_openai_api_key
CENTRALA_API_KEY=your_centrala_api_key

# Neo4j (opcjonalne, domyślne wartości)
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=neo4j
```

## Uruchomienie

```bash
cd exrcises/lesson15
python connections_task.py
```

## Jak działa skrypt

1. **Połączenie z Neo4j** - Sprawdza połączenie z bazą grafową
2. **Ładowanie danych** - Próbuje załadować dane z lokalnych plików JSON
3. **Pobieranie z MySQL** - Jeśli brak lokalnych danych, pobiera z API:
   - `SELECT id, username FROM users`
   - `SELECT user1_id, user2_id FROM connections`
4. **Zapisywanie lokalnie** - Zapisuje dane do `users_data.json` i `connections_data.json`
5. **Ładowanie do Neo4j**:
   - Tworzy węzły `User` z atrybutami `userId` i `username`
   - Tworzy relacje `KNOWS` między użytkownikami
6. **Znajdowanie ścieżki** - Używa Cypher query:
   ```cypher
   MATCH (start:User {username: 'Rafał'}), (end:User {username: 'Barbara'})
   MATCH path = shortestPath((start)-[:KNOWS*]-(end))
   RETURN [node in nodes(path) | node.username] as path_names
   ```
7. **Wysyłanie odpowiedzi** - Formatuje wynik jako string oddzielony przecinkami

## Struktura plików

```
lesson15/
├── connections_task.py     # Główny skrypt
├── requirements.txt        # Zależności Python
├── README.md              # Ten plik
├── users_data.json        # Cache danych użytkowników (generowany)
└── connections_data.json  # Cache danych połączeń (generowany)
```

## Rozwiązywanie problemów

### Neo4j nie uruchamia się
- Sprawdź czy port 7687 nie jest zajęty
- Upewnij się, że Java jest zainstalowana
- Sprawdź logi Neo4j

### Błąd połączenia z Neo4j
- Sprawdź czy Neo4j jest uruchomiony
- Zweryfikuj dane logowania w `.env`
- Sprawdź URI połączenia

### Błąd API MySQL
- Sprawdź klucz API w `.env`
- Zweryfikuj połączenie internetowe
- Sprawdź czy API centrali jest dostępne

## Przykładowy wynik

```
=== ROZPOCZYNAM ROZWIĄZYWANIE ZADANIA CONNECTIONS ===
✅ Połączono z Neo4j
✅ Załadowano 50 użytkowników i 100 połączeń z plików lokalnych
✅ Baza Neo4j wyczyszczona
✅ Załadowano 50 użytkowników do Neo4j
✅ Załadowano 100 połączeń do Neo4j
Znalezieni użytkownicy podobni do 'Rafał': ['Rafał']
Znalezieni użytkownicy podobni do 'Barbara': ['Barbara']
Szukam ścieżki między: Rafał -> Barbara
✅ Znaleziona najkrótsza ścieżka: Rafał -> Andrzej -> Stefania -> Barbara
✅ Zadanie zakończone pomyślnie! 