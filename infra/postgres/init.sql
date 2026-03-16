-- ByggSjekk – PostgreSQL initialiseringsskript
-- Kjøres automatisk ved første oppstart av postgres-containeren.
-- Databasen "byggsjekk" og brukeren er allerede opprettet via miljøvariabler (POSTGRES_DB / POSTGRES_USER).

-- Utvidelser som kreves av applikasjonen
CREATE EXTENSION IF NOT EXISTS "pgcrypto";    -- bcrypt-hashing, gen_random_uuid()
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";   -- uuid_generate_v4() for primærnøkler
CREATE EXTENSION IF NOT EXISTS "pg_trgm";     -- trigram-indekser for fulltekstsøk
CREATE EXTENSION IF NOT EXISTS "unaccent";    -- normalisering av norske tegn (æøå) ved søk

-- Sett standard søkebane
SET search_path TO public;

-- Rettigheter for applikasjonsbrukeren
GRANT ALL PRIVILEGES ON DATABASE byggsjekk TO byggsjekk;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO byggsjekk;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO byggsjekk;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO byggsjekk;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO byggsjekk;

-- Nyttige domener og typer (opprettes her slik at Alembic ikke trenger å håndtere dem manuelt)
-- Selve tabellstrukturen styres av Alembic-migrasjoner (apps/api/alembic/).
-- Dette skriptet sikrer kun at extensions og rettigheter er på plass ved første oppstart.

DO $$
BEGIN
    RAISE NOTICE 'ByggSjekk: PostgreSQL-utvidelser og rettigheter er konfigurert.';
END;
$$;
