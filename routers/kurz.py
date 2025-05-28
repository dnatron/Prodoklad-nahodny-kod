from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlmodel import Session, select
from typing import List, Optional
from datetime import date, datetime
import urllib.request
import urllib.error
import ssl
from database import get_session
from models.kurz import Kurz
from auth import get_current_user, get_template_context, User, SubUser
from utils import MessageType, handle_message, templates

router = APIRouter(
    prefix="/nastaveni-kurzy",
    tags=["nastaveni-kurzy"],
)

# URL a hlavička pro získání kurzů ČNB
CNB_URL = "https://www.cnb.cz/cs/financni_trhy/devizovy_trh/kurzy_devizoveho_trhu/denni_kurz.txt"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}


def fetch_cnb_kurzy():
    """Stáhne aktuální kurzovní lístek ČNB."""
    try:
        # Pro macOS často potřebujeme obejít SSL verifikaci pro některé servery
        context = ssl._create_unverified_context()
        
        req = urllib.request.Request(CNB_URL, headers=HEADERS)
        with urllib.request.urlopen(req, context=context) as response:
            return response.read().decode('utf-8')
    except urllib.error.HTTPError as e:
        raise HTTPException(status_code=e.code, detail=f"Chyba při stahování kurzů ČNB: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chyba při stahování kurzů ČNB: {str(e)}")


def parse_cnb_kurzy(text_data: str):
    """Parsuje textová data kurzovního lístku ČNB."""
    lines = text_data.strip().split('\n')
    
    # Kontrola, zda máme dostatek řádků
    if len(lines) < 2:
        raise ValueError("Neplatná struktura dat kurzovního lístku")
    
    # Získáme datum kurzu z prvního řádku
    try:
        # První řádek obsahuje datum ve formátu "28.03.2025 #62"
        datum_parts = lines[0].split()[0].split('.')
        datum_kurzu = date(int(datum_parts[2]), int(datum_parts[1]), int(datum_parts[0]))
    except (IndexError, ValueError) as e:
        raise ValueError(f"Chyba při zpracování data kurzu: {str(e)}")
    
    # Zpracování kurzů měn
    kurzy = []
    # Přeskočíme první dva řádky (datum a hlavičku)
    for line in lines[2:]:
        if not line.strip():
            continue
        
        try:
            parts = line.split('|')
            if len(parts) < 5:
                continue
            
            nazev_statu = parts[0].strip()
            nazev_meny = parts[1].strip()
            mnozstvi = int(parts[2].strip())
            kod_meny = parts[3].strip()
            kurz_meny = float(parts[4].strip().replace(',', '.'))
            
            kurzy.append({
                "nazev_statu": nazev_statu,
                "nazev_meny": nazev_meny,
                "mnozstvi": mnozstvi,
                "kod_meny": kod_meny,
                "kurz_meny": kurz_meny,
                "datum_kurzu": datum_kurzu
            })
        except Exception:
            # Pokračujeme i když je jedna položka neplatná
            continue
    
    return kurzy


@router.get("/", response_class=HTMLResponse)
async def list_kurzy(
    request: Request,
    session: Session = Depends(get_session),
    current_user: User | SubUser | None = Depends(get_current_user)
):
    """Zobrazí seznam kurzů měn."""
    if not current_user:
        return RedirectResponse(url="/login", status_code=303)
    
    try:
        # Získáme nejnovější datum kurzu
        latest_date_query = select(Kurz.datum_kurzu).order_by(Kurz.datum_kurzu.desc()).limit(1)
        latest_date = session.exec(latest_date_query).first()
        
        kurzy = []
        if latest_date:
            # Získáme kurzy pro nejnovější datum
            kurzy_query = select(Kurz).where(Kurz.datum_kurzu == latest_date).order_by(Kurz.nazev_statu)
            kurzy = session.exec(kurzy_query).all()
        
        context = get_template_context(request)
        context.update({
            "kurzy": kurzy,
            "datum_kurzu": latest_date if latest_date else None,
        })
        
        return templates.TemplateResponse(
            "nastaveni/kurzy/kurzy_list.html", 
            context
        )
    except Exception as e:
        response = RedirectResponse(url="/dashboard", status_code=303)
        handle_message(
            request,
            MessageType.DANGER,
            f"Chyba při načítání kurzů měn: {str(e)}",
            response=response
        )
        return response


@router.get("/aktualizovat", response_class=HTMLResponse)
def aktualizovat_kurzy(
    request: Request,
    session: Session = Depends(get_session),
    current_user: User | SubUser | None = Depends(get_current_user)
):
    """Aktualizuje kurzy měn z ČNB."""
    if not current_user:
        return RedirectResponse(url="/login", status_code=303)
    
    try:
        # Stáhneme aktuální kurzovní lístek
        text_data = fetch_cnb_kurzy()
        
        # Zpracujeme data
        kurzy_data = parse_cnb_kurzy(text_data)
        
        if not kurzy_data:
            response = RedirectResponse(url="/nastaveni-kurzy", status_code=303)
            handle_message(
                request,
                MessageType.WARNING,
                "Nebyla nalezena žádná data kurzů",
                response=response
            )
            return response
        
        # Zjistíme datum kurzu z prvního záznamu
        datum_kurzu = kurzy_data[0]["datum_kurzu"]
        
        # Zkontrolujeme, jestli již máme kurzy pro toto datum
        existing_kurz_query = select(Kurz).where(Kurz.datum_kurzu == datum_kurzu).limit(1)
        existing_kurz = session.exec(existing_kurz_query).first()
        
        if existing_kurz:
            # Smažeme existující kurzy pro toto datum
            delete_query = select(Kurz).where(Kurz.datum_kurzu == datum_kurzu)
            kurzy_to_delete = session.exec(delete_query).all()
            for kurz in kurzy_to_delete:
                session.delete(kurz)
        
        # Uložíme nové kurzy
        for kurz_data in kurzy_data:
            kurz = Kurz(
                nazev_statu=kurz_data["nazev_statu"],
                nazev_meny=kurz_data["nazev_meny"],
                mnozstvi=kurz_data["mnozstvi"],
                kod_meny=kurz_data["kod_meny"],
                kurz_meny=kurz_data["kurz_meny"],
                datum_kurzu=kurz_data["datum_kurzu"],
                datum_create=datetime.now()
            )
            session.add(kurz)
        
        session.commit()
        
        response = RedirectResponse(url="/nastaveni-kurzy", status_code=303)
        handle_message(
            request,
            MessageType.SUCCESS,
            f"Kurzovní lístek byl úspěšně aktualizován k datu {datum_kurzu.strftime('%d.%m.%Y')}",
            response=response
        )
        return response
        
    except Exception as e:
        response = RedirectResponse(url="/kurzy", status_code=303)
        handle_message(
            request,
            MessageType.DANGER,
            f"Chyba při aktualizaci kurzů měn: {str(e)}",
            response=response
        )
        return response


@router.get("/api/kurzy", response_model=List[Kurz])
async def api_get_kurzy(
    kod_meny: Optional[str] = None,
    datum: Optional[date] = None,
    session: Session = Depends(get_session)
):
    """API endpoint pro získání kurzů měn."""
    try:
        # Vytvoříme základní dotaz
        query = select(Kurz)
        
        # Filtrování podle kódu měny
        if kod_meny:
            query = query.where(Kurz.kod_meny == kod_meny.upper())
        
        # Filtrování podle data
        if datum:
            query = query.where(Kurz.datum_kurzu == datum)
        else:
            # Když datum není zadáno, použijeme nejnovější datum
            latest_date_query = select(Kurz.datum_kurzu).order_by(Kurz.datum_kurzu.desc()).limit(1)
            latest_date = session.exec(latest_date_query).first()
            if latest_date:
                query = query.where(Kurz.datum_kurzu == latest_date)
        
        # Seřazení výsledků
        query = query.order_by(Kurz.nazev_statu)
        
        # Vykonání dotazu
        kurzy = session.exec(query).all()
        
        return kurzy
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chyba při načítání kurzů měn: {str(e)}")


@router.get("/api/kurz/{kod_meny}")
async def api_get_kurz(
    kod_meny: str,
    datum: Optional[date] = None,
    session: Session = Depends(get_session)
):
    """API endpoint pro získání konkrétního kurzu měny."""
    try:
        # Vytvoříme základní dotaz
        query = select(Kurz).where(Kurz.kod_meny == kod_meny.upper())
        
        # Filtrování podle data
        if datum:
            query = query.where(Kurz.datum_kurzu == datum)
        else:
            # Když datum není zadáno, použijeme nejnovější datum
            latest_date_query = select(Kurz.datum_kurzu).order_by(Kurz.datum_kurzu.desc()).limit(1)
            latest_date = session.exec(latest_date_query).first()
            if latest_date:
                query = query.where(Kurz.datum_kurzu == latest_date)
        
        # Vykonání dotazu
        kurz = session.exec(query).first()
        
        if not kurz:
            raise HTTPException(status_code=404, detail=f"Kurz pro měnu {kod_meny} nebyl nalezen")
        
        return {
            "kod_meny": kurz.kod_meny,
            "nazev_statu": kurz.nazev_statu,
            "nazev_meny": kurz.nazev_meny,
            "mnozstvi": kurz.mnozstvi,
            "kurz_meny": kurz.kurz_meny,
            "datum_kurzu": kurz.datum_kurzu.isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chyba při načítání kurzu měny: {str(e)}")