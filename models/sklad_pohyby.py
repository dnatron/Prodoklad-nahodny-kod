from datetime import datetime
from decimal import Decimal
from sqlmodel import SQLModel, Field
from typing import Optional, TYPE_CHECKING
from models.enums import TypSkladovehoPohybu, TypDokladu

if TYPE_CHECKING:
    pass
    # Tyto importy jsou pouze pro typové kontroly
    # a budou použity později při nastavení vztahů
    # from .sklad import Sklad
    # from .produkt import Produkt
    # from .firma import Firma
    # from .user import User

class SkladPohyb(SQLModel, table=True):
    """Model pro evidenci skladových pohybů (příjem, výdej)"""
    id: Optional[int] = Field(primary_key=True)
    firma_id: int = Field(foreign_key="firma.id", index=True)
    sklad_id: int = Field(foreign_key="sklad.id", index=True)
    produkt_id: int = Field(foreign_key="produkt.id", index=True)
    produkt_nazev: Optional[str] = Field(default=None, max_length=200)
    uzivatel_id: Optional[int] = Field(default=None, foreign_key="user.id")
    first_last_name: Optional[str] = Field(default=None, max_length=100)
    typ_pohybu: TypSkladovehoPohybu
    mnozstvi: Decimal = Field(default=Decimal("0.00"))
    jednotka: Optional[str] = Field(default=None, max_length=100)
    # Odkaz na doklad
    doklad_id: Optional[int] = Field(default=None, index=True)
    cislo_dokladu: Optional[str] = Field(default=None, max_length=50, index=True)
    typ_dokladu: Optional[TypDokladu] = Field(default=None)
    # Popis pohybu
    popis: Optional[str] = Field(default=None, max_length=500)
    # Stav zásob po provedení pohybu
    zustatek_mnozstvi: Decimal = Field(default=Decimal("0.00"))
    rezervovane_mnozstvi: Decimal = Field(default=Decimal("0.00"))
    dostupne_mnozstvi: Decimal = Field(default=Decimal("0.00"))
    # Časový údaj vytvoření
    vytvoreno: datetime = Field(default_factory=datetime.utcnow)