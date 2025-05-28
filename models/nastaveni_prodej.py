from datetime import datetime
from sqlmodel import Field, Relationship, SQLModel
from typing import Optional
from .enums import ZpusobUhrady, Zaokrouhleni, TypCeny, SazbaDPH
from .firma import Firma

#Výchozí nastavení
class SetProdej(SQLModel, table=True):
    id: Optional[int] = Field(primary_key=True)
    firma_id: int = Field(foreign_key="firma.id", index=True)
    typ_ceny: TypCeny = Field(default=TypCeny.S_DPH)
    sazba_dph: SazbaDPH = Field(default=SazbaDPH.DPH_21)
    zaokrouhleni: Zaokrouhleni = Field(default=Zaokrouhleni.ZAOKROUHLOVAT)
    zpusob_uhrady: ZpusobUhrady = Field(default=ZpusobUhrady.PREVODEM)
    splatnost_faktur: int = Field(default=14)
    platnost_cenovych_nabidek: int = Field(default=14)
    konstantni_symbol: str = Field(default="0308", max_length=4)
    # Vzhled a tisk dokladů
    tisknout_datum_tisku: bool = Field(default=True)
    # Vydané faktury
    vydane_faktury_text_pred: str = Field(
        default="Fakturujeme Vám za dodané zboží nebo služby",
        max_length=500
    )
    vydane_faktury_text_za: str = Field(
        default="Upozorňujeme, že v případě opožděné platby faktury nám vzniká nárok na úrok z prodlení, který Vám budeme účtovat.",
        max_length=500
    )
    # Zálohové faktury
    zalohove_faktury_text_pred: str = Field(
        default="Zasíláme Vám zálohovou fakturu na objednané zboží nebo služby",
        max_length=500
    )
    zalohove_faktury_text_za: str = Field(
        default="Zboží pošleme po přijetí platby. Odeslání proběhne v co nejkratším čase.",
        max_length=500
    )
    # Dodací listy
    tisk_ceny_v_dodacim_listu: bool = Field(default=True)
    # relationships
    firma: Firma = Relationship(back_populates="set_prodej")

# Číselné řady - base
class BaseCislovani(SQLModel):
    format_cisla: str = Field(default="Z", max_length=20)
    rok: int = Field(default=datetime.now().year)
    nazev_rady: str = Field(default="Výchozí", max_length=50)
    poradove_cislo: int = Field(default=0)

# Faktura vydaná - Číselné řady
class SetFakturaVydana(BaseCislovani, table=True):
    id: Optional[int] = Field(primary_key=True)
    firma_id: int = Field(foreign_key="firma.id", index=True)
    # relationships
    firma: Firma = Relationship(back_populates="set_faktury_vydane")

# Dobropis - Číselné řady
class SetDobropis(BaseCislovani, table=True):
    id: Optional[int] = Field(primary_key=True)
    firma_id: int = Field(foreign_key="firma.id", index=True)
    # relationships
    firma: Firma = Relationship(back_populates="set_dobropis")

# Zálohová faktura - Číselné řady
class SetFakturaZalohova(BaseCislovani, table=True):
    id: Optional[int] = Field(primary_key=True)
    firma_id: int = Field(foreign_key="firma.id", index=True)
    # relationships
    firma: Firma = Relationship(back_populates="set_faktury_zalohove")

# Daňový doklad k přijaté platbě - Číselné řady
class SetDokladPrijataPlatba(BaseCislovani, table=True):
    id: Optional[int] = Field(primary_key=True)
    firma_id: int = Field(foreign_key="firma.id", index=True)
    # relationships
    firma: Firma = Relationship(back_populates="set_doklady_prijate_platby")

# Cenová nabídka - Číselné řady
class SetCenoveNabidka(BaseCislovani, table=True):
    id: Optional[int] = Field(primary_key=True)
    firma_id: int = Field(foreign_key="firma.id", index=True)
    # relationships
    firma: Firma = Relationship(back_populates="set_cenove_nabidky")

# Prodejka - Číselné řady
class SetProdejka(BaseCislovani, table=True):
    id: Optional[int] = Field(primary_key=True)
    firma_id: int = Field(foreign_key="firma.id", index=True)
    # relationships
    firma: Firma = Relationship(back_populates="set_prodejky")

# Interní doklad - Číselné řady
class SetInterniDoklad(BaseCislovani, table=True):
    id: Optional[int] = Field(primary_key=True)
    firma_id: int = Field(foreign_key="firma.id", index=True)
    # relationships
    firma: Firma = Relationship(back_populates="set_interni_doklady")