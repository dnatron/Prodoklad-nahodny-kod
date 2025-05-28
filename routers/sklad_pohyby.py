from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse, Response, RedirectResponse
from sqlmodel import Session, select, func
from database import get_session
from models.user import User, SubUser
from models.sklad import Sklad
from models.produkt import Produkt
from models.sklad_pohyby import SkladPohyb
from models.enums import TypSkladovehoPohybu, TypDokladu
from auth import get_current_user, get_selected_firma_id
from fastapi.templating import Jinja2Templates
from utils import handle_message, MessageType
from decimal import Decimal

router = APIRouter()
templates = Jinja2Templates(directory="templates")

ITEMS_PER_PAGE = 10

@router.get("/sklad-pohyby", response_class=HTMLResponse)
async def list_sklad_pohyby(
    request: Request,
    page: int = 1,
    search: str = "",
    sklad_id: str = None,
    typ_pohybu: str = None,
    current_user: User | SubUser | None = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    # Kontrola typu uživatele ze session
    is_subuser = request.session.get("is_subuser", False)
    if is_subuser:
        response = RedirectResponse(url="/", status_code=303)
        return handle_message(request, "Přístup odepřen", MessageType.DANGER, response)
    
    # Pro běžné uživatele zkontrolujeme, zda mají správnou roli
    if not is_subuser and getattr(current_user, 'role', None) != "user":
        response = RedirectResponse(url="/", status_code=303)
        return handle_message(request, "Přístup odepřen", MessageType.DANGER, response)
    
    # Získání vybrané firmy
    firma_id = get_selected_firma_id(request, session, current_user)
    if firma_id is None:
        response = RedirectResponse(url="/", status_code=303)
        return handle_message(request, "Není vybrána firma", MessageType.WARNING, response)
    
    # Vytvoření dotazu pro skladové pohyby
    query = select(SkladPohyb).where(SkladPohyb.firma_id == firma_id)
    
    # Aplikace filtrů, pokud jsou zadány
    if search:
        query = query.where(
            (SkladPohyb.cislo_dokladu.contains(search)) | 
            (SkladPohyb.popis.contains(search)) |
            (SkladPohyb.produkt_nazev.contains(search))
        )
    
    # Převod sklad_id z řetězce na číslo, pokud není prázdné
    sklad_id_int = None
    if sklad_id and sklad_id.strip():
        try:
            sklad_id_int = int(sklad_id)
            query = query.where(SkladPohyb.sklad_id == sklad_id_int)
        except ValueError:
            # Neplatné číslo, ignorujeme tento filtr
            pass
    
    if typ_pohybu:
        try:
            # Použití hranatých závorek pro přístup k enum podle názvu
            typ_enum = TypSkladovehoPohybu[typ_pohybu]
            query = query.where(SkladPohyb.typ_pohybu == typ_enum)
        except KeyError:
            # Neplatný název enum, ignorujeme tento filtr
            pass
    
    # Získání celkového počtu pro stránkování
    total_items = session.exec(
        select(func.count(SkladPohyb.id)).where(SkladPohyb.firma_id == firma_id)
    ).one()
    
    total_pages = (total_items + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE
    
    # Získání stránkovaných položek
    skladove_pohyby = session.exec(
        query
        .order_by(SkladPohyb.vytvoreno.desc())
        .offset((page - 1) * ITEMS_PER_PAGE)
        .limit(ITEMS_PER_PAGE)
    ).all()
    
    # Pro každý pohyb načteme související entities a vytvoříme slovník doplňujících informací
    pohyby_data = []
    for pohyb in skladove_pohyby:
        # Načtení souvisejících entit
        sklad = session.get(Sklad, pohyb.sklad_id)
        produkt = session.get(Produkt, pohyb.produkt_id)
        
        uzivatel = None
        if pohyb.uzivatel_id:
            uzivatel = session.get(User, pohyb.uzivatel_id)
        
        # Vytvoříme rozšířená data pro pohyb
        pohyb_dict = {
            "pohyb": pohyb,
            "sklad": sklad,
            "produkt": produkt,
            "uzivatel": uzivatel
        }
        pohyby_data.append(pohyb_dict)
    
    # Získání seznamu skladů pro filtr
    sklady = session.exec(
        select(Sklad)
        .where(Sklad.firma_id == firma_id)
        .where(Sklad.aktivni)
    ).all()
    
    # Získání hodnot enum pro UI
    typy_pohybu = [{"name": e.name, "value": e.value} for e in TypSkladovehoPohybu]
    
    # Kontrola, zda se jedná o HTMX požadavek
    is_htmx = request.headers.get("HX-Request") == "true"
    
    if is_htmx:
        # Pro HTMX požadavky vrátíme pouze řádky tabulky
        return templates.TemplateResponse(
            "sklad-cenik/pohyby/pohyby_rows.html",
            {
                "request": request,
                "pohyby_data": pohyby_data
            }
        )
    else:
        # Pro běžné požadavky vrátíme celou stránku
        return templates.TemplateResponse(
            "sklad-cenik/pohyby/pohyby.html",
            {
                "request": request,
                "pohyby_data": pohyby_data,
                "current_page": page,
                "total_pages": total_pages,
                "total_items": total_items,
                "search": search,
                "sklady": sklady,
                "selected_sklad_id": sklad_id_int,
                "typy_pohybu": typy_pohybu,
                "selected_typ_pohybu": typ_pohybu
            }
        )

@router.get("/sklad-pohyby/add", response_class=HTMLResponse)
async def get_add_pohyb_page(
    request: Request,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    if current_user.role != "user":
        response = RedirectResponse(url="/", status_code=303)
        return handle_message(request, "Přístup odepřen", MessageType.DANGER, response)
    
    # Get selected firma
    firma_id = get_selected_firma_id(request, session, current_user)
    if firma_id is None:
        response = RedirectResponse(url="/", status_code=303)
        return handle_message(request, "Není vybrána firma", MessageType.WARNING, response)
    
    # Získání všech aktivních skladů pro firmu
    sklady = session.exec(
        select(Sklad)
        .where(Sklad.firma_id == firma_id)
        .where(Sklad.aktivni)
    ).all()
    
    # Získání výchozího skladu, pokud existuje
    default_sklad_id = None
    default_sklad = session.exec(
        select(Sklad)
        .where(Sklad.firma_id == firma_id)
        .where(Sklad.vychozi)
    ).first()
    
    if default_sklad:
        default_sklad_id = default_sklad.id
    
    # Získání hodnot enum pro UI
    typy_pohybu = [{"name": e.name, "value": e.value} for e in TypSkladovehoPohybu]
    typy_dokladu = [{"name": e.name, "value": e.value} for e in TypDokladu]
    
    return templates.TemplateResponse(
        "sklad-cenik/pohyby/pohyby_add.html",
        {
            "request": request,
            "pohyb": None,
            "sklady": sklady,
            "typy_pohybu": typy_pohybu,
            "typy_dokladu": typy_dokladu,
            "default_sklad_id": default_sklad_id
        }
    )

# Endpoint pro získání modálního okna pro výběr produktu
@router.get("/sklad-pohyby/select-produkt", response_class=HTMLResponse)
async def get_produkt_select_modal_for_pohyb(
    request: Request,
    search: str = "",
    sklad_id: int = None,
    page: int = 1,
    per_page: int = 10,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    if not current_user:
        return RedirectResponse(url="/login", status_code=303)

    firma_id = get_selected_firma_id(request, session, current_user)
    if not firma_id:
        return handle_message(request, "Není vybrána firma", MessageType.DANGER)

    # Načtení skladů pro výběr
    sklady = session.exec(select(Sklad).where(Sklad.firma_id == firma_id).where(Sklad.aktivni)).all()
    
    # Pokud není zadáno sklad_id, pokusíme se získat výchozí sklad
    if sklad_id is None:
        default_sklad = session.exec(select(Sklad).where(Sklad.firma_id == firma_id).where(Sklad.vychozi)).first()
        if default_sklad:
            sklad_id = default_sklad.id
    
    # Načtení produktů přímo při otevření modálu
    offset = (page - 1) * per_page
    
    # Základní query pro produkty se sledováním skladu a aktivní
    query = select(Produkt).where(Produkt.firma_id == firma_id).where(Produkt.sledovat_sklad).where(Produkt.aktivni)
    
    # Aplikace filtru vyhledávání, pokud je zadán
    if search:
        search_term = f"%{search}%"
        query = query.where(
            (Produkt.nazev.ilike(search_term)) | 
            (Produkt.popis.ilike(search_term)) |
            (Produkt.katalogove_cislo.ilike(search_term))
        )
    
    # Počítání celkových výsledků pro stránkování
    count_query = select(func.count()).select_from(query.subquery())
    total_count = session.exec(count_query).one()
    total_pages = (total_count + per_page - 1) // per_page
    
    # Aplikace stránkování
    query = query.offset(offset).limit(per_page)
    produkty = session.exec(query).all()
    
    # Získání množství na skladě pro každý produkt
    produkty_with_stock = []
    stock_info = {}
    
    for produkt in produkty:
        # Získání posledního skladového pohybu pro tento produkt ve vybraném skladu
        stock_query = None
        if sklad_id:
            stock_query = select(SkladPohyb).where(
                SkladPohyb.produkt_id == produkt.id,
                SkladPohyb.sklad_id == sklad_id
            ).order_by(SkladPohyb.vytvoreno.desc())
        else:
            stock_query = select(SkladPohyb).where(
                SkladPohyb.produkt_id == produkt.id
            ).order_by(SkladPohyb.vytvoreno.desc())
        
        latest_movement = session.exec(stock_query).first()
        
        # Uložení informací o stavu skladu do slovníku
        stock_info[produkt.id] = {
            "mnozstvi_skladem": latest_movement.zustatek_mnozstvi if latest_movement else Decimal("0.00"),
            "rezervovane_mnozstvi": latest_movement.rezervovane_mnozstvi if latest_movement else Decimal("0.00"),
            "dostupne_mnozstvi": latest_movement.dostupne_mnozstvi if latest_movement else Decimal("0.00")
        }
        
        produkty_with_stock.append(produkt)

    return templates.TemplateResponse(
        "sklad-cenik/pohyby/product_list.html",
        {
            "request": request,
            "produkty": produkty_with_stock,
            "stock_info": stock_info,
            "current_page": page,
            "total_pages": total_pages,
            "total_count": total_count,
            "search": search,
            "sklad_id": sklad_id,
            "sklady": sklady
        }
    )

# Endpoint pro vyhledávání produktů v modálním okně
@router.get("/sklad-pohyby/search-produkty", response_class=HTMLResponse)
async def search_produkty_for_pohyb(
    request: Request,
    search: str = "",
    sklad_id: int = None,
    page: int = 1,
    per_page: int = 10,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    if not current_user:
        return RedirectResponse(url="/login", status_code=303)

    firma_id = get_selected_firma_id(request, session, current_user)
    if not firma_id:
        return handle_message(request, "Není vybrána firma", MessageType.DANGER)

    # Pokud není zadáno sklad_id, pokusíme se získat výchozí sklad
    if sklad_id is None:
        default_sklad = session.exec(select(Sklad).where(Sklad.firma_id == firma_id).where(Sklad.vychozi)).first()
        if default_sklad:
            sklad_id = default_sklad.id
    
    # Načtení produktů
    offset = (page - 1) * per_page
    
    # Základní query pro produkty se sledováním skladu a aktivní
    query = select(Produkt).where(Produkt.firma_id == firma_id).where(Produkt.sledovat_sklad).where(Produkt.aktivni)
    
    # Aplikace filtru vyhledávání, pokud je zadán
    if search:
        search_term = f"%{search}%"
        query = query.where(
            (Produkt.nazev.ilike(search_term)) | 
            (Produkt.popis.ilike(search_term)) |
            (Produkt.katalogove_cislo.ilike(search_term))
        )
    
    # Počítání celkových výsledků pro stránkování
    count_query = select(func.count()).select_from(query.subquery())
    total_count = session.exec(count_query).one()
    total_pages = (total_count + per_page - 1) // per_page
    
    # Aplikace stránkování
    query = query.offset(offset).limit(per_page)
    produkty = session.exec(query).all()
    
    # Získání množství na skladě pro každý produkt
    produkty_with_stock = []
    stock_info = {}
    
    for produkt in produkty:
        # Získání posledního skladového pohybu pro tento produkt ve vybraném skladu
        stock_query = None
        if sklad_id:
            stock_query = select(SkladPohyb).where(
                SkladPohyb.produkt_id == produkt.id,
                SkladPohyb.sklad_id == sklad_id
            ).order_by(SkladPohyb.vytvoreno.desc())
        else:
            stock_query = select(SkladPohyb).where(
                SkladPohyb.produkt_id == produkt.id
            ).order_by(SkladPohyb.vytvoreno.desc())
        
        latest_movement = session.exec(stock_query).first()
        
        # Uložení informací o stavu skladu do slovníku
        stock_info[produkt.id] = {
            "mnozstvi_skladem": latest_movement.zustatek_mnozstvi if latest_movement else Decimal("0.00"),
            "rezervovane_mnozstvi": latest_movement.rezervovane_mnozstvi if latest_movement else Decimal("0.00"),
            "dostupne_mnozstvi": latest_movement.dostupne_mnozstvi if latest_movement else Decimal("0.00")
        }
        
        produkty_with_stock.append(produkt)

    return templates.TemplateResponse(
        "sklad-cenik/pohyby/product_list.html",
        {
            "request": request,
            "produkty": produkty_with_stock,
            "stock_info": stock_info,
            "current_page": page,
            "total_pages": total_pages,
            "total_count": total_count,
            "search": search,
            "sklad_id": sklad_id
        }
    )

# Endpoint pro výběr produktu pro skladový pohyb
@router.post("/sklad-pohyby/select-produkt/{produkt_id}", response_class=HTMLResponse)
async def select_produkt_for_pohyb(
    request: Request,
    produkt_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    if not current_user:
        return RedirectResponse(url="/login", status_code=303)

    firma_id = get_selected_firma_id(request, session, current_user)
    if not firma_id:
        return handle_message(request, "Není vybrána firma", MessageType.DANGER)
    
    # Získání dat z formuláře
    form_data = await request.form()
    sklad_id = int(form_data.get("sklad_id", 0))
    
    # Získání produktu
    produkt = session.get(Produkt, produkt_id)
    if not produkt or produkt.firma_id != firma_id:
        return Response("Produkt nenalezen", status_code=404)

    # Získání skladu
    sklad = session.get(Sklad, sklad_id)
    if not sklad or sklad.firma_id != firma_id:
        return Response("Sklad nenalezen", status_code=404)
    
    # Získání nejnovějších skladových dat pro tento produkt a sklad
    latest_pohyb = session.exec(
        select(SkladPohyb)
        .where(SkladPohyb.firma_id == firma_id)
        .where(SkladPohyb.sklad_id == sklad_id)
        .where(SkladPohyb.produkt_id == produkt_id)
        .order_by(SkladPohyb.vytvoreno.desc())
    ).first()
    
    # Výchozí hodnoty, pokud neexistuje žádný pohyb
    zustatek_mnozstvi = Decimal("0.00")
    rezervovane_mnozstvi = Decimal("0.00")
    dostupne_mnozstvi = Decimal("0.00")
    
    if latest_pohyb:
        zustatek_mnozstvi = latest_pohyb.zustatek_mnozstvi
        rezervovane_mnozstvi = latest_pohyb.rezervovane_mnozstvi
        dostupne_mnozstvi = latest_pohyb.dostupne_mnozstvi

    return templates.TemplateResponse(
        "sklad-cenik/pohyby/selected_product.html",
        {
            "request": request,
            "produkt": produkt,
            "sklad": sklad,
            "zustatek_mnozstvi": zustatek_mnozstvi,
            "rezervovane_mnozstvi": rezervovane_mnozstvi,
            "dostupne_mnozstvi": dostupne_mnozstvi
        }
    )

# Endpoint pro získání informací o stavu zásob produktu na skladě
@router.get("/sklad-pohyby/get-inventory-info", response_class=HTMLResponse)
async def get_inventory_info(
    request: Request,
    produkt_id: int,
    sklad_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    if not current_user:
        return Response("Unauthorized", status_code=401)

    firma_id = get_selected_firma_id(request, session, current_user)
    if not firma_id:
        return Response("Není vybrána firma", status_code=400)
    
    # Získání nejnovějších skladových dat pro tento produkt a sklad
    latest_pohyb = session.exec(
        select(SkladPohyb)
        .where(SkladPohyb.firma_id == firma_id)
        .where(SkladPohyb.sklad_id == sklad_id)
        .where(SkladPohyb.produkt_id == produkt_id)
        .order_by(SkladPohyb.vytvoreno.desc())
    ).first()
    
    # Výchozí hodnoty, pokud neexistuje žádný pohyb
    zustatek_mnozstvi = Decimal("0.00")
    rezervovane_mnozstvi = Decimal("0.00")
    dostupne_mnozstvi = Decimal("0.00")
    
    if latest_pohyb:
        zustatek_mnozstvi = latest_pohyb.zustatek_mnozstvi
        rezervovane_mnozstvi = latest_pohyb.rezervovane_mnozstvi
        dostupne_mnozstvi = latest_pohyb.dostupne_mnozstvi

    return templates.TemplateResponse(
        "sklad-cenik/pohyby/inventory_info.html",
        {
            "request": request,
            "zustatek_mnozstvi": zustatek_mnozstvi,
            "rezervovane_mnozstvi": rezervovane_mnozstvi,
            "dostupne_mnozstvi": dostupne_mnozstvi
        }
    )

@router.post("/sklad-pohyby/add", response_class=HTMLResponse)
async def add_pohyb(
    request: Request,
    current_user: User | SubUser | None = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Přidá nový skladový pohyb"""
    form_data = await request.form()
    
    # Získání vybrané firmy
    firma_id = get_selected_firma_id(request, session, current_user)
    if firma_id is None:
        response = RedirectResponse(url="/", status_code=303)
        return handle_message(request, "Není vybrána firma", MessageType.WARNING, response)
    
    # Kontrola, zda se jedná o HTMX požadavek
    is_htmx = request.headers.get("HX-Request") == "true"
    
    try:
        # Zpracování dat z formuláře
        sklad_id = int(form_data.get("sklad_id"))
        produkt_id = int(form_data.get("produkt_id"))
        typ_pohybu_str = form_data.get("typ_pohybu")
        mnozstvi_str = form_data.get("mnozstvi", "0")
        cislo_dokladu = form_data.get("cislo_dokladu")
        typ_dokladu_str = form_data.get("typ_dokladu")
        popis = form_data.get("popis")
        
        # Převod na správné datové typy
        try:
            mnozstvi = Decimal(mnozstvi_str)
            typ_pohybu = TypSkladovehoPohybu[typ_pohybu_str]
            typ_dokladu = TypDokladu[typ_dokladu_str] if typ_dokladu_str else None
        except (ValueError, KeyError):
            if is_htmx:
                response = Response(status_code=200)
            else:
                response = RedirectResponse(url="/sklad-pohyby/add", status_code=303)
            return handle_message(request, "Neplatné hodnoty formuláře", MessageType.DANGER, response)
        
        # Validace dat
        if mnozstvi <= 0:
            if is_htmx:
                response = Response(status_code=200)
            else:
                response = RedirectResponse(url="/sklad-pohyby/add", status_code=303)
            return handle_message(request, "Množství musí být větší než 0", MessageType.DANGER, response)
        
        # Kontrola, zda sklad existuje
        sklad = session.get(Sklad, sklad_id)
        if not sklad or sklad.firma_id != firma_id:
            if is_htmx:
                response = Response(status_code=200)
            else:
                response = RedirectResponse(url="/sklad-pohyby/add", status_code=303)
            return handle_message(request, "Neplatný sklad", MessageType.DANGER, response)
        
        # Kontrola, zda produkt existuje
        produkt = session.get(Produkt, produkt_id)
        if not produkt or produkt.firma_id != firma_id:
            if is_htmx:
                response = Response(status_code=200)
            else:
                response = RedirectResponse(url="/sklad-pohyby/add", status_code=303)
            return handle_message(request, "Neplatný produkt", MessageType.DANGER, response)
        
        # Vypočítat aktuální stavy zásob pro daný produkt a sklad
        # 1. Zjistit poslední stav zásob
        last_pohyb = session.exec(
            select(SkladPohyb)
            .where(SkladPohyb.firma_id == firma_id)
            .where(SkladPohyb.sklad_id == sklad_id)
            .where(SkladPohyb.produkt_id == produkt_id)
            .order_by(SkladPohyb.vytvoreno.desc())
        ).first()
        
        # Výchozí hodnoty, pokud neexistuje předchozí pohyb
        zustatek_mnozstvi = Decimal("0.00")
        rezervovane_mnozstvi = Decimal("0.00")
        dostupne_mnozstvi = Decimal("0.00")
        
        # Pokud existuje předchozí pohyb, použít jeho hodnoty jako základ
        if last_pohyb:
            zustatek_mnozstvi = last_pohyb.zustatek_mnozstvi
            rezervovane_mnozstvi = last_pohyb.rezervovane_mnozstvi
            dostupne_mnozstvi = last_pohyb.dostupne_mnozstvi
        
        # Aktualizovat hodnoty podle typu pohybu
        if typ_pohybu == TypSkladovehoPohybu.PRIJEM:
            zustatek_mnozstvi += mnozstvi
            dostupne_mnozstvi += mnozstvi
        elif typ_pohybu == TypSkladovehoPohybu.VYDEJ:
            zustatek_mnozstvi -= mnozstvi
            dostupne_mnozstvi -= mnozstvi
            # Kontrola, zda je dostatek zásob
            if zustatek_mnozstvi < 0 or dostupne_mnozstvi < 0:
                if is_htmx:
                    response = Response(status_code=200)
                else:
                    response = RedirectResponse(url="/sklad-pohyby/add", status_code=303)
                return handle_message(request, "Nedostatek zásob na skladě", MessageType.DANGER, response)
        elif typ_pohybu == TypSkladovehoPohybu.REZERVACE:
            rezervovane_mnozstvi += mnozstvi
            dostupne_mnozstvi -= mnozstvi
            # Kontrola, zda je dostatek dostupných zásob
            if dostupne_mnozstvi < 0:
                if is_htmx:
                    response = Response(status_code=200)
                else:
                    response = RedirectResponse(url="/sklad-pohyby/add", status_code=303)
                return handle_message(request, "Nedostatek dostupných zásob na skladě", MessageType.DANGER, response)
        
        # Vytvoření nového skladového pohybu
        pohyb = SkladPohyb(
            firma_id=firma_id,
            sklad_id=sklad_id,
            produkt_id=produkt_id,
            produkt_nazev=produkt.nazev,
            typ_pohybu=typ_pohybu,
            mnozstvi=mnozstvi,
            jednotka=produkt.jednotka,
            cislo_dokladu=cislo_dokladu if cislo_dokladu else None,
            typ_dokladu=typ_dokladu,
            popis=popis if popis else None,
            uzivatel_id=current_user.id,
            first_last_name=f"{current_user.first_name} {current_user.last_name}",
            zustatek_mnozstvi=zustatek_mnozstvi,
            rezervovane_mnozstvi=rezervovane_mnozstvi,
            dostupne_mnozstvi=dostupne_mnozstvi
        )
        
        session.add(pohyb)
        session.commit()
        
        # Zpráva o úspěchu
        success_message = "Skladový pohyb byl úspěšně přidán"
        
        if is_htmx:
            # Pro HTMX požadavky musíme uložit zprávu do session a přesměrovat
            # Tím zajistíme, že se zpráva zobrazí po přesměrování
            if "message" not in request.session:
                request.session["message"] = {}
            request.session["message"][MessageType.SUCCESS.value] = success_message
            
            # Použití HX-Redirect pro přesměrování na straně klienta
            response = Response(status_code=200)
            response.headers["HX-Redirect"] = "/sklad-pohyby"
            return response
        else:
            # Pro běžná odeslání formuláře
            response = RedirectResponse(url="/sklad-pohyby", status_code=303)
            return handle_message(request, success_message, MessageType.SUCCESS, response)
    
    except Exception as e:
        # Zpracování ostatních chyb
        if is_htmx:
            response = Response(status_code=200)
        else:
            response = RedirectResponse(url="/sklad-pohyby/add", status_code=303)
        
        return handle_message(request, f"Chyba při vytváření skladového pohybu: {str(e)}", MessageType.DANGER, response)

@router.get("/sklad-pohyby/{pohyb_id}", response_class=HTMLResponse)
async def get_pohyb_detail(
    request: Request, 
    pohyb_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    if not current_user:
        return RedirectResponse(url="/login", status_code=303)
    
    # Získání vybrané firmy
    firma_id = get_selected_firma_id(request, session, current_user)
    if firma_id is None:
        response = RedirectResponse(url="/", status_code=303)
        return handle_message(request, "Není vybrána firma", MessageType.WARNING, response)
    
    # Získání skladového pohybu
    pohyb = session.get(SkladPohyb, pohyb_id)
    if not pohyb or pohyb.firma_id != firma_id:
        response = Response(status_code=404)
        return handle_message(request, "Skladový pohyb nenalezen", MessageType.DANGER, response)
    
    # Načtení souvisejících entit
    sklad = session.get(Sklad, pohyb.sklad_id)
    produkt = session.get(Produkt, pohyb.produkt_id)
    
    uzivatel = None
    if pohyb.uzivatel_id:
        uzivatel = session.get(User, pohyb.uzivatel_id)
    
    # Příprava odpovědi
    return templates.TemplateResponse(
        "sklad-cenik/pohyby/pohyby_detail.html",
        {
            "request": request,
            "pohyb": pohyb,
            "sklad": sklad,
            "produkt": produkt,
            "uzivatel": uzivatel
        }
    )