from datetime import datetime
from decimal import Decimal
import sys
from pathlib import Path
import os

# Přidání nadřazeného adresáře do sys.path, aby bylo možné importovat moduly z kořenového adresáře projektu
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlmodel import Session, SQLModel, create_engine

from models.nastaveni_prodej import (
    SetProdej, SetFakturaVydana, SetDobropis, SetFakturaZalohova,
    SetDokladPrijataPlatba, SetCenoveNabidka, SetProdejka,
    SetInterniDoklad
)
from models.kontakt import Kontakt, KontaktAdresa
from models.produkt import Produkt
from models.firma import Firma
from models.user import User, UserRole, SubUser
from models.sklad import Sklad
from models.sklad_pohyby import SkladPohyb, TypSkladovehoPohybu, TypDokladu  # Potřebné pro inicializaci modelu
from models.nastaveni_pokladna import SetPokladna, SetTerminal, SetPokladnaCislovani, TypProdeje
from models.enums import (
    Mena, TypPlatce, TypSubjektu, SazbaDPH, TypCeny,
    ZpusobUhrady, Zaokrouhleni, Zeme  # Přidáno Zeme
)
from models.nastaveni_banka import SetBanka, SetBankaCislovani
from models.nastaveni_email import (
    SetEmail, ZpusobOdeslaniEmailu, OdeslatEmailPres
)
from models.nastaveni_nakup import (
    SetNakup, ZpusobUhradyNakup,
    SetNakupFakturaPrijata, SetNakupUctenka
)

# Importujeme funkci pro nastavení vztahů
from models.vztahy import nastav_vztahy

# Database URL - použijeme stejnou cestu jako v hlavní aplikaci
data_dir = os.path.dirname(os.path.abspath(__file__))
DATABASE_URL = f"sqlite:///{data_dir}/app.db"
print(f"Inicializace databáze: {DATABASE_URL}")


