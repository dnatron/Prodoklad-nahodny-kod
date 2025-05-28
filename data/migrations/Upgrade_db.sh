#!/bin/bash
# Skript pro správu migrací databáze pomocí Alembic
# Autor: ProDoklad Team
# Datum: 2025-05-02
#
# Použití:
#   ./Upgrade_db.sh                  # Zobrazí nápovědu
#   ./Upgrade_db.sh upgrade          # Aktualizuje databázi na nejnovější verzi
#   ./Upgrade_db.sh downgrade        # Vrátí databázi o jednu verzi zpět
#   ./Upgrade_db.sh create "zpráva"  # Vytvoří novou migraci s popisem "zpráva"
#   ./Upgrade_db.sh history          # Zobrazí historii migrací
#   ./Upgrade_db.sh current          # Zobrazí aktuální verzi databáze
#   ./Upgrade_db.sh check            # Zkontroluje, zda jsou potřeba nějaké migrace

# Cesta k projektu (o dva adresáře výše)
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
echo "Projekt: $PROJECT_DIR"

# Funkce pro zobrazení nápovědy
show_help() {
    echo "Použití skriptu pro správu migrací databáze:"
    echo "  ./Upgrade_db.sh upgrade          # Aktualizuje databázi na nejnovější verzi"
    echo "  ./Upgrade_db.sh downgrade        # Vrátí databázi o jednu verzi zpět"
    echo "  ./Upgrade_db.sh create \"zpráva\"  # Vytvoří novou migraci s popisem \"zpráva\""
    echo "  ./Upgrade_db.sh history          # Zobrazí historii migrací"
    echo "  ./Upgrade_db.sh current          # Zobrazí aktuální verzi databáze"
    echo "  ./Upgrade_db.sh check            # Zkontroluje, zda jsou potřeba nějaké migrace"
}

# Kontrola, zda je Alembic nainstalován
if ! command -v alembic &> /dev/null; then
    echo "Alembic není nainstalován. Instalujte ho pomocí: pip install alembic"
    exit 1
fi

# Zpracování parametrů
case "$1" in
    upgrade)
        echo "Aktualizace databáze na nejnovější verzi..."
        cd "$PROJECT_DIR" && alembic upgrade head
        ;;
    downgrade)
        echo "Návrat databáze o jednu verzi zpět..."
        cd "$PROJECT_DIR" && alembic downgrade -1
        ;;
    create)
        if [ -z "$2" ]; then
            echo "Chybí popis migrace. Použijte: ./Upgrade_db.sh create \"popis migrace\""
            exit 1
        fi
        echo "Vytváření nové migrace: $2"
        cd "$PROJECT_DIR" && alembic revision --autogenerate -m "$2"
        ;;
    history)
        echo "Historie migrací:"
        cd "$PROJECT_DIR" && alembic history
        ;;
    current)
        echo "Aktuální verze databáze:"
        cd "$PROJECT_DIR" && alembic current
        ;;
    check)
        echo "Kontrola potřebných migrací:"
        cd "$PROJECT_DIR" && alembic check
        ;;
    *)
        show_help
        ;;
esac

exit 0