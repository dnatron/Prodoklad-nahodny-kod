from datetime import datetime
from typing import List, Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship
from models.enums import UserRole
import bcrypt

if TYPE_CHECKING:
    from .firma import Firma
    # Dočasně zakomentovaný import, který budeme potřebovat později
    # from .sklad_pohyby import SkladPohyb

class BaseUser(SQLModel):
    email: str = Field(index=True)
    hashed_password: str = Field(min_length=8, max_length=255)
    first_name: str = Field(default="", max_length=50)
    last_name: str = Field(default="", max_length=50)
    bio: str = Field(default="", max_length=500)
    is_active: bool = Field(default=True)
    phone: str = Field(default="", max_length=20)
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow, sa_column_kwargs={"onupdate": datetime.utcnow})

    def verify_password(self, password: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode(), self.hashed_password.encode())


class User(BaseUser, table=True):
    id: Optional[int] = Field(primary_key=True)
    role: UserRole = Field(default=UserRole.USER)
    
    # Relationships
    firmy: List["Firma"] = Relationship(back_populates="owner", sa_relationship_kwargs={"foreign_keys": "[Firma.user_id]"})
    # sklad_pohyby: List["SkladPohyb"] = Relationship(back_populates="uzivatel")


class BaseSubUser(BaseUser):
    # Kontakty
    kontakty: bool = Field(default=True)
    # Prodej
    prodej_faktury_vydane: bool = Field(default=True)
    prodej_faktury_zalohove: bool = Field(default=True)
    prodej_danove_doklady_k_platbe: bool = Field(default=True)
    prodej_dobropisy: bool = Field(default=True)
    prodej_cenove_nabidky: bool = Field(default=True)
    prodej_prodejky: bool = Field(default=True)
    prodej_zauctovani_prodejek: bool = Field(default=True)
    prodej_sablony: bool = Field(default=True)
    prodej_pravidelne_faktury: bool = Field(default=True)
    prodej_uhrady: bool = Field(default=True)
    prodej_prehled_prodeje: bool = Field(default=False)
    # Nakup
    nakup_faktury_prijate: bool = Field(default=False)
    nakup_uctenky: bool = Field(default=False)
    nakup_uhrady: bool = Field(default=False)
    # Sklad/Cenik
    produkty_cenik: bool = Field(default=True)
    skladove_pohyby: bool = Field(default=True)
    sklady: bool = Field(default=True)
    # Finance
    banka: bool = Field(default=False)
    pokladna: bool = Field(default=False)
    dan_z_prijmu: bool = Field(default=False)
    # Nastaveni
    nastavni_predplatne: bool = Field(default=False)
    nastavni_firma: bool = Field(default=False)
    nastavni_prodej: bool = Field(default=False)
    nastavni_nakup: bool = Field(default=False)
    nastavni_komunikace: bool = Field(default=False)
    nastavni_banka: bool = Field(default=False)
    nastavni_pokladna: bool = Field(default=False)
    nastavni_aplikace: bool = Field(default=False)
    nastavni_uzivatel: bool = Field(default=False)


class SubUser(BaseSubUser, table=True):
    id: Optional[int] = Field(primary_key=True)
    firma_id: int | None = Field(default=None, foreign_key="firma.id", index=True)

    # Relationships
    firma: "Firma" = Relationship(back_populates="subusers")