def init_db(db_url: str = DATABASE_URL):
    engine = create_engine(db_url, echo=True)
    
    # Zajistěte, aby byl Skladpohyb správně inicializován jeho enum
    test_enum = TypSkladovehoPohybu.PRIJEM
    test_model = SkladPohyb.__name__
    print(f"Inicializace modelu {test_model} s výčtem {test_enum}")
    
    # Nastavíme vztahy mezi modely (řeší kruhové závislosti)
    nastav_vztahy()
    SQLModel.metadata.drop_all(engine)  # Drop all tables first
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        # Create admin user
        admin = User(
            email="fxtc@post.cz",
            # password: admin
            hashed_password="$4b$12$zB95A56X3SOQSenxDvzk.eibNAjWZPAoX11bM1XxphpmRXAdGODxO",
            first_name="Admin",
            last_name="User",
            bio="System Administrator",
            role=UserRole.ADMIN,
            is_active=True,
            phone="+420777888999"
        )
        session.add(admin)
        session.commit()

        # Create first regular user 1(owner of FXTC Company)
        user = User(
            email="selmi@centrum.cz",
            # password: admin
            hashed_password="$4b$12$zB95A56X3SOQSenxDvzk.eibNAjWZPAoX11bM1XxphpmRXAdGODxO",
            first_name="Karel",
            last_name="Kura",
            bio="Regular User",
            role=UserRole.USER,
            is_active=True,
            phone="+420666555444"
        )
        session.add(user)
        session.commit()

        # Create initial firma 1 owned by first regular user 1
        firma1 = Firma(
            user_id=user.id,
            legislativa=Zeme.CZ,
            firma="FXTC Company",
            ic="12345678",
            dic="CZ12345678",
            ulice="Hlavní 123",
            psc="11000",
            mesto="Praha",
            telefon="+420123456789",
            mobil="",
            email="info@fxtc.cz",
            web="https://www.fxtc.cz",
            typ_platce=TypPlatce.PLATCE_DPH,
            typ_subjektu=TypSubjektu.FO,
            spisova_znacka="",
            logo="",
            podpis="test popis"
        )
        session.add(firma1)
        session.commit()

        # Create SetProdej for firma 1
        set_prodej = SetProdej(
            firma_id=firma1.id,
            typ_ceny=TypCeny.S_DPH,
            sazba_dph=SazbaDPH.DPH_21,
            zaokrouhleni=Zaokrouhleni.ZAOKROUHLOVAT,
            zpusob_uhrady=ZpusobUhrady.PREVODEM,
            splatnost_faktur=14,
            platnost_cenovych_nabidek=30,
            konstantni_symbol="0308",
            tisknout_datum_tisku=True,
            tisk_ceny_v_dodacim_listu=True,
            vydane_faktury_text_pred="Fakturujeme Vám za dodané zboží nebo služby",
            vydane_faktury_text_za="Děkujeme za Vaši důvěru. V případě dotazů nás neváhejte kontaktovat.",
            zalohove_faktury_text_pred="Zasíláme Vám zálohovou fakturu na objednané zboží nebo služby",
            zalohove_faktury_text_za="Po přijetí platby Vám zboží odešleme v co nejkratším termínu."
        )
        session.add(set_prodej)
        session.commit()

        # Create second firma 2 owned by first regular user 1
        firma2 = Firma(
            user_id=user.id,
            legislativa=Zeme.CZ,
            firma="FXTC Company 2",
            ic="87654321",
            dic="CZ87654321",
            ulice="Vedlejší 456",
            psc="11000",
            mesto="Praha",
            telefon="+420987654321",
            mobil="",
            email="karel@company.cz",
            web="https://www.karel-company.cz",
            typ_platce=TypPlatce.NEPLATCE_DPH,
            typ_subjektu=TypSubjektu.PO,
            spisova_znacka="",
            logo="",
            podpis="Karel's signature"
        )
        session.add(firma2)
        session.commit()

        # Create SetProdej for firma 2
        set_prodej2 = SetProdej(
            firma_id=firma2.id,
            typ_ceny=TypCeny.BEZ_DPH,
            sazba_dph=SazbaDPH.DPH_12,
            zaokrouhleni=Zaokrouhleni.ZAOKROUHLOVAT,
            zpusob_uhrady=ZpusobUhrady.KARTOU,
            splatnost_faktur=30,
            platnost_cenovych_nabidek=14,
            konstantni_symbol="0308",
            tisknout_datum_tisku=False,
            tisk_ceny_v_dodacim_listu=False,
            vydane_faktury_text_pred="Fakturujeme Vám následující položky",
            vydane_faktury_text_za="Děkujeme za spolupráci",
            zalohove_faktury_text_pred="Zálohová faktura na objednané zboží",
            zalohove_faktury_text_za="Děkujeme za platbu předem"
        )
        session.add(set_prodej2)
        session.commit()

        # Create second regular user 2
        user2 = User(
            email="selmi2@centrum.cz",
            # password: admin
            hashed_password="$4b$12$zB95A56X3SOQSenxDvzk.eibNAjWZPAoX11bM1XxphpmRXAdGODxO",
            first_name="KarelDva",
            last_name="KuraDva",
            bio="Regular User2",
            role=UserRole.USER,
            is_active=True,
            phone="+420666555442"
        )
        session.add(user2)
        session.commit()

        # Create third firma 3 owned by second regular user 2
        firma3 = Firma(
            user_id=user2.id,
            legislativa=Zeme.CZ,
            firma="FX Firma 3 Company",
            ic="12345673",
            dic="CZ87654323",  # Changed DIC to be unique
            ulice="Hlavní 123",
            psc="11002",
            mesto="Praha Firma 3",
            email="Firma3@fxtc.cz",
            telefon="+420123456782",
            mobil="",
            web="https://www.Firma3.cz",
            typ_platce=TypPlatce.NEPLATCE_DPH,
            typ_subjektu=TypSubjektu.FO,
            spisova_znacka="",
            logo="",
            podpis=""
        )
        session.add(firma3)
        session.commit()

        # Create SetProdej for firma 3
        set_prodej3 = SetProdej(
            firma_id=firma3.id,
            typ_ceny=TypCeny.BEZ_DPH,
            sazba_dph=SazbaDPH.DPH_0,
            zaokrouhleni=Zaokrouhleni.NEZAOKROUHLOVAT,
            zpusob_uhrady=ZpusobUhrady.HOTOVE,
            splatnost_faktur=7,
            platnost_cenovych_nabidek=7,
            konstantni_symbol="0308",
            tisknout_datum_tisku=True,
            tisk_ceny_v_dodacim_listu=True,
            vydane_faktury_text_pred="Děkujeme za Vaši objednávku. Fakturujeme Vám:",
            vydane_faktury_text_za="Těšíme se na další spolupráci!",
            zalohove_faktury_text_pred="Zálohová faktura k objednávce",
            zalohove_faktury_text_za="Po obdržení platby Vám bude vystavena faktura."
        )
        session.add(set_prodej3)
        session.commit()

        # Create bank settings for all firms
        bank_settings_data = [
            # Firma 1 bank accounts
            {
                "firma": firma1,
                "accounts": [
                    {
                        "nazev_uctu": "Hlavní účet CZK",
                        "mena": Mena.CZK,
                        "cislo_uctu": "123456789",
                        "iban": "CZ6200010000000123456789",
                        "swift": "FIOBCZPPXXX",
                        "kod_banky": "0800",  # Česká spořitelna
                        "vychozi_ucet": True
                    },
                    {
                        "nazev_uctu": "EUR účet",
                        "mena": Mena.EUR,
                        "cislo_uctu": "987654321",
                        "iban": "CZ6200010000000123456789",
                        "swift": "FIOBCZPPXXX",
                        "kod_banky": "0300",  # ČSOB
                        "vychozi_ucet": False
                    }
                ]
            },
            # Firma 2 bank accounts
            {
                "firma": firma2,
                "accounts": [
                    {
                        "nazev_uctu": "Podnikatelský účet",
                        "mena": Mena.CZK,
                        "cislo_uctu": "111222333",
                        "iban": "CZ6200010000000123456789",
                        "swift": "FIOBCZPPXXX",
                        "kod_banky": "0100",  # Komerční banka
                        "vychozi_ucet": True
                    },
                    {
                        "nazev_uctu": "USD Account",
                        "mena": Mena.USD,
                        "cislo_uctu": "444555666",
                        "iban": "CZ6200010000000123456789",
                        "swift": "FIOBCZPPXXX",
                        "kod_banky": "0300",  # ČSOB
                        "vychozi_ucet": False
                    }
                ]
            },
            # Firma 3 bank accounts
            {
                "firma": firma3,
                "accounts": [
                    {
                        "nazev_uctu": "Běžný účet CZK",
                        "mena": Mena.CZK,
                        "cislo_uctu": "777888999",
                        "iban": "CZ6200010000000123456789",
                        "swift": "FIOBCZPPXXX",
                        "kod_banky": "2010",  # Fio banka
                        "vychozi_ucet": True
                    },
                    {
                        "nazev_uctu": "Eurový účet",
                        "mena": Mena.EUR,
                        "cislo_uctu": "123987456",
                        "iban": "CZ6200010000000123456789",
                        "swift": "FIOBCZPPXXX",
                        "kod_banky": "2010",  # Fio banka
                        "vychozi_ucet": False
                    },
                    {
                        "nazev_uctu": "USD Account",
                        "mena": Mena.USD,
                        "cislo_uctu": "456789123",
                        "iban": "CZ6200010000000123456789",
                        "swift": "FIOBCZPPXXX",
                        "kod_banky": "2010",  # Fio banka
                        "vychozi_ucet": False
                    }
                ]
            }
        ]

        # Create bank accounts for all firms
        for firm_data in bank_settings_data:
            for account in firm_data["accounts"]:
                bank = SetBanka(
                    firma_id=firm_data["firma"].id,
                    nazev_uctu=account["nazev_uctu"],
                    mena=account["mena"],
                    cislo_uctu=account["cislo_uctu"],
                    iban=account["iban"],
                    swift=account["swift"],
                    kod_banky=account["kod_banky"]
                )
                session.add(bank)
            session.commit()

        # Create bank numbering settings for all firms
        bank_numbering_data = [
            # Firma 1 bank numbering
            {
                "firma": firma1,
                "numbering": [
                    {
                        "format_cisla": "BV",  # Bankovní výpis
                        "rok": datetime.now().year,
                        "poradove_cislo": 1
                    },
                    {
                        "format_cisla": "PB",  # Platební příkaz
                        "rok": datetime.now().year,
                        "poradove_cislo": 1
                    }
                ]
            },
            # Firma 2 bank numbering
            {
                "firma": firma2,
                "numbering": [
                    {
                        "format_cisla": "BAN",  # Bankovní výpis
                        "rok": datetime.now().year,
                        "poradove_cislo": 100
                    },
                    {
                        "format_cisla": "PAY",  # Platební příkaz
                        "rok": datetime.now().year,
                        "poradove_cislo": 100
                    }
                ]
            },
            # Firma 3 bank numbering
            {
                "firma": firma3,
                "numbering": [
                    {
                        "format_cisla": "BANK",  # Bankovní výpis
                        "rok": datetime.now().year,
                        "poradove_cislo": 1000
                    },
                    {
                        "format_cisla": "PAYMENT",  # Platební příkaz
                        "rok": datetime.now().year,
                        "poradove_cislo": 1000
                    }
                ]
            }
        ]

        # Create bank numbering settings for all firms
        for firm_data in bank_numbering_data:
            for numbering in firm_data["numbering"]:
                bank_numbering = SetBankaCislovani(
                    firma_id=firm_data["firma"].id,
                    format_cisla=numbering["format_cisla"],
                    rok=numbering["rok"],
                    poradove_cislo=numbering["poradove_cislo"]
                )
                session.add(bank_numbering)
            session.commit()

        # Create email settings for all firms
        email_settings_data = [
            {
                "firma": firma1,
                "zpusob_odeslani": ZpusobOdeslaniEmailu.PRILOHA_PDF,
                "odeslat_email_pres": OdeslatEmailPres.INTERNI_SERVER,
                "email_odchozi": "info@fxtc.cz",
                "jmeno_odesilatele": "FXTC Company",
                "smtp_server": None,
                "smtp_port": None,
                "smtp_username": None,
                "smtp_server_potrebuje_overeni": True,
                "smtp_password": None,
                "smtp_domain": None,
                "email_ucetni": "ucetni@fxtc.cz",
                "zasilat_upominky_automaticky": True,
                "zasilat_podekovani_automaticky": True,
                "text_prefix": "Dobrý den,\n\n",
                "text_suffix": "\n\nS pozdravem\nFXTC Company",
                "text_templates": {
                    "faktura_vydana": "v příloze zasíláme fakturu za naše služby.",
                    "faktura_zalohova": "v příloze zasíláme zálohovou fakturu.",
                    "danovy_doklad": "v příloze zasíláme daňový doklad.",
                    "dobropis": "v příloze zasíláme dobropis.",
                    "prodejka": "v příloze zasíláme prodejku.",
                    "cenova_nabidka": "v příloze zasíláme cenovou nabídku.",
                    "upominky": "dovolujeme si Vás upozornit na neuhrazenou fakturu.",
                    "podekovani": "děkujeme za včasnou úhradu faktury."
                }
            },
            {
                "firma": firma2,
                "zpusob_odeslani": ZpusobOdeslaniEmailu.ODKAZ_PDF,
                "odeslat_email_pres": OdeslatEmailPres.VLASTNI_SMTP_SERVER,
                "email_odchozi": "karel@company.cz",
                "jmeno_odesilatele": "Karel's Company",
                "smtp_server": "smtp.company.cz",
                "smtp_port": 587,
                "smtp_username": "karel@company.cz",
                "smtp_server_potrebuje_overeni": True,
                "smtp_password": "dummy_password",
                "smtp_domain": "company.cz",
                "email_ucetni": "ucetni@company.cz",
                "zasilat_upominky_automaticky": False,
                "zasilat_podekovani_automaticky": True,
                "text_prefix": "Vážený zákazníku,\n\n",
                "text_suffix": "\n\nDěkujeme\nKarel's Company",
                "text_templates": {
                    "faktura_vydana": "zasíláme Vám fakturu ke stažení.",
                    "faktura_zalohova": "zasíláme Vám zálohovou fakturu ke stažení.",
                    "danovy_doklad": "zasíláme Vám daňový doklad ke stažení.",
                    "dobropis": "zasíláme Vám dobropis ke stažení.",
                    "prodejka": "zasíláme Vám prodejku ke stažení.",
                    "cenova_nabidka": "zasíláme Vám cenovou nabídku ke stažení.",
                    "upominky": "prosíme o úhradu faktury.",
                    "podekovani": "děkujeme za úhradu.\n\nS přáním hezkého dne"
                }
            },
            {
                "firma": firma3,
                "zpusob_odeslani": ZpusobOdeslaniEmailu.PRILOHA_PDF,
                "odeslat_email_pres": OdeslatEmailPres.INTERNI_SERVER,
                "email_odchozi": "Firma3@fxtc.cz",
                "jmeno_odesilatele": "FX Firma 3",
                "smtp_server": None,
                "smtp_port": None,
                "smtp_username": None,
                "smtp_server_potrebuje_overeni": True,
                "smtp_password": None,
                "smtp_domain": None,
                "email_ucetni": None,
                "zasilat_upominky_automaticky": True,
                "zasilat_podekovani_automaticky": False,
                "text_prefix": "Dobrý den,\n\n",
                "text_suffix": "\n\nS pozdravem\nFX Firma 3",
                "text_templates": {
                    "faktura_vydana": "v příloze naleznete fakturu.",
                    "faktura_zalohova": "v příloze naleznete zálohovou fakturu.",
                    "danovy_doklad": "v příloze naleznete daňový doklad.",
                    "dobropis": "v příloze naleznete dobropis.",
                    "prodejka": "v příloze naleznete prodejku.",
                    "cenova_nabidka": "v příloze naleznete cenovou nabídku.",
                    "upominky": "upozorňujeme na neuhrazenou fakturu.",
                    "podekovani": "děkujeme za platbu."
                }
            }
        ]

        # Create email settings for each firma
        for settings in email_settings_data:
            firma = settings["firma"]
            text_prefix = settings["text_prefix"]
            text_suffix = settings["text_suffix"]
            text_templates = settings["text_templates"]

            set_email = SetEmail(
                firma_id=firma.id,
                zpusob_odeslani=settings["zpusob_odeslani"],
                odeslat_email_pres=settings["odeslat_email_pres"],
                email_odchozi=settings["email_odchozi"],
                jmeno_odesilatele=settings["jmeno_odesilatele"],
                smtp_server=settings["smtp_server"],
                smtp_port=settings["smtp_port"],
                smtp_username=settings["smtp_username"],
                smtp_server_potrebuje_overeni=settings["smtp_server_potrebuje_overeni"],
                smtp_password=settings["smtp_password"],
                smtp_domain=settings["smtp_domain"],
                text_faktura_vydana=text_prefix +
                text_templates["faktura_vydana"] + text_suffix,
                text_faktura_zalohova=text_prefix +
                text_templates["faktura_zalohova"] + text_suffix,
                text_danovy_doklad=text_prefix +
                text_templates["danovy_doklad"] + text_suffix,
                text_dobropis=text_prefix +
                text_templates["dobropis"] + text_suffix,
                text_prodejka=text_prefix +
                text_templates["prodejka"] + text_suffix,
                text_cenova_nabidka=text_prefix +
                text_templates["cenova_nabidka"] + text_suffix,
                email_ucetni=settings["email_ucetni"],
                zasilat_upominky_automaticky=settings["zasilat_upominky_automaticky"],
                text_upominky=text_prefix +
                text_templates["upominky"] + text_suffix,
                zasilat_podekovani_automaticky=settings["zasilat_podekovani_automaticky"],
                text_podekovani=text_prefix +
                text_templates["podekovani"] + text_suffix
            )
            session.add(set_email)
            session.commit()

        # Create purchase settings for all firms
        for firma in [firma1, firma2, firma3]:
            # Basic purchase settings
            set_nakup = SetNakup(
                firma_id=firma.id,
                typ_ceny=TypCeny.BEZ_DPH,
                sazba_dph=SazbaDPH.DPH_21,
                zpusob_uhrady=ZpusobUhradyNakup.PREVODEM
            )
            session.add(set_nakup)

            # Purchase invoice settings
            set_nakup_faktura = SetNakupFakturaPrijata(
                firma_id=firma.id,
                format_cisla="DF",
                rok=2025,
                poradove_cislo=0
            )
            session.add(set_nakup_faktura)

            # Purchase receipt settings
            set_nakup_uctenka = SetNakupUctenka(
                firma_id=firma.id,
                format_cisla="UC",
                rok=2025,
                poradove_cislo=1
            )
            session.add(set_nakup_uctenka)

            session.commit()

        # Create SetPokladna for firma 1
        pokladna1 = SetPokladna(
            firma_id=firma1.id,
            nazev_pokladny="Hlavní pokladna",
            mena=Mena.CZK,
            pocatecni_stav=10000.0,
            pocatecni_stav_datum=datetime(2025, 1, 1),
            poznamka="Hlavní pokladna pro běžný provoz"
        )
        session.add(pokladna1)
        session.commit()

        # Create SetTerminal linked to pokladna1
        terminal1 = SetTerminal(
            firma_id=firma1.id,
            pokladna_id=pokladna1.id,
            nazev_terminalu="Terminál 1",
            sparovano_pres_pin=True,
            typ_prodeje=TypProdeje.PRIMO_Z_DOKLADU,
            poznamka="Hlavní prodejní terminál"
        )
        session.add(terminal1)
        session.commit()

        # Create SetPokladnaCislovani for firma 1
        pokladna_cislovani = SetPokladnaCislovani(
            firma_id=firma1.id,
            format_cisla="PP",
            rok=2025,
            poradove_cislo=0
        )
        session.add(pokladna_cislovani)
        session.commit()

        # Create SetPokladna for firma 2
        pokladna2 = SetPokladna(
            firma_id=firma2.id,
            nazev_pokladny="Pokladna Praha 2",
            mena=Mena.CZK,
            pocatecni_stav=5000.0,
            pocatecni_stav_datum=datetime(2025, 1, 1),
            poznamka="Pokladna pro pobočku Praha 2"
        )
        session.add(pokladna2)
        session.commit()

        # Create SetTerminal linked to pokladna2
        terminal2 = SetTerminal(
            firma_id=firma2.id,
            pokladna_id=pokladna2.id,
            nazev_terminalu="Terminál Praha 2",
            sparovano_pres_pin=True,
            typ_prodeje=TypProdeje.TERMINAL_MIMO_DOKLAD,
            poznamka="Terminál pro rychlé prodeje"
        )
        session.add(terminal2)
        session.commit()

        # Create SetPokladnaCislovani for firma 2
        pokladna_cislovani2 = SetPokladnaCislovani(
            firma_id=firma2.id,
            format_cisla="PD2",
            rok=2025,
            poradove_cislo=0
        )
        session.add(pokladna_cislovani2)
        session.commit()

        # Create SetPokladna for firma 3
        pokladna3 = SetPokladna(
            firma_id=firma3.id,
            nazev_pokladny="Hlavní pokladna Firma 3",
            mena=Mena.EUR,
            pocatecni_stav=1000.0,
            pocatecni_stav_datum=datetime(2025, 1, 1),
            poznamka="Eurová pokladna pro zahraniční transakce"
        )
        session.add(pokladna3)
        session.commit()

        # Create SetTerminal linked to pokladna3
        terminal3 = SetTerminal(
            firma_id=firma3.id,
            pokladna_id=pokladna3.id,
            nazev_terminalu="Terminál F3",
            sparovano_pres_pin=False,
            typ_prodeje=TypProdeje.PRIMO_Z_DOKLADU,
            poznamka="Hlavní prodejní terminál Firma 3"
        )
        session.add(terminal3)
        session.commit()

        # Create SetPokladnaCislovani for firma 3
        pokladna_cislovani3 = SetPokladnaCislovani(
            firma_id=firma3.id,
            format_cisla="F3P",
            rok=2025,
            poradove_cislo=0
        )
        session.add(pokladna_cislovani3)
        session.commit()

        # Document settings configuration
        document_settings = [
            (SetFakturaVydana, "FV", "Faktury vydané"),
            (SetDobropis, "DB", "Dobropisy"),
            (SetFakturaZalohova, "ZF", "Zálohové faktury"),
            (SetDokladPrijataPlatba, "DP", "Daňové doklady"),
            (SetCenoveNabidka, "CN", "Cenové nabídky"),
            (SetProdejka, "PR", "Prodejky"),
            (SetInterniDoklad, "ID", "Interní doklady"),
        ]

        # Create document settings for all firms
        firms = [firma1, firma2, firma3]
        for firma in firms:
            for setting_class, prefix, name in document_settings:
                setting = setting_class(
                    firma_id=firma.id,
                    format_cisla=f"{prefix}",
                    rok=2025,
                    nazev_rady=name,
                    poradove_cislo=1
                )
                session.add(setting)
            session.commit()

        # Create subuser 1 for the first firma 1
        subuser = SubUser(
            firma_id=firma1.id,
            email="gigafx@centrum.cz",
            # password: admin
            hashed_password="$4b$12$zB95A56X3SOQSenxDvzk.eibNAjWZPAoX11bM1XxphpmRXAdGODxO",
            first_name="Alfons",
            last_name="Blecha",
            bio="Regular User",
            is_active=True,
            phone="+420666555422",
            # Kontakty
            kontakty=True,
            # Prodej
            prodej_faktury_vydane=True,
            prodej_faktury_zalohove=True,
            prodej_danove_doklady_k_platbe=True,
            prodej_dobropisy=True,
            prodej_cenove_nabidky=True,
            prodej_prodejky=True,
            prodej_zauctovani_prodejek=True,
            prodej_sablony=True,
            prodej_pravidelne_faktury=True,
            prodej_uhrady=True,
            prodej_prehled_prodeje=False,
            # Nakup
            nakup_faktury_prijate=False,
            nakup_uctenky=False,
            nakup_uhrady=False,
            # Sklad/Cenik
            produkty_cenik=True,
            skladove_pohyby=True,
            sklady=True,
            # Finance
            banka=False,
            pokladna=False,
            dan_z_prijmu=False,
            # Nastaveni
            nastavni_predplatne=False,
            nastavni_firma=False,
            nastavni_prodej=False,
            nastavni_nakup=False,
            nastavni_komunikace=False,
            nastavni_banka=False,
            nastavni_pokladna=False,
            nastavni_aplikace=False,
            nastavni_uzivatel=False
        )
        session.add(subuser)
        session.commit()

        # Create subuser 2 for the third firma 3
        subuser2 = SubUser(
            firma_id=firma3.id,
            email="gigafx2@centrum.cz",
            # password: admin
            hashed_password="$4b$12$zB95A56X3SOQSenxDvzk.eibNAjWZPAoX11bM1XxphpmRXAdGODxO",
            first_name="Alfons2",
            last_name="Blecha2",
            bio="Regular User2",
            is_active=True,
            phone="+420666555422",
            # Kontakty
            kontakty=True,
            # Prodej
            prodej_faktury_vydane=True,
            prodej_faktury_zalohove=True,
            prodej_danove_doklady_k_platbe=True,
            prodej_dobropisy=True,
            prodej_cenove_nabidky=True,
            prodej_prodejky=True,
            prodej_zauctovani_prodejek=True,
            prodej_sablony=True,
            prodej_pravidelne_faktury=True,
            prodej_uhrady=True,
            prodej_prehled_prodeje=False,
            # Nakup
            nakup_faktury_prijate=False,
            nakup_uctenky=False,
            nakup_uhrady=False,
            # Sklad/Cenik
            produkty_cenik=True,
            skladove_pohyby=True,
            sklady=True,
            # Finance
            banka=False,
            pokladna=False,
            dan_z_prijmu=False,
            # Nastaveni
            nastavni_predplatne=False,
            nastavni_firma=False,
            nastavni_prodej=False,
            nastavni_nakup=False,
            nastavni_komunikace=False,
            nastavni_banka=False,
            nastavni_pokladna=False,
            nastavni_aplikace=False,
            nastavni_uzivatel=False
        )
        session.add(subuser2)
        session.commit()

        # Create sample produkty for firma 1
        produkty = []
        for i in range(1, 23):
            base_price = Decimal(f"{i}00.00")
            dph_rate = Decimal("0.21")  # 21% DPH
            dph_amount = base_price * dph_rate
            price_with_dph = base_price + dph_amount

            produkty.append(
                Produkt(
                    firma_id=firma1.id,
                    nazev=f"Produkt {i}",
                    popis=f"Sample produkt {i}",
                    katalogove_cislo=f"P00{i}",
                    carovy_kod=f"{i}3456789012{i}",
                    prodejni_mnozstvi=1,
                    jednotka="kus",
                    cena=base_price,
                    mena="CZK",
                    sazba_dph=SazbaDPH.DPH_21,
                    typ_ceny=TypCeny.S_DPH,
                    cena_s_dph=price_with_dph,
                    cena_bez_dph=base_price,
                    cleneni_dph="",
                    sledovat_sklad=True,
                    aktivni=True
                )
            )
        session.add_all(produkty)
        session.commit()

        # Create sample produkty for firma 2
        produkty = []
        for i in range(1, 23):
            base_price = Decimal(f"{i}00.00")
            dph_rate = Decimal("0.21")  # 21% DPH
            dph_amount = base_price * dph_rate
            price_with_dph = base_price + dph_amount

            produkty.append(
                Produkt(
                    firma_id=firma2.id,
                    nazev=f"Produkt {i} firma 2",
                    popis=f"Sample produkt {i} firma 2",
                    katalogove_cislo=f"P00{i}",
                    carovy_kod=f"{i}3456789012{i}",
                    prodejni_mnozstvi=1,
                    jednotka="kus",  # Now using string instead of enum
                    cena=base_price,
                    mena="CZK",
                    sazba_dph=SazbaDPH.DPH_21,
                    typ_ceny=TypCeny.S_DPH,
                    cena_s_dph=price_with_dph,
                    cena_bez_dph=base_price,
                    cleneni_dph="",
                    sledovat_sklad=True,
                    aktivni=True
                )
            )
        session.add_all(produkty)
        session.commit()

        # Create sample produkty for firma 3
        produkty = []
        for i in range(1, 13):
            base_price = Decimal(f"{i}00.00")
            dph_rate = Decimal("0.21")  # 21% DPH
            dph_amount = base_price * dph_rate
            price_with_dph = base_price + dph_amount

            produkty.append(
                Produkt(
                    firma_id=firma3.id,
                    nazev=f"Produkt {i} Firma3",
                    popis=f"Sample produkt {i} Firma3",
                    katalogove_cislo=f"P00{i}Firma3",
                    carovy_kod=f"{i}234567890{i}3",
                    prodejni_mnozstvi=1,
                    jednotka="kus",  # Now using string instead of enum
                    cena=base_price,
                    mena="CZK",
                    sazba_dph=SazbaDPH.DPH_21,
                    typ_ceny=TypCeny.S_DPH,
                    cena_s_dph=price_with_dph,
                    cena_bez_dph=base_price,
                    cleneni_dph="",
                    sledovat_sklad=True,
                    aktivni=True
                )
            )
        session.add_all(produkty)
        session.commit()

        # Create sample sklady for firma 1, firma 2 and firma 3
        sklady = []
        # Sklady for firma 1
        sklady.append(
            Sklad(
                firma_id=firma1.id,
                nazev="Hlavní sklad",
                popis="Centrální skladové prostory",
                poznamka="Otevřeno 7-17 hod",
                aktivni=True,
                vychozi=True
            )
        )
        sklady.append(
            Sklad(
                firma_id=firma1.id,
                nazev="Expediční sklad",
                popis="Sklad pro expedici zboží",
                poznamka="Expedice pouze v pracovní dny",
                aktivni=True,
                vychozi=False
            )
        )
        
        # Sklady for firma 2
        sklady.append(
            Sklad(
                firma_id=firma2.id,
                nazev="Centrální sklad",
                popis="Hlavní skladové prostory",
                poznamka="Otevřeno 8-16 hod",
                aktivni=True,
                vychozi=True
            )
        )
        sklady.append(
            Sklad(
                firma_id=firma2.id,
                nazev="Sklad materiálu",
                popis="Skladové prostory pro materiál",
                poznamka="Přístup pouze pro oprávněné osoby",
                aktivni=True,
                vychozi=False
            )
        )
        
        # Sklady for firma 3
        sklady.append(
            Sklad(
                firma_id=firma3.id,
                nazev="Hlavní sklad",
                popis="Hlavní skladové prostory",
                poznamka="Otevřeno 8-16 hod",
                aktivni=True,
                vychozi=True
            )
        )
        sklady.append(
            Sklad(
                firma_id=firma3.id,
                nazev="Vedlejší sklad",
                popis="Skladové prostory pro nadměrné zboží",
                poznamka="Pouze po domluvě",
                aktivni=True,
                vychozi=False
            )
        )
        sklady.append(
            Sklad(
                firma_id=firma3.id,
                nazev="Prodejna sklad",
                popis="Skladové prostory pro nadměrné zboží",
                poznamka="Prodejna otevřeno od 8:00 do 16:00",
                aktivni=True,
                vychozi=False
            )
        )
        session.add_all(sklady)
        session.commit()

        # Create sample contacts for firma 1
        kontakty = []
        for i in range(1, 13):
            kontakt = Kontakt(
                firma_id=firma1.id,
                zeme=Zeme.CZ,
                nazev_firmy=f"Sample Customer {i}",
                ico=f"{i}87654321",
                dic=f"CZ{i}87654321",
                ulice=f"Zákaznická {i}",
                mesto="Brno",
                psc="60200",
                email=f"customer{i}@example.com",
                telefon=f"+42098765432{i}",
                web="",
                titul="",
                jmeno="",
                prijmeni="",
                mobil=""
            )
            kontakty.append(kontakt)
            for j in range(1, 5):
                kontakt.adresy.append(
                    KontaktAdresa(
                        ulice=f"Adresa firma 1{j}",
                        mesto="Brno",
                        psc="60200",
                        zeme=Zeme.CZ,
                        jmeno=f"Jméno {j}",
                        prijmeni=f"Přijmení {j}",
                        telefon=f"+42098765432{i*10+j}",
                        email=f"adresa{j}@example.com",
                        poznamka=f"Poznámka test poznamka{j}"
                    )
                )
        session.add_all(kontakty)
        session.commit()

        # Create sample contacts for firma 2
        kontakty = []
        for i in range(1, 13):
            kontakt = Kontakt(
                firma_id=firma2.id,
                zeme=Zeme.CZ,
                nazev_firmy=f"Sample Customer {i} firma 2",
                ico=f"{i}87654321",
                dic=f"CZ{i}87654321",
                ulice=f"Zákaznická {i}",
                mesto="Brno",
                psc="60200",
                email=f"customer{i}@example.com",
                telefon=f"+42098765432{i}",
                web="",
                titul="",
                jmeno="",
                prijmeni="",
                mobil=""
            )
            kontakty.append(kontakt)
            for j in range(1, 5):
                kontakt.adresy.append(
                    KontaktAdresa(
                        ulice=f"Adresa firma 2 {j}",
                        mesto="Brno",
                        psc="60200",
                        zeme=Zeme.CZ,
                        jmeno=f"Jméno {j}",
                        prijmeni=f"Přijmení {j}",
                        telefon=f"+42098765432{i*10+j}",
                        email=f"adresa{j}@example.com",
                        poznamka=f"Poznámka test poznamka{j}"
                    )
                )
        session.add_all(kontakty)
        session.commit()

        # Create sample contacts for firma 3
        kontakty = []
        for i in range(1, 13):
            kontakt = Kontakt(
                firma_id=firma3.id,
                zeme=Zeme.CZ,
                nazev_firmy=f"Sample Customer {i} Firma 3",
                ico=f"{i}765432{i}",
                dic=f"CZ{i}765432{i}",
                ulice=f"Zákaznická {i} Firma3",
                mesto="Brno Firma3",
                psc="60200",
                email=f"customer{i}Firma3@example.com",
                telefon=f"+42098765432{i}",
                web="",
                titul="",
                jmeno="",
                prijmeni="",
                mobil=""
            )
            kontakty.append(kontakt)
            for j in range(1, 5):
                kontakt.adresy.append(
                    KontaktAdresa(
                        ulice=f"Adresa firma 3 {j}",
                        mesto="Brno Firma3",
                        psc="60200",
                        zeme=Zeme.CZ,
                        jmeno=f"Jméno {j}",
                        prijmeni=f"Přijmení {j}",
                        telefon=f"+42098765432{i*10+j}",
                        email=f"adresa{j}Firma3@example.com",
                        poznamka=f"Poznámka test poznamka{j}"
                    )
                )
        session.add_all(kontakty)
        session.commit()

        # Vytvoření skladových pohybů typu "Příjem" pro prvních 10 produktů každé firmy
        print("Vytváření skladových pohybů pro produkty...")
        
        # Zjištění všech produktů pro každou firmu
        produkty_firma1 = session.query(Produkt).filter(Produkt.firma_id == firma1.id).limit(10).all()
        produkty_firma2 = session.query(Produkt).filter(Produkt.firma_id == firma2.id).limit(10).all()
        produkty_firma3 = session.query(Produkt).filter(Produkt.firma_id == firma3.id).limit(10).all()
        
        # Zjištění skladů pro každou firmu - bereme první sklad pro každou firmu
        sklad_firma1 = session.query(Sklad).filter(Sklad.firma_id == firma1.id).first()
        sklad_firma2 = session.query(Sklad).filter(Sklad.firma_id == firma2.id).first()
        sklad_firma3 = session.query(Sklad).filter(Sklad.firma_id == firma3.id).first()
        
        skladove_pohyby = []
        
        # Uživatel pro všechny pohyby
        admin_user = session.query(User).filter(User.email == "fxtc@post.cz").first()
        
        # Vytvoření skladových pohybů pro produkty firmy 1
        if sklad_firma1 and produkty_firma1:
            for i, produkt in enumerate(produkty_firma1):
                # Nastavíme sledování skladu pro tyto produkty
                produkt.sledovat_sklad = True
                skladovy_pohyb = SkladPohyb(
                    firma_id=firma1.id,
                    sklad_id=sklad_firma1.id,
                    produkt_id=produkt.id,
                    produkt_nazev=produkt.nazev,
                    uzivatel_id=admin_user.id,
                    first_last_name=f"{admin_user.first_name} {admin_user.last_name}",
                    typ_pohybu=TypSkladovehoPohybu.PRIJEM,
                    mnozstvi=Decimal("1000.00"),
                    jednotka=produkt.jednotka,
                    doklad_id=None,
                    cislo_dokladu=f"PRIJ-{firma1.id}-{i+1}",
                    typ_dokladu=TypDokladu.PRIJEMKA,
                    popis=f"Iniciální příjem na sklad: {produkt.nazev}",
                    zustatek_mnozstvi=Decimal("1000.00"),
                    rezervovane_mnozstvi=Decimal("0.00"),
                    dostupne_mnozstvi=Decimal("1000.00")
                )
                skladove_pohyby.append(skladovy_pohyb)
                
        # Vytvoření skladových pohybů pro produkty firmy 2
        if sklad_firma2 and produkty_firma2:
            for i, produkt in enumerate(produkty_firma2):
                # Nastavíme sledování skladu pro tyto produkty
                produkt.sledovat_sklad = True
                skladovy_pohyb = SkladPohyb(
                    firma_id=firma2.id,
                    sklad_id=sklad_firma2.id,
                    produkt_id=produkt.id,
                    produkt_nazev=produkt.nazev,
                    uzivatel_id=admin_user.id,
                    first_last_name=f"{admin_user.first_name} {admin_user.last_name}",
                    typ_pohybu=TypSkladovehoPohybu.PRIJEM,
                    mnozstvi=Decimal("1000.00"),
                    jednotka=produkt.jednotka,
                    doklad_id=None,
                    cislo_dokladu=f"PRIJ-{firma2.id}-{i+1}",
                    typ_dokladu=TypDokladu.PRIJEMKA,
                    popis=f"Iniciální příjem na sklad: {produkt.nazev}",
                    zustatek_mnozstvi=Decimal("1000.00"),
                    rezervovane_mnozstvi=Decimal("0.00"),
                    dostupne_mnozstvi=Decimal("1000.00")
                )
                skladove_pohyby.append(skladovy_pohyb)
                
        # Vytvoření skladových pohybů pro produkty firmy 3
        if sklad_firma3 and produkty_firma3:
            for i, produkt in enumerate(produkty_firma3):
                # Nastavíme sledování skladu pro tyto produkty
                produkt.sledovat_sklad = True
                skladovy_pohyb = SkladPohyb(
                    firma_id=firma3.id,
                    sklad_id=sklad_firma3.id,
                    produkt_id=produkt.id,
                    produkt_nazev=produkt.nazev,
                    uzivatel_id=admin_user.id,
                    first_last_name=f"{admin_user.first_name} {admin_user.last_name}",
                    typ_pohybu=TypSkladovehoPohybu.PRIJEM,
                    mnozstvi=Decimal("1000.00"),
                    jednotka=produkt.jednotka,
                    doklad_id=None,
                    cislo_dokladu=f"PRIJ-{firma3.id}-{i+1}",
                    typ_dokladu=TypDokladu.PRIJEMKA,
                    popis=f"Iniciální příjem na sklad: {produkt.nazev}",
                    zustatek_mnozstvi=Decimal("1000.00"),
                    rezervovane_mnozstvi=Decimal("0.00"),
                    dostupne_mnozstvi=Decimal("1000.00")
                )
                skladove_pohyby.append(skladovy_pohyb)
                
        session.add_all(skladove_pohyby)
        session.commit()


if __name__ == "__main__":
    init_db()
