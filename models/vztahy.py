"""
Tento modul obsahuje funkce pro nastavení vztahů mezi modely.
Pomáhá vyřešit problém s kruhovými závislostmi tím, že vztahy jsou 
nastaveny až po definici všech modelů.
"""
from sqlmodel import Relationship

def nastav_vztahy():
    """
    Nastaví vztahy mezi modely poté, co jsou všechny modely definovány.
    Tím řeší problémy s kruhovými závislostmi.
    """
    # Import modelů - tady jsou již všechny modely definované
    from .firma import Firma
    from .sklad import Sklad
    from .produkt import Produkt
    from .user import User
    from .sklad_pohyby import SkladPohyb
    
    # Nastavení vztahů pro model Firma
    Firma.sklad_pohyby = Relationship(
        sa_relationship_kwargs={
            "lazy": "selectin", 
            "cascade": "all, delete-orphan"  # Při smazání firmy se smažou i pohyby
        }, 
        back_populates="firma"
    )
    
    # Nastavení vztahů pro model Sklad
    Sklad.sklad_pohyby = Relationship(
        sa_relationship_kwargs={
            "lazy": "selectin",
            "foreign_keys": "[SkladPohyb.sklad_id]",
            # Zakázat smazání skladu, pokud obsahuje pohyby
            "passive_deletes": "all"
        }, 
        back_populates="sklad"
    )
    
    # Nastavení vztahů pro model Produkt
    Produkt.sklad_pohyby = Relationship(
        sa_relationship_kwargs={
            "lazy": "selectin",
            # Zakázat smazání produktu, pokud má skladové pohyby
            "passive_deletes": "all"
        }, 
        back_populates="produkt"
    )
    
    # Nastavení vztahů pro model User
    User.sklad_pohyby = Relationship(
        sa_relationship_kwargs={
            "lazy": "selectin",
            # Při smazání uživatele se pouze zruší vazba (nastaví na NULL)
            "passive_deletes": False
        }, 
        back_populates="uzivatel"
    )
    
    # Nastavení vztahů pro model SkladPohyb
    SkladPohyb.firma = Relationship(
        back_populates="sklad_pohyby",
        sa_relationship_kwargs={"cascade": "save-update"}
    )
    
    SkladPohyb.sklad = Relationship(
        back_populates="sklad_pohyby",
        sa_relationship_kwargs={
            "foreign_keys": "[SkladPohyb.sklad_id]",
            "cascade": "save-update"
        }
    )
    
    SkladPohyb.produkt = Relationship(
        back_populates="sklad_pohyby",
        sa_relationship_kwargs={"cascade": "save-update"}
    )
    
    SkladPohyb.uzivatel = Relationship(
        back_populates="sklad_pohyby",
        sa_relationship_kwargs={"cascade": "save-update"}
    )
