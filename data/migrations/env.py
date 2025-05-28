from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

import os
import sys

# Přidání kořenového adresáře projektu do Python cesty
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Import modelů a nastavení vztahů
from database import SQLModel

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Dynamické nastavení URL k databázi
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
db_path = os.path.join(project_root, "data", "app.db")
config.set_main_option("sqlalchemy.url", f"sqlite:///{db_path}")

# Explicitní import modelů - tyto importy jsou potřebné pro Alembic,
# aby mohl detekovat modely a jejich změny pro generování migrací,
# i když je přímo nepoužíváme v tomto souboru
from models.firma import Firma  # noqa
from models.user import User, SubUser  # noqa
from models.kontakt import Kontakt  # noqa
from models.produkt import Produkt  # noqa
from models.faktura import (  # noqa
    FakturaVydana, FakturaZalohova, FakturaPrijata,
    Dobropis, FakturaPolozka
)
from models.nastaveni_prodej import (  # noqa
    SetProdej, SetFakturaVydana, SetDobropis, SetFakturaZalohova,
    SetDokladPrijataPlatba, SetCenoveNabidka, SetProdejka, SetInterniDoklad
)
from models.nastaveni_nakup import SetNakup, SetNakupFakturaPrijata, SetNakupUctenka  # noqa
from models.nastaveni_banka import SetBanka, SetBankaCislovani, SetBankaParovani  # noqa
from models.nastaveni_pokladna import SetPokladna, SetTerminal, SetPokladnaCislovani  # noqa
from models.nastaveni_email import SetEmail  # noqa
from models.sklad import Sklad  # noqa
from models.sklad_pohyby import SkladPohyb  # noqa
from models.enums import (  # noqa
    UserRole, SazbaDPH, TypCeny,
    ZpusobOdeslaniEmailu, OdeslatEmailPres,
    ZpusobUhrady, Zaokrouhleni, Mena,
    ZpusobUhradyNakup, TypProdeje, TypPlatce, TypSubjektu
)

try:
    from models.vztahy import nastav_vztahy
    # Nastavení vztahů mezi modely
    nastav_vztahy()
except ImportError:
    print("WARNING: models.vztahy modul nebyl nalezen, vztahy mezi modely nebudou nastaveny")

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = SQLModel.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
