from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from sqlmodel import Session, select
import json
from datetime import datetime

from models.user import User, SubUser
from models.nastaveni_pokladna import SetPokladna, SetTerminal, SetPokladnaCislovani
from models.enums import TypProdeje, Mena
from database import get_session
from auth import get_current_user, get_template_context, get_firma_filter, get_selected_firma_id
from utils import MessageType, handle_message, templates

router = APIRouter()

@router.get("/nastaveni-pokladna", response_class=HTMLResponse)
async def list_pokladny(
    request: Request,
    session: Session = Depends(get_session),
    current_user: User | SubUser | None = Depends(get_current_user)
):
    if not current_user:
        response = RedirectResponse(url="/login", status_code=303)
        return handle_message(request, "Pro zobrazení nastavení se prosím přihlaste", MessageType.WARNING, response)
    
    # Získání vybrané firmy
    selected_firma_id = get_selected_firma_id(request, session, current_user)
    if selected_firma_id is None:
        response = RedirectResponse(url="/firma", status_code=303)
        return handle_message(request, "Není vybrána aktivní firma", MessageType.DANGER, response)
    
    # Získání pokladen
    pokladny = session.exec(
        select(SetPokladna)
        .where(SetPokladna.firma_id == selected_firma_id)
    ).all()

    # Získání terminalů
    terminaly = session.exec(
        select(SetTerminal)
        .where(SetTerminal.firma_id == selected_firma_id)
    ).all()

    # Získání nastavení číslování
    cislovani = session.exec(
        select(SetPokladnaCislovani)
        .where(SetPokladnaCislovani.firma_id == selected_firma_id)
    ).first()
    
    # Příprava kontextu šablony
    context = {
        "pokladny": pokladny,
        "terminaly": terminaly,
        "typ_prodeje_choices": [e.value for e in TypProdeje],
        "cislovani": cislovani,
        "current_year": datetime.now().year
    }
    
    # Kontrola, zda je to HTMX request
    is_htmx = request.headers.get("HX-Request") == "true"
    if is_htmx:
        return templates.TemplateResponse(
            "nastaveni/pokladna/pokladna_table.html",
            {**get_template_context(request, session), **context}
        )
    
    return templates.TemplateResponse(
        "nastaveni/pokladna/pokladna.html",
        {**get_template_context(request, session), **context}
    )

@router.get("/nastaveni-pokladna/add", response_class=HTMLResponse)
async def add_pokladna_form(
    request: Request,
    session: Session = Depends(get_session),
    current_user: User | SubUser | None = Depends(get_current_user)
):
    if not current_user:
        return RedirectResponse(url="/login", status_code=303)
    
    # Získání kontextu šablony
    context = get_template_context(request, session)
    context["title"] = "Přidat pokladnu"
    context["action"] = "/nastaveni-pokladna/add"
    context["meny"] = list(Mena)
    context["pokladna"] = None
    return templates.TemplateResponse(
        "nastaveni/pokladna/pokladna_form.html",
        context
    )

@router.post("/nastaveni-pokladna/add", response_class=HTMLResponse)
async def add_pokladna(
    request: Request,
    session: Session = Depends(get_session),
    current_user: User | SubUser | None = Depends(get_current_user)
):
    if not current_user:
        response = RedirectResponse(url="/login", status_code=303)
        return handle_message(request, "Pro úpravu nastavení se prosím přihlaste", MessageType.WARNING, response)
    
    is_htmx = request.headers.get("HX-Request") == "true"
    
    try:
        # Získání dat z formuláře
        form = await request.form()
        
        # Získání vybrané firmy
        firma_id = get_selected_firma_id(request, session, current_user)
        if firma_id is None:
            response = RedirectResponse(url="/nastaveni-pokladna", status_code=303)
            return handle_message(request, "Není vybrána aktivní firma", MessageType.DANGER, response)
        
        # Vytvoření nové pokladny
        pokladna = SetPokladna(
            firma_id=firma_id,
            nazev_pokladny=form.get("nazev_pokladny"),
            mena=Mena(form.get("mena")),
            pocatecni_stav=float(form.get("pocatecni_stav")),
            pocatecni_stav_datum=datetime.strptime(form.get("pocatecni_stav_datum"), "%Y-%m-%d").date(),
            poznamka=form.get("poznamka", ""),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        session.add(pokladna)
        session.commit()
        session.refresh(pokladna)
        
        if is_htmx:
            response = templates.TemplateResponse(
                "nastaveni/pokladna/pokladna_row.html",
                {
                    **get_template_context(request, session),
                    "pokladna": pokladna
                }
            )
            # Přidáme HX-Trigger pro reload pokladen, ale zprávu zpracujeme přes handle_message
            response.headers["HX-Trigger"] = json.dumps({
                "reloadPokladny": True
            })
            return handle_message(request, "Pokladna byla úspěšně přidána", MessageType.SUCCESS, response)
        else:
            response = RedirectResponse(url="/nastaveni-pokladna", status_code=303)
            return handle_message(request, "Pokladna byla úspěšně přidána", MessageType.SUCCESS, response)
            
    except Exception:
        error_message = "Chyba při přidávání pokladny"
        if is_htmx:
            response = Response(status_code=422)
            return handle_message(request, error_message, MessageType.DANGER, response)
        else:
            response = RedirectResponse(url="/nastaveni-pokladna", status_code=303)
            return handle_message(request, error_message, MessageType.DANGER, response)

@router.get("/nastaveni-pokladna/{pokladna_id}/edit", response_class=HTMLResponse)
async def edit_pokladna_form(
    request: Request,
    pokladna_id: int,
    session: Session = Depends(get_session),
    current_user: User | SubUser | None = Depends(get_current_user)
):
    if not current_user:
        return RedirectResponse(url="/login", status_code=303)
    
    # Získání pokladny s kontrolou přístupu
    pokladna = session.get(SetPokladna, pokladna_id)
    if not pokladna:
        handle_message(request, "Pokladna nenalezena", MessageType.DANGER)
        return RedirectResponse(url="/nastaveni-pokladna", status_code=303)
    
    # Kontrola, zda má uživatel přístup k firmě tohoto pokladny
    firma_filter = get_firma_filter(request, session, current_user)
    if firma_filter is not None and pokladna.firma_id != get_selected_firma_id(request, session, current_user):
        handle_message(request, "Přístup odepřen", MessageType.DANGER)
        return RedirectResponse(url="/nastaveni-pokladna", status_code=303)
    
    # Získání kontextu šablony
    context = get_template_context(request, session)
    context["title"] = "Upravit pokladnu"
    context["action"] = f"/nastaveni-pokladna/{pokladna_id}/edit"
    context["pokladna"] = pokladna
    context["meny"] = list(Mena)
    return templates.TemplateResponse(
        "nastaveni/pokladna/pokladna_form.html",
        context
    )

@router.post("/nastaveni-pokladna/{pokladna_id}/edit", response_class=HTMLResponse)
async def edit_pokladna(
    request: Request,
    pokladna_id: int,
    session: Session = Depends(get_session),
    current_user: User | SubUser | None = Depends(get_current_user)
):
    if not current_user:
        response = RedirectResponse(url="/login", status_code=303)
        return handle_message(request, "Pro úpravu nastavení se prosím přihlaste", MessageType.WARNING, response)
    
    is_htmx = request.headers.get("HX-Request") == "true"
    
    # Získání dat z formuláře
    form = await request.form()
    
    # Získání pokladny a kontrola přístupu
    pokladna = session.get(SetPokladna, pokladna_id)
    if not pokladna:
        error_message = "Pokladna nebyla nalezena"
        if is_htmx:
            response = Response(status_code=404)
            return handle_message(request, error_message, MessageType.DANGER, response)
        else:
            response = RedirectResponse(url="/nastaveni-pokladna", status_code=303)
            return handle_message(request, error_message, MessageType.DANGER, response)
    
    # Kontrola, zda má uživatel přístup k firmě tohoto pokladny
    firma_filter = get_firma_filter(request, session, current_user)
    if firma_filter is not None and pokladna.firma_id != get_selected_firma_id(request, session, current_user):
        response = RedirectResponse(url="/nastaveni-pokladna", status_code=303)
        return handle_message(request, "Přístup odepřen", MessageType.DANGER, response)
    
    try:
        # Aktualizace polí pokladny
        pokladna.nazev_pokladny = form.get("nazev_pokladny")
        pokladna.mena = Mena(form.get("mena"))
        pokladna.pocatecni_stav = float(form.get("pocatecni_stav"))
        pokladna.pocatecni_stav_datum = datetime.strptime(form.get("pocatecni_stav_datum"), "%Y-%m-%d").date()
        pokladna.poznamka = form.get("poznamka", "")
        pokladna.updated_at = datetime.utcnow()
        
        session.add(pokladna)
        session.commit()
        
        if is_htmx:
            response = templates.TemplateResponse(
                "nastaveni/pokladna/pokladna_row.html",
                {
                    **get_template_context(request, session),
                    "pokladna": pokladna
                }
            )
            # Přidáme HX-Trigger pro reload pokladen, ale zprávu zpracujeme přes handle_message
            response.headers["HX-Trigger"] = json.dumps({
                "reloadPokladny": True
            })
            return handle_message(request, "Pokladna byla úspěšně upravena", MessageType.SUCCESS, response)
        else:
            response = RedirectResponse(url="/nastaveni-pokladna", status_code=303)
            return handle_message(request, "Pokladna byla úspěšně upravena", MessageType.SUCCESS, response)
            
    except Exception:
        error_message = "Chyba při úpravě pokladny"
        if is_htmx:
            response = Response(status_code=422)
            return handle_message(request, error_message, MessageType.DANGER, response)
        else:
            response = RedirectResponse(url="/nastaveni-pokladna", status_code=303)
            return handle_message(request, error_message, MessageType.DANGER, response)

@router.post("/nastaveni-terminal/{terminal_id}/edit", response_class=HTMLResponse)
async def edit_terminal(
    request: Request,
    terminal_id: int,
    session: Session = Depends(get_session),
    current_user: User | SubUser | None = Depends(get_current_user)
):
    if not current_user:
        response = RedirectResponse(url="/login", status_code=303)
        return handle_message(request, "Pro úpravu nastavení se prosím přihlaste", MessageType.WARNING, response)
    
    is_htmx = request.headers.get("HX-Request") == "true"
    
    try:
        # Získání dat z formuláře
        form = await request.form()
        
        # Získání terminálu a kontrola přístupu
        terminal = session.get(SetTerminal, terminal_id)
        if not terminal:
            error_message = "Terminál nebyl nalezen"
            if is_htmx:
                response = Response(status_code=404)
                return handle_message(request, error_message, MessageType.DANGER, response)
            else:
                response = RedirectResponse(url="/nastaveni-pokladna", status_code=303)
                return handle_message(request, error_message, MessageType.DANGER, response)
        
        # Kontrola, zda má uživatel přístup k firmě tohoto terminálu
        firma_filter = get_firma_filter(request, session, current_user)
        if firma_filter is not None and terminal.firma_id != get_selected_firma_id(request, session, current_user):
            error_message = "Přístup odepřen"
            if is_htmx:
                response = Response(status_code=403)
                return handle_message(request, error_message, MessageType.DANGER, response)
            else:
                response = RedirectResponse(url="/nastaveni-pokladna", status_code=303)
                return handle_message(request, error_message, MessageType.DANGER, response)
        
        # Aktualizace polí terminálu
        terminal.nazev_terminalu = form.get("nazev_terminalu")
        terminal.typ_prodeje = TypProdeje(form.get("typ_prodeje"))
        terminal.pokladna_id = int(form.get("pokladna_id")) if form.get("pokladna_id") else None
        terminal.sparovano_pres_pin = form.get("sparovano_pres_pin") == "true"
        terminal.poznamka = form.get("poznamka", "")
        terminal.updated_at = datetime.utcnow()
        
        session.add(terminal)
        session.commit()
        session.refresh(terminal)
        
        if is_htmx:
            response = templates.TemplateResponse(
                "nastaveni/pokladna/terminal_row.html",
                {
                    **get_template_context(request, session),
                    "terminal": terminal
                }
            )
            # Přidáme HX-Trigger pro reload terminálů, ale zprávu zpracujeme přes handle_message
            response.headers["HX-Trigger"] = json.dumps({
                "reloadTerminaly": True
            })
            return handle_message(request, "Terminál byl úspěšně upraven", MessageType.SUCCESS, response)
        else:
            response = RedirectResponse(url="/nastaveni-pokladna", status_code=303)
            return handle_message(request, "Terminál byl úspěšně upraven", MessageType.SUCCESS, response)
            
    except Exception:
        error_message = "Chyba při úpravě terminálu"
        if is_htmx:
            response = Response(status_code=422)
            return handle_message(request, error_message, MessageType.DANGER, response)
        else:
            response = RedirectResponse(url="/nastaveni-pokladna", status_code=303)
            return handle_message(request, error_message, MessageType.DANGER, response)

@router.get("/nastaveni-terminal/add", response_class=HTMLResponse)
async def add_terminal_form(
    request: Request,
    session: Session = Depends(get_session),
    current_user: User | SubUser | None = Depends(get_current_user)
):
    if not current_user:
        response = RedirectResponse(url="/login", status_code=303)
        return handle_message(request, "Pro zobrazení nastavení se prosím přihlaste", MessageType.WARNING, response)
    
    # Získání vybrané firmy
    selected_firma_id = get_selected_firma_id(request, session, current_user)
    if not selected_firma_id:
        response = RedirectResponse(url="/firma", status_code=303)
        return handle_message(request, "Není vybrána aktivní firma", MessageType.DANGER, response)

    # Získání pokladen pro rozbalovací nabídku
    pokladny = session.exec(
        select(SetPokladna)
        .where(SetPokladna.firma_id == selected_firma_id)
    ).all()

    # Získání kontextu šablony
    context = get_template_context(request, session)
    context["title"] = "Přidat terminál"
    context["action"] = "/nastaveni-terminal/add"
    context["terminal"] = None
    context["pokladny"] = pokladny
    context["typ_prodeje_choices"] = [e.value for e in TypProdeje]
    return templates.TemplateResponse(
        "nastaveni/pokladna/terminal_form.html",
        context
    )

@router.post("/nastaveni-terminal/add", response_class=HTMLResponse)
async def add_terminal(
    request: Request,
    session: Session = Depends(get_session),
    current_user: User | SubUser | None = Depends(get_current_user)
):
    if not current_user:
        response = RedirectResponse(url="/login", status_code=303)
        return handle_message(request, "Pro úpravu nastavení se prosím přihlaste", MessageType.WARNING, response)
    
    is_htmx = request.headers.get("HX-Request") == "true"
    
    # Získání vybrané firmy
    firma_id = get_selected_firma_id(request, session, current_user)
    if firma_id is None:
        response = RedirectResponse(url="/firma", status_code=303)
        return handle_message(request, "Není vybrána aktivní firma", MessageType.DANGER, response)
    
    try:
        # Získání dat z formuláře
        form = await request.form()
        
        terminal = SetTerminal(
            nazev_terminalu=form.get("nazev_terminalu"),
            pokladna_id=int(form.get("pokladna_id")) if form.get("pokladna_id") else None,
            typ_prodeje=TypProdeje(form.get("typ_prodeje")),
            sparovano_pres_pin=form.get("sparovano_pres_pin") == "true",
            poznamka=form.get("poznamka", ""),
            firma_id=firma_id
        )
        session.add(terminal)
        session.commit()
        session.refresh(terminal)
        
        if is_htmx:
            response = templates.TemplateResponse(
                "nastaveni/pokladna/nastaveni-terminal_row.html",
                {
                    **get_template_context(request, session),
                    "terminal": terminal
                }
            )
            response.headers["HX-Trigger"] = json.dumps({
                "showMessage": {
                    "type": "success",
                    "message": "Terminál byl úspěšně přidán"
                },
                "reloadTerminaly": True
            })
            return response
        else:
            handle_message(request, "Terminál byl úspěšně přidán", MessageType.SUCCESS)
            return RedirectResponse(url="/nastaveni-pokladna", status_code=303)
            
    except Exception:
        error_message = "Chyba při přidávání terminálu"
        if is_htmx:
            response = Response(status_code=422)
            response.headers["HX-Trigger"] = json.dumps({
                "showMessage": {
                    "type": "danger",
                    "message": error_message
                }
            })
            return response
        else:
            handle_message(request, error_message, MessageType.DANGER)
            return RedirectResponse(url="/nastaveni-pokladna", status_code=303)

@router.get("/nastaveni-terminal/{terminal_id}/edit", response_class=HTMLResponse)
async def edit_terminal_form(
    request: Request,
    terminal_id: int,
    session: Session = Depends(get_session),
    current_user: User | SubUser | None = Depends(get_current_user)
):
    if not current_user:
        response = RedirectResponse(url="/login", status_code=303)
        return handle_message(request, "Pro zobrazení nastavení se prosím přihlaste", MessageType.WARNING, response)
    
    # Získání vybrané firmy
    selected_firma_id = get_selected_firma_id(request, session, current_user)
    if not selected_firma_id:
        response = RedirectResponse(url="/firma", status_code=303)
        return handle_message(request, "Není vybrána aktivní firma", MessageType.DANGER, response)

    # Získání terminálu
    terminal = session.get(SetTerminal, terminal_id)
    if not terminal:
        response = RedirectResponse(url="/nastaveni-pokladna", status_code=303)
        return handle_message(request, "Terminál nenalezen", MessageType.DANGER, response)
    
    # Kontrola, zda má uživatel přístup k firmě tohoto terminálu
    if terminal.firma_id != selected_firma_id:
        response = RedirectResponse(url="/nastaveni-pokladna", status_code=303)
        return handle_message(request, "Přístup odepřen", MessageType.DANGER, response)
    
    # Získání pokladen pro rozbalovací nabídku
    pokladny = session.exec(
        select(SetPokladna)
        .where(SetPokladna.firma_id == selected_firma_id)
    ).all()

    # Získání kontextu šablony
    context = get_template_context(request, session)
    context["title"] = "Upravit terminál"
    context["action"] = f"/nastaveni-terminal/{terminal_id}/edit"
    context["terminal"] = terminal
    context["pokladny"] = pokladny
    context["typ_prodeje_choices"] = [e.value for e in TypProdeje]
    return templates.TemplateResponse(
        "nastaveni/pokladna/terminal_form.html",
        context
    )

@router.delete("/nastaveni-pokladna/{pokladna_id}")
async def delete_pokladna(
    request: Request,
    pokladna_id: int,
    session: Session = Depends(get_session),
    current_user: User | SubUser | None = Depends(get_current_user)
):
    if not current_user:
        return RedirectResponse(url="/login", status_code=303)

    is_htmx = request.headers.get("HX-Request") == "true"
    
    try:
        # Získání a smazání pokladny
        pokladna = session.get(SetPokladna, pokladna_id)
        if not pokladna:
            error_message = "Pokladna nebyla nalezena"
            if is_htmx:
                response = Response(status_code=404)
                response.headers["HX-Trigger"] = json.dumps({
                    "showMessage": {
                        "type": "danger",
                        "message": error_message
                    }
                })
                return response
            else:
                handle_message(request, error_message, MessageType.DANGER)
                return RedirectResponse(url="/nastaveni-pokladna", status_code=303)

        session.delete(pokladna)
        session.commit()

        if is_htmx:
            response = Response(status_code=200)
            response.headers["HX-Trigger"] = json.dumps({
                "showMessage": {
                    "type": "success",
                    "message": "Pokladna byla úspěšně smazána"
                },
                "reloadPokladny": True
            })
            return response
        else:
            handle_message(request, "Pokladna byla úspěšně smazána", MessageType.SUCCESS)
            return RedirectResponse(url="/nastaveni-pokladna", status_code=303)

    except Exception:
        error_message = "Chyba při mazání pokladny"
        if is_htmx:
            response = Response(status_code=422)
            response.headers["HX-Trigger"] = json.dumps({
                "showMessage": {
                    "type": "danger",
                    "message": error_message
                }
            })
            return response
        else:
            handle_message(request, error_message, MessageType.DANGER)
            return RedirectResponse(url="/nastaveni-pokladna", status_code=303)

@router.delete("/nastaveni-terminal/{terminal_id}")
async def delete_terminal(
    request: Request,
    terminal_id: int,
    session: Session = Depends(get_session),
    current_user: User | SubUser | None = Depends(get_current_user)
):
    if not current_user:
        return RedirectResponse(url="/login", status_code=303)

    is_htmx = request.headers.get("HX-Request") == "true"
    
    try:
        # Získání a smazání terminálu
        terminal = session.get(SetTerminal, terminal_id)
        if not terminal:
            error_message = "Terminál nebyl nalezen"
            if is_htmx:
                response = Response(status_code=404)
                response.headers["HX-Trigger"] = json.dumps({
                    "showMessage": {
                        "type": "danger",
                        "message": error_message
                    }
                })
                return response
            else:
                handle_message(request, error_message, MessageType.DANGER)
                return RedirectResponse(url="/nastaveni-pokladna", status_code=303)

        session.delete(terminal)
        session.commit()

        if is_htmx:
            response = Response(status_code=200)
            response.headers["HX-Trigger"] = json.dumps({
                "showMessage": {
                    "type": "success",
                    "message": "Terminál byl úspěšně smazán"
                },
                "reloadTerminaly": True
            })
            return response
        else:
            handle_message(request, "Terminál byl úspěšně smazán", MessageType.SUCCESS)
            return RedirectResponse(url="/nastaveni-pokladna", status_code=303)

    except Exception:
        error_message = "Chyba při mazání terminálu"
        if is_htmx:
            response = Response(status_code=422)
            response.headers["HX-Trigger"] = json.dumps({
                "showMessage": {
                    "type": "danger",
                    "message": error_message
                }
            })
            return response
        else:
            handle_message(request, error_message, MessageType.DANGER)
            return RedirectResponse(url="/nastaveni-pokladna", status_code=303)

@router.post("/nastaveni-pokladna/update-cislovani")
async def update_cislovani(
    request: Request,
    session: Session = Depends(get_session),
    current_user: User | SubUser | None = Depends(get_current_user)
):
    if not current_user:
        return RedirectResponse(url="/login", status_code=303)

    selected_firma_id = get_selected_firma_id(request, session, current_user)
    if not selected_firma_id:
        raise HTTPException(status_code=400, detail="Není vybrána aktivní firma")

    # Získání dat z formuláře
    form = await request.form()
    
    # Získání nebo vytvoření nastavení číslovaní
    cislovani = session.exec(
        select(SetPokladnaCislovani)
        .where(SetPokladnaCislovani.firma_id == selected_firma_id)
    ).first()

    if cislovani:
        cislovani.format_cisla = form.get("format_cisla")
        cislovani.rok = int(form.get("rok"))
        cislovani.poradove_cislo = int(form.get("poradove_cislo"))
    else:
        cislovani = SetPokladnaCislovani(
            firma_id=selected_firma_id,
            format_cisla=form.get("format_cisla"),
            rok=int(form.get("rok")),
            poradove_cislo=int(form.get("poradove_cislo"))
        )

    session.add(cislovani)
    session.commit()

    handle_message(request, "Nastavení číslování bylo aktualizováno", MessageType.SUCCESS)
    return Response(status_code=200)
