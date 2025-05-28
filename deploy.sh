#!/bin/bash
# Skript pro nasazení aplikace ProDoklad
#
# Před spuštěním skriptu je třeba nastavit práva:
# chmod +x deploy.sh
#
# Pokud nahrajeme soubor deploy.sh sami tak použijeme abyho git nechtěl aktualizovat:
# cd /home/docker/ProDoklad
# git checkout -- deploy.sh
# ./deploy.sh
#
# Nastavení e-mailu:
# git config --global user.email "fxtc@fxtc.cz"
# git config --global user.name ".:FXTC:."
#
# Nastavení ukládání přihlašovacích údajů:
# git config --global credential.helper store
#
# Při prvním použití git pull nebo git clone budete vyzváni k zadání přihlašovacích údajů,
# které budou poté uloženy pro budoucí použití
#
# Použití:
# ./deploy.sh              # Standardní nasazení
# ./deploy.sh --no-pull    # Nasazení bez stažení změn z Gitu
# ./deploy.sh --no-build   # Nasazení bez přestavění Docker obrazu
# ./deploy.sh --rebuild-db     # Přestaví databázi (smaže existující a vytvoří novou)

# Nastavení proměnných
APP_DIR="/home/docker/ProDoklad"
LOG_FILE="$APP_DIR/deploy.log"
GIT_REPO="https://github.com/dnatron/ProDoklad.git"
CONTAINER_NAME="prodoklad_app_1"
DOCKER_COMPOSE_FILE="docker-compose.prod.yml"

# Zpracování parametrů
NO_PULL=false
NO_BUILD=false
REBUILD_DB=false

for arg in "$@"; do
    case $arg in
        --no-pull)
            NO_PULL=true
            ;;
        --no-build)
            NO_BUILD=true
            ;;
        --rebuild-db)
            REBUILD_DB=true
            ;;
    esac
done

# Funkce pro logování
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

# Vytvoření adresáře pro aplikaci, pokud neexistuje
mkdir -p "$APP_DIR"
mkdir -p "$APP_DIR/data"
chmod -R 777 "$APP_DIR/data"  # Zajistíme plná oprávnění pro adresář data

# Přejdeme do adresáře aplikace
cd "$APP_DIR" || { log "Nelze přejít do adresáře $APP_DIR"; exit 1; }

# Stažení změn z Gitu
if [ "$NO_PULL" = "false" ]; then
    log "Stahuji změny z Gitu"
    if [ -d ".git" ]; then
        git pull || { log "Chyba při stahování změn z Gitu"; exit 1; }
    else
        git clone "$GIT_REPO" . || { log "Chyba při klonování repozitáře"; exit 1; }
    fi
fi

# Záloha databáze před nasazením
if [ -f "$APP_DIR/data/app.db" ]; then
    BACKUP_FILE="$APP_DIR/data/app.db.backup-$(date '+%Y%m%d%H%M%S')"
    log "Vytvářím zálohu databáze: $BACKUP_FILE"
    cp "$APP_DIR/data/app.db" "$BACKUP_FILE" || { log "Chyba při vytváření zálohy databáze"; }
    
    # Ponecháme pouze 5 nejnovějších záloh
    ls -t "$APP_DIR/data/app.db.backup-"* | tail -n +6 | xargs -r rm
    log "Staré zálohy byly odstraněny"
fi

# Pokud je požadováno přestavění databáze, smažeme existující
if [ "$REBUILD_DB" = "true" ] && [ -f "$APP_DIR/data/app.db" ]; then
    log "Mažu existující databázi"
    rm "$APP_DIR/data/app.db" || { log "Chyba při mazání databáze"; }
fi

# Zastavení běžících kontejnerů
log "Zastavuji běžící kontejnery"
docker-compose -f "$DOCKER_COMPOSE_FILE" down || { log "Chyba při zastavování kontejnerů"; }

# Sestavení a spuštění Docker kontejnerů
if [ "$NO_BUILD" = "false" ]; then
    log "Sestavuji Docker obraz"
    docker-compose -f "$DOCKER_COMPOSE_FILE" build || { log "Chyba při sestavování Docker obrazu"; exit 1; }
fi

log "Spouštím Docker kontejnery"
docker-compose -f "$DOCKER_COMPOSE_FILE" up -d || { log "Chyba při spouštění Docker kontejnerů"; exit 1; }

# Spuštění Alembic migrací
log "Spouštím databázové migrace"
sleep 3  # Počkáme, až se kontejner spustí
docker exec $CONTAINER_NAME bash -c "cd /app && ./data/migrations/Upgrade_db.sh upgrade" || { log "Chyba při spouštění migrací"; }

# Inicializace databáze, pokud je potřeba
if [ "$REBUILD_DB" = "true" ] || [ ! -f "$APP_DIR/data/app.db.backup-"* ]; then
    log "Inicializuji databázi s testovacími daty"
    sleep 5  # Počkáme, až se aplikace spustí a vytvoří základní strukturu databáze
    docker exec $CONTAINER_NAME python /app/data/init_db.py || { log "Chyba při inicializaci databáze"; }
fi

# Kontrola stavu aplikace
log "Kontroluji stav aplikace"
sleep 5  # Počkáme 5 sekund, aby se aplikace stihla nastartovat
curl -s http://localhost:8002 > /dev/null && log "Aplikace je dostupná na http://localhost:8002" || log "Aplikace není dostupná"

log "Nasazení dokončeno"
exit 0