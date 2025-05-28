from enum import Enum


class TypPlatce(str, Enum):
    NEPLATCE_DPH = "Neplátce DPH"
    PLATCE_DPH = "Plátce DPH"
    IDENTIFIKOVANA_OSOBA = "Identifikovaná osoba"


class TypSubjektu(str, Enum):
    FO = "Fyzická osoba"
    PO = "Právnická osoba"


class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"


class TypCeny(str, Enum):
    S_DPH = "s DPH"
    BEZ_DPH = "bez DPH"
    PDP = "PDP"


class TypProdeje(str, Enum):
    PRIMO_Z_DOKLADU = "Prodávat se bude přímo z ProDokladu"
    TERMINAL_MIMO_DOKLAD = "Prodejní terminal mimo Doklad"


class ZpusobOdeslaniEmailu(str, Enum):
    PRILOHA_PDF = "Příloha PDF v e-mailu"
    ODKAZ_PDF = "Odkaz na PDF v prohlížeči"


class OdeslatEmailPres(str, Enum):
    INTERNI_SERVER = "Interní server"
    VLASTNI_SMTP_SERVER = "Vlastní SMTP server"


class ZpusobUhrady(str, Enum):
    PREVODEM = "Převodem"
    KARTOU = "Kartou"
    HOTOVE = "Hotově"
    DOBIRKA = "Dobírka"
    ZAPOCTEM = "Zapoctem"
    ZALOHOU = "Zálohou"
    PAYPAL = "PayPal"
    STRIPE = "Stripe"


class Zaokrouhleni(str, Enum):
    NEZAOKROUHLOVAT = "Žádné"
    ZAOKROUHLOVAT = "Zaokrouhlovat"
    PODLE_ZPUSOBU_UHRADY = "Pouze hotovostní platby"


class Mena(str, Enum):
    """Seznam podporovaných měn podle ČNB"""
    CZK = "CZK"  # Česká republika - koruna
    EUR = "EUR"  # EMU - euro
    USD = "USD"  # USA - dolar
    PLN = "PLN"  # Polsko - zlotý
    GBP = "GBP"  # Velká Británie - libra
    BGN = "BGN"  # Bulharsko - lev
    DKK = "DKK"  # Dánsko - koruna
    HUF = "HUF"  # Maďarsko - forint
    RON = "RON"  # Rumunsko - leu
    SEK = "SEK"  # Švédsko - koruna
    AUD = "AUD"  # Austrálie - dolar
    BRL = "BRL"  # Brazílie - real
    PHP = "PHP"  # Filipíny - peso
    HKD = "HKD"  # Hongkong - dolar
    INR = "INR"  # Indie - rupie
    IDR = "IDR"  # Indonesie - rupie
    ISK = "ISK"  # Island - koruna
    ILS = "ILS"  # Izrael - nový šekel
    JPY = "JPY"  # Japonsko - jen
    ZAR = "ZAR"  # Jižní Afrika - rand
    CAD = "CAD"  # Kanada - dolar
    KRW = "KRW"  # Korejská republika - won
    XDR = "XDR"  # MMF - ZPČ
    MYR = "MYR"  # Malajsie - ringgit
    MXN = "MXN"  # Mexiko - peso
    NOK = "NOK"  # Norsko - koruna
    NZD = "NZD"  # Nový Zéland - dolar
    SGD = "SGD"  # Singapur - dolar
    THB = "THB"  # Thajsko - baht
    TRY = "TRY"  # Turecko - lira
    CNY = "CNY"  # Čína - žen-min-pi
    CHF = "CHF"  # Švýcarsko - frank


class ZpusobUhradyNakup(str, Enum):
    PREVODEM = "Převodem"
    KARTOU = "Kartou"
    HOTOVE = "Hotově"
    ZAPOCTEM = "Zapoctem"
    ZALOHOU = "Zálohou"
    PAYPAL = "PayPal"
    STRIPE = "Stripe"


class SazbaDPH(str, Enum):
    DPH_0 = "0"
    DPH_12 = "12"
    DPH_21 = "21"


class TypSkladovehoPohybu(str, Enum):
    PRIJEM = "Příjem"
    VYDEJ = "Výdej"
    REZERVACE = "Rezervace"
    ZRUSENI_REZERVACE = "Zrušení rezervace"
    ZMENA_REZERVACE = "Změna rezervace"


class TypDokladu(str, Enum):
    FAKTURA_VYDANA = "Faktura vydána"
    FAKTURA_ZALOHOVA = "Faktura zálohová"
    CENOVA_NABIDKA = "Cenová nabídka"
    FAKTURA_PRIJATA = "Faktura přijatá"
    DOBROPIS = "Dobropis"
    DODACI_LIST = "Dodací list"
    PREVODKA = "Převodka"
    PRIJEMKA = "Příjemka"
    VYDEJKA = "Výdejka"
    INVENTURA = "Inventura"
    VRATKA = "Vratka"
    OSTATNI = "Ostatní"


class Zeme(str, Enum):
    """Seznam zemí pro použití v adresách a kontaktech"""
    # Evropa
    CZ = "Česko"
    SK = "Slovensko"
    AT = "Rakousko"
    DE = "Německo"
    PL = "Polsko"
    HU = "Maďarsko"
    GB = "Velká Británie"
    FR = "Francie"
    IT = "Itálie"
    ES = "Španělsko"
    NL = "Nizozemsko"
    BE = "Belgie"
    SE = "Švédsko"
    DK = "Dánsko"
    FI = "Finsko"
    NO = "Norsko"
    CH = "Švýcarsko"
    RU = "Rusko"
    UA = "Ukrajina"
    RO = "Rumunsko"
    BG = "Bulharsko"
    HR = "Chorvatsko"
    SI = "Slovinsko"
    RS = "Srbsko"
    GR = "Řecko"
    TR = "Turecko"
    PT = "Portugalsko"
    IE = "Irsko"
    LT = "Litva"
    LV = "Lotyšsko"
    EE = "Estonsko"
    BY = "Bělorusko"
    MD = "Moldavsko"
    AL = "Albánie"
    BA = "Bosna a Hercegovina"
    ME = "Černá Hora"
    MK = "Severní Makedonie"
    LU = "Lucembursko"
    IS = "Island"
    MT = "Malta"
    CY = "Kypr"
    LI = "Lichtenštejnsko"
    MC = "Monako"
    SM = "San Marino"
    VA = "Vatikán"
    AD = "Andorra"
    
    # Severní Amerika
    US = "Spojené státy americké"
    CA = "Kanada"
    MX = "Mexiko"
    CR = "Kostarika"
    PA = "Panama"
    JM = "Jamajka"
    CU = "Kuba"
    DO = "Dominikánská republika"
    
    # Jižní Amerika
    BR = "Brazílie"
    AR = "Argentina"
    CL = "Chile"
    CO = "Kolumbie"
    PE = "Peru"
    VE = "Venezuela"
    UY = "Uruguay"
    EC = "Ekvádor"
    
    # Asie
    CN = "Čína"
    JP = "Japonsko"
    KR = "Jižní Korea"
    IN = "Indie"
    ID = "Indonésie"
    MY = "Malajsie"
    SG = "Singapur"
    TH = "Thajsko"
    VN = "Vietnam"
    PH = "Filipíny"
    AE = "Spojené arabské emiráty"
    SA = "Saúdská Arábie"
    IL = "Izrael"
    LB = "Libanon"
    IR = "Írán"
    IQ = "Irák"
    PK = "Pákistán"
    AF = "Afghánistán"
    KZ = "Kazachstán"
    UZ = "Uzbekistán"
    
    # Afrika
    ZA = "Jihoafrická republika"
    EG = "Egypt"
    MA = "Maroko"
    TN = "Tunisko"
    NG = "Nigérie"
    KE = "Keňa"
    ET = "Etiopie"
    GH = "Ghana"
    SN = "Senegal"
    TZ = "Tanzanie"
    
    # Austrálie a Oceánie
    AU = "Austrálie"
    NZ = "Nový Zéland"
    FJ = "Fidži"
    PG = "Papua-Nová Guinea"