// ===== DATOVÝ MODEL =====
const InvoiceModel = {
  // Datový model pro položky faktury
  items: [],
  
  // Nastavení faktury
  settings: {
    roundingType: 'ZAOKROUHLOVAT',
    paymentMethod: 'HOTOVE',
    invoiceDiscount: 0
  },
  
  // Inicializace modelu z existujících dat v DOM
  initialize() {
    this.settings.roundingType = document.getElementById('zaokrouhleni_typ')?.value || 'ZAOKROUHLOVAT';
    this.settings.paymentMethod = document.getElementById('zpusob_uhrady')?.value || '';
    
    // Inicializace slevy na fakturu
    const slevaNaFakturuElement = document.getElementById('sleva_na_fakturu');
    if (slevaNaFakturuElement) {
      this.settings.invoiceDiscount = parseFloat(slevaNaFakturuElement.textContent) || 0;
      
      // Pokud existuje sleva na fakturu, zobrazíme příslušné sekce
      if (this.settings.invoiceDiscount > 0) {
        const slevaInfoEl = document.getElementById('sleva-info');
        const slevaRadekEl = document.getElementById('sleva-radek');
        
        if (slevaInfoEl) {
          slevaInfoEl.classList.remove('d-none');
          slevaInfoEl.classList.add('d-block');
        }
        if (slevaRadekEl) {
          slevaRadekEl.classList.remove('d-none');
          slevaRadekEl.classList.add('d-block');
        }
        
        console.log("Inicializace - nalezena sleva na fakturu:", this.settings.invoiceDiscount);
      }
    }
    
    // Načtení existujících položek z DOM
    this.syncFromDOM();
    
    // Po načtení položek aktualizujeme celkové součty
    this.calculateTotals();
  },
  
  // Synchronizace modelu z DOM
  syncFromDOM() {
    // console.log("Synchronizace modelu s DOM - začátek");
    const rows = document.querySelectorAll('.polozka-item');
    // console.log("Počet položek v DOM:", rows.length);
    
    // Uložíme si původní počet položek v modelu pro porovnání
    const originalItemCount = this.items.length;
    // console.log("Původní počet položek v modelu:", originalItemCount);
    
    // Vytvoříme nové pole položek z DOM
    const newItems = Array.from(rows).map((row, index) => {
      // Extrahovat ID z row.id (polozka-X)
      const rowId = row.id.replace('polozka-', '');
      
      // Zkontrolovat, zda položka již existuje v modelu
      const existingItem = this.items.find(item => {
        const itemIdStr = item.id.toString();
        const rowIdStr = rowId.toString();
        return itemIdStr === rowIdStr;
      });
      
      // console.log(`Položka ${index} (DOM ID: ${rowId})`, existingItem ? `existuje v modelu s ID ${existingItem.id}` : "je nová");
      
      return {
        id: existingItem ? existingItem.id : Date.now() + parseInt(rowId || 0),
        name: row.querySelector('input[name$="[nazev]"]').value,
        quantity: parseFloat(row.querySelector('input[name$="[mnozstvi]"]').value) || 0,
        unitPrice: parseFloat(row.querySelector('input[name$="[cena_za_jednotku]"]').value) || 0,
        unit: row.querySelector('input[name$="[jednotka]"]')?.value || 'kus',
        vatRate: this.getVatRate(row),
        priceType: this.getPriceType(row),
        productId: row.querySelector('input[name$="[produkt_id]"]')?.value || null,
        warehouseId: row.querySelector('input[name$="[sklad_id]"]')?.value || null,
        trackInventory: row.querySelector('input[name$="[sledovat_sklad]"]')?.value === 'true',
        isSale: row.querySelector('input[name$="[its_sale]"]')?.value === 'true'
      };
    });
    
    // Nahradíme původní pole položek novým
    this.items = newItems;
    
    // Logování změn v počtu položek
    if (this.items.length !== originalItemCount) {
      // console.log(`Změna počtu položek: z ${originalItemCount} na ${this.items.length}`);
    }
    
    // Přepočítat ceny pro všechna položky
    this.items.forEach(item => this.calculateItemPrices(item));
    
    // console.log("Synchronizace modelu s DOM - dokončena, nový počet položek:", this.items.length);
    // console.log("Aktuální položky v modelu:", JSON.parse(JSON.stringify(this.items)));
  },
  
  // Pomocné metody pro získání hodnot z DOM
  getVatRate(row) {
    // Nejprve zkusit select, pak hidden input
    const select = row.querySelector('select[name$="[sazba_dph]"]');
    if (select && select.value) {
      return select.value;
    }
    
    const hidden = row.querySelector('input[type="hidden"][name$="[sazba_dph]"]');
    return hidden ? hidden.value : 'DPH_21';
  },
  
  getPriceType(row) {
    // Nejprve zkusit select, pak hidden input
    const select = row.querySelector('select[name$="[typ_ceny]"]');
    if (select && select.value) {
      return select.value;
    }
    
    const hidden = row.querySelector('input[type="hidden"][name$="[typ_ceny]"]');
    return hidden ? hidden.value : 's DPH';
  },
  
  // Přidat novou položku do modelu
  addItem(itemData) {
    const newItem = {
      id: Date.now(),
      name: itemData.name || '',
      quantity: parseFloat(itemData.quantity) || 0,
      unitPrice: parseFloat(itemData.unitPrice) || 0,
      unit: itemData.unit || 'kus',
      vatRate: itemData.vatRate || 'DPH_21',
      priceType: itemData.priceType || 's DPH',
      productId: itemData.productId || null,
      warehouseId: itemData.warehouseId || null,
      trackInventory: !!itemData.trackInventory,
      isSale: !!itemData.isSale
    };
    
    // Výpočet cen
    this.calculateItemPrices(newItem);
    
    // Přidání do pole
    this.items.push(newItem);
    
    return newItem;
  },
  
  // Aktualizovat existující položku
  updateItem(id, itemData) {
    const index = this.items.findIndex(item => item.id.toString() === id.toString());
    if (index === -1) return null;
    
    // Aktualizace dat
    Object.assign(this.items[index], itemData);
    
    // Přepočet cen
    this.calculateItemPrices(this.items[index]);
    
    return this.items[index];
  },
  
  // Odstranit položku
  removeItem(id) {
    const index = this.items.findIndex(item => item.id.toString() === id.toString());
    if (index === -1) return false;
    
    this.items.splice(index, 1);
    return true;
  },
  
  // Výpočet cen položky
  calculateItemPrices(item) {
    console.log("DEBUG - Položka:", item);
    console.log("DEBUG - Typ sazby DPH:", typeof item.vatRate, "Hodnota:", item.vatRate);
    
    // Extrahovat číselnou hodnotu sazby DPH - potřebujeme extrahovat číslo z "DPH_21"
    let vatValue = 0;
    if (typeof item.vatRate === 'string') {
      // Pokud je to řetězec ve formátu "DPH_21"
      const vatMatch = item.vatRate.match(/DPH_(\d+)/);
      if (vatMatch) {
        vatValue = parseFloat(vatMatch[1]) / 100;
      }
    } else if (typeof item.vatRate === 'number') {
      // Pokud je to číslo
      vatValue = item.vatRate / 100;
    }
    
    console.log(`Výpočet cen pro položku (${item.name}) se sazbou: ${item.vatRate}, hodnota: ${vatValue}`);
    
    // Výpočet cen podle typu ceny (s DPH nebo bez DPH)
    if (item.priceType === 's DPH') {
      item.priceWithVat = item.unitPrice;
      // Správný výpočet ceny bez DPH: cena s DPH / (1 + sazba DPH)
      item.priceWithoutVat = item.priceWithVat / (1 + vatValue);
    } else {
      item.priceWithoutVat = item.unitPrice;
      // Správný výpočet ceny s DPH: cena bez DPH * (1 + sazba DPH)
      item.priceWithVat = item.priceWithoutVat * (1 + vatValue);
    }
    
    // Výpočet celkových cen
    item.totalWithVat = item.priceWithVat * item.quantity;
    item.totalWithoutVat = item.priceWithoutVat * item.quantity;
    
    // Výpočet DPH
    item.vatAmount = item.totalWithVat - item.totalWithoutVat;
    
    console.log(`Vypočtené hodnoty: totalWithoutVat=${item.totalWithoutVat.toFixed(2)}, vatAmount=${item.vatAmount.toFixed(2)}, totalWithVat=${item.totalWithVat.toFixed(2)}`);
    
    // Zaokrouhlení na 2 desetinná místa pro přesnější výpočty
    item.priceWithVat = parseFloat(item.priceWithVat.toFixed(2));
    item.priceWithoutVat = parseFloat(item.priceWithoutVat.toFixed(2));
    item.totalWithVat = parseFloat(item.totalWithVat.toFixed(2));
    item.totalWithoutVat = parseFloat(item.totalWithoutVat.toFixed(2));
    item.vatAmount = parseFloat(item.vatAmount.toFixed(2));
    
    return item;
  },
  
  // Výpočet celkových součtů faktury
  calculateTotals() {
    console.log("Volána metoda calculateTotals");
    
    // Rozdělení položek na běžné a slevové
    const regularItems = this.items.filter(item => !item.isSale);
    const saleItems = this.items.filter(item => item.isSale);
    
    console.log("Položky:", {regularItems, saleItems});
    
    // Dynamicky získáme sazby DPH z položek faktury
    const vatRates = [...new Set(regularItems.map(item => item.vatRate.toString()))];
    console.log("Nalezeny sazby DPH:", vatRates);
    
    // Vytvoříme dynamicky objekty pro každou sazbu DPH
    const itemsByVat = {};
    vatRates.forEach(vatRate => {
      // Extrahujeme číselnou hodnotu ze sazby DPH_X pomocí regex
      const vatMatch = vatRate.match(/DPH_(\d+)/);
      const numericRate = vatMatch ? parseInt(vatMatch[1]) : 0;
      
      itemsByVat[numericRate] = { 
        items: [], 
        totalWithoutVat: 0, 
        totalVat: 0, 
        totalWithVat: 0,
        vatRate: numericRate
      };
    });
    
    console.log("Vytvořené skupiny podle DPH:", itemsByVat);
    
    // Přiřazení položek do správných skupin podle sazby DPH
    regularItems.forEach(item => {
      const vatRateStr = item.vatRate.toString();
      // Extrahujeme číselnou hodnotu ze sazby DPH_X pomocí regex
      const vatMatch = vatRateStr.match(/DPH_(\d+)/);
      const numericRate = vatMatch ? parseInt(vatMatch[1]) : 0;
      
      if (itemsByVat[numericRate]) {
        itemsByVat[numericRate].items.push(item);
        itemsByVat[numericRate].totalWithoutVat += item.totalWithoutVat;
        itemsByVat[numericRate].totalVat += item.vatAmount;
        itemsByVat[numericRate].totalWithVat += item.totalWithVat;
      } else {
        console.warn(`Nenalezena skupina pro sazbu ${vatRateStr} (${numericRate})`);
      }
    });
    
    // Zaokrouhlíme hodnoty na 2 desetinná místa
    Object.keys(itemsByVat).forEach(vatRate => {
      const group = itemsByVat[vatRate];
      group.totalWithoutVat = parseFloat(group.totalWithoutVat.toFixed(2));
      group.totalVat = parseFloat(group.totalVat.toFixed(2));
      group.totalWithVat = parseFloat(group.totalWithVat.toFixed(2));
    });
    
    // Celkové hodnoty před rozdělením slevy
    const totalWithoutVatBeforeDiscount = parseFloat(regularItems.reduce((sum, item) => sum + item.totalWithoutVat, 0).toFixed(2));
    const totalVatBeforeDiscount = parseFloat(regularItems.reduce((sum, item) => sum + item.vatAmount, 0).toFixed(2));
    const totalWithVatBeforeDiscount = parseFloat(regularItems.reduce((sum, item) => sum + item.totalWithVat, 0).toFixed(2));
    
    // Výpočet celkové slevy z položek
    const totalSaleAmount = parseFloat(Math.abs(saleItems.reduce((sum, item) => sum + item.totalWithVat, 0)).toFixed(2));
    
    // Cena před slevou (pro zobrazení)
    const priceBeforeDiscount = totalWithVatBeforeDiscount;
    
    // Rozdělení slevy na fakturu mezi sazby DPH
    let totalWithoutVatAfterDiscount = totalWithoutVatBeforeDiscount;
    let totalVatAfterDiscount = totalVatBeforeDiscount;
    let totalWithVatAfterDiscount = totalWithVatBeforeDiscount - totalSaleAmount;
    
    if (this.settings.invoiceDiscount > 0 && totalWithVatBeforeDiscount > 0) {
      // Rozdělení slevy mezi sazby podle poměru
      const totalInvoiceWithVat = totalWithVatBeforeDiscount;
      
      Object.keys(itemsByVat).forEach(vatRateKey => {
        const group = itemsByVat[vatRateKey];
        const vatRate = parseInt(vatRateKey); // Klíč je již číslo
        
        if (group.totalWithVat > 0) {
          // Poměr této sazby vůči celkové částce
          const ratio = group.totalWithVat / totalInvoiceWithVat;
          
          // Část slevy připadající na tuto sazbu
          const vatRateDiscount = this.settings.invoiceDiscount * ratio;
          
          if (vatRate === 0) {
            // Pro 0% DPH se celá sleva odečítá od základu
            group.totalWithoutVat -= vatRateDiscount;
            group.totalWithVat -= vatRateDiscount;
          } else {
            // Pro nenulové sazby DPH rozdělíme slevu mezi základ a DPH
            const vatRatio = vatRate / (100 + vatRate);
            const discountOnVat = vatRateDiscount * vatRatio;
            const discountOnBase = vatRateDiscount - discountOnVat;
            
            group.totalWithoutVat -= discountOnBase;
            group.totalVat -= discountOnVat;
            group.totalWithVat -= vatRateDiscount;
          }
        }
      });
      
      // Přepočet hodnot
      totalWithoutVatAfterDiscount = parseFloat(Object.values(itemsByVat).reduce((sum, group) => sum + group.totalWithoutVat, 0).toFixed(2));
      totalVatAfterDiscount = parseFloat(Object.values(itemsByVat).reduce((sum, group) => sum + group.totalVat, 0).toFixed(2));
      totalWithVatAfterDiscount = parseFloat(Object.values(itemsByVat).reduce((sum, group) => sum + group.totalWithVat, 0).toFixed(2));
    }
    
    // Celkové součty z jednotlivých skupin po aplikaci slev
    let totalWithoutVat = parseFloat(Object.values(itemsByVat).reduce((sum, group) => sum + group.totalWithoutVat, 0).toFixed(2));
    let totalVat = parseFloat(Object.values(itemsByVat).reduce((sum, group) => sum + group.totalVat, 0).toFixed(2));
    let totalWithVat = parseFloat(Object.values(itemsByVat).reduce((sum, group) => sum + group.totalWithVat, 0).toFixed(2));
    
    console.log("Sumy z vatBreakdown:", { totalWithoutVat, totalVat, totalWithVat });
    
    // Výpočet zaokrouhlení a finální celkové částky
    let roundingAmount = 0;
    let finalTotal = totalWithVat;
    
    if (this.settings.roundingType === 'ZAOKROUHLOVAT') {
      // Zaokrouhlení na celé koruny
      const roundedTotal = Math.round(totalWithVat);
      roundingAmount = parseFloat((roundedTotal - totalWithVat).toFixed(2));
      finalTotal = roundedTotal;
    } else if (this.settings.roundingType === 'ZAOKROUHLOVAT_NAHORU') {
      // Zaokrouhlení nahoru na celé koruny
      const roundedTotal = Math.ceil(totalWithVat);
      roundingAmount = parseFloat((roundedTotal - totalWithVat).toFixed(2));
      finalTotal = roundedTotal;
    } else if (this.settings.roundingType === 'ZAOKROUHLOVAT_DOLU') {
      // Zaokrouhlení dolů na celé koruny
      const roundedTotal = Math.floor(totalWithVat);
      roundingAmount = parseFloat((roundedTotal - totalWithVat).toFixed(2));
      finalTotal = roundedTotal;
    }
    
    finalTotal = parseFloat(finalTotal.toFixed(2));
    
    // Aplikace slevy na položky
    totalWithVatAfterDiscount = Math.max(0, totalWithVatAfterDiscount - totalSaleAmount);
    
    console.log("Finální součty:", {
      totalWithoutVat,
      totalVat,
      totalWithVat,
      totalSaleAmount,
      invoiceDiscount: this.settings.invoiceDiscount,
      roundingAmount,
      finalTotal,
      vatBreakdown: itemsByVat
    });
    
    return {
      totalWithoutVat, // Celková částka bez DPH
      totalVat,        // Celková částka DPH
      totalWithVat,    // Celková částka s DPH před zaokrouhlením
      totalSaleAmount, // Celková sleva na položkách
      invoiceDiscount: this.settings.invoiceDiscount, // Sleva na faktuře
      roundingAmount, // Hodnota zaokrouhlení 
      finalTotal,     // Finální částka s DPH po zaokrouhlení
      priceBeforeDiscount, // Cena před slevou (pro zobrazení)
      vatBreakdown: itemsByVat // Rozklad DPH podle sazeb
    };
  },
  
  // Nastavení slevy na fakturu
  setInvoiceDiscount(amount) {
    this.settings.invoiceDiscount = parseFloat(amount) || 0;
  },
  
  // Výpočet slevy podle typu (procento nebo částka)
  calculateDiscount(type, value, baseAmount) {
    if (type === 'procento') {
      // Omezení na max 100%
      const percentage = Math.min(parseFloat(value) || 0, 100);
      return baseAmount * percentage / 100;
    } else {
      // Omezení na max baseAmount
      return Math.min(parseFloat(value) || 0, baseAmount);
    }
  }
};

// ===== UI CONTROLLER =====
const InvoiceUI = {
  // Inicializace UI
  initialize() {
    // Nejprve se ujistíme, že model je inicializován
    InvoiceModel.initialize();
    
    // Aktualizace UI podle modelu
    this.updateTotals();
    
    // Nastavení modálních oken
    this.setupModals();
    
    // Přidání event listenerů
    this.addEventListeners();
    
    // Přidání event listenerů pro položky
    this.addItemChangeListeners();
    
    // console.log("InvoiceUI inicializován");
  },
  
  // Aktualizace celého UI podle modelu
  updateUI() {
    // Aktualizace zobrazení cen u všech položek
    InvoiceModel.items.forEach(item => {
      const itemElement = document.getElementById(`polozka-${item.id}`);
      if (itemElement) {
        this.updateItemPriceDisplay(itemElement);
      }
    });
    
    // Přidání event listenerů pro změny v položkách
    this.addItemChangeListeners();
    
    // Aktualizace celkových součtů
    this.updateTotals();
  },
  
  // Přidání event listenerů
  addEventListeners() {
    // Event listenery pro změny v položkách
    document.addEventListener('htmx:afterSwap', event => {
      if (event.detail.target.id === 'polozky-list' || event.detail.target.id.startsWith('polozka-')) {
        // console.log("HTMX afterSwap event - přeindexování a přepočítání cen");
        this.reindexItems();
        this.addItemChangeListeners();
        
        // Synchronizace modelu s DOM
        InvoiceModel.syncFromDOM();
        
        // Aktualizace UI
        this.updateTotals();
      }
    });
    
    // Event listener pro formulář
    const form = document.getElementById('invoice-form');
    if (form) {
      form.addEventListener('submit', this.handleFormSubmit.bind(this));
    }
    
    // Event listener pro zaokrouhlení a způsob úhrady
    const roundingSelect = document.getElementById('zaokrouhleni_typ');
    if (roundingSelect) {
      roundingSelect.addEventListener('change', () => {
        InvoiceModel.settings.roundingType = roundingSelect.value;
        this.updateTotals();
      });
    }
    
    const paymentMethodSelect = document.getElementById('zpusob_uhrady');
    if (paymentMethodSelect) {
      paymentMethodSelect.addEventListener('change', () => {
        InvoiceModel.settings.paymentMethod = paymentMethodSelect.value;
        this.updateTotals();
      });
    }
    
    // Event listener pro checkbox "uhrazeno"
    const paidCheckbox = document.getElementById('uhrazeno');
    if (paidCheckbox) {
      paidCheckbox.addEventListener('change', this.handlePaidStatusChange.bind(this));
    }
    
    // Event listener pro výběr banky
    const bankSelect = document.getElementById('banka_id');
    if (bankSelect) {
      bankSelect.addEventListener('change', () => this.updateBankDetails(bankSelect));
    }
  },
  
  // Přidání event listenerů pro položky
  addItemChangeListeners() {
    const items = document.querySelectorAll('.polozka-item');
    items.forEach(item => {
      // Sledování změn v množství
      const quantityInput = item.querySelector('input[name$="[mnozstvi]"]');
      if (quantityInput) {
        quantityInput.addEventListener('input', () => {
          this.handleItemChange(item);
        });
      }
      
      // Sledování změn v ceně za jednotku
      const priceInput = item.querySelector('input[name$="[cena_za_jednotku]"]');
      if (priceInput) {
        priceInput.addEventListener('input', () => {
          this.handleItemChange(item);
        });
      }
      
      // Sledování změn v typu ceny
      const priceTypeSelect = item.querySelector('select[name$="[typ_ceny]"]');
      if (priceTypeSelect) {
        priceTypeSelect.addEventListener('change', () => {
          this.handleItemChange(item);
        });
      }
      
      // Sledování změn v sazbě DPH
      const vatRateSelect = item.querySelector('select[name$="[sazba_dph]"]');
      if (vatRateSelect) {
        vatRateSelect.addEventListener('change', () => {
          this.handleItemChange(item);
        });
      }
    });
  },
  
  // Obsluha změny v položce
  handleItemChange(itemElement) {
    // Získat index položky v DOM
    const index = Array.from(document.querySelectorAll('.polozka-item')).indexOf(itemElement);
    
    // Aktualizovat data v modelu
    const updatedData = {
      name: itemElement.querySelector('input[name$="[nazev]"]').value,
      quantity: parseFloat(itemElement.querySelector('input[name$="[mnozstvi]"]').value) || 0,
      unitPrice: parseFloat(itemElement.querySelector('input[name$="[cena_za_jednotku]"]').value) || 0,
      vatRate: InvoiceModel.getVatRate(itemElement),
      priceType: InvoiceModel.getPriceType(itemElement)
    };
    
    // Ujistit se, že položka existuje v modelu
    if (index >= 0 && index < InvoiceModel.items.length) {
      // Aktualizovat model
      InvoiceModel.items[index] = {
        ...InvoiceModel.items[index],
        ...updatedData
      };
      
      // Přepočítat ceny položky
      InvoiceModel.calculateItemPrices(InvoiceModel.items[index]);
      
      // Aktualizovat zobrazení cen v položce
      this.updateItemPriceDisplay(itemElement);
      
      // Aktualizovat celkové součty
      this.updateTotals();
    } else {
      console.error('Položka nebyla nalezena v modelu podle indexu:', index);
    }
  },
  
  // Aktualizace zobrazení cen v položce
  updateItemPriceDisplay(itemElement) {
    // Aktualizace zobrazení cen - hledáme podle indexu v DOM
    const index = Array.from(document.querySelectorAll('.polozka-item')).indexOf(itemElement);
    
    // Ujistit se, že položka existuje v modelu
    if (index >= 0 && index < InvoiceModel.items.length) {
      const item = InvoiceModel.items[index];
      
      // Aktualizace zobrazení cen
      const bezDphElement = document.getElementById(`polozka-bez-dph-${index}`);
      const sDphElement = document.getElementById(`polozka-s-dph-${index}`);
      const totalElement = document.getElementById(`polozka-total-${index}`);
      
      // Oprava: bezDphElement by měl zobrazovat cenu bez DPH, ne totalWithoutVat
      // sDphElement by měl zobrazovat cenu s DPH, ne vatAmount
      if (bezDphElement) bezDphElement.textContent = item.totalWithoutVat.toFixed(2);
      if (sDphElement) sDphElement.textContent = item.totalWithVat.toFixed(2);
      if (totalElement) totalElement.textContent = item.totalWithVat.toFixed(2);
      
      // console.log('Aktualizace cen položky:', index, item);
      // console.log('Detaily výpočtu:', {
      //   quantity: item.quantity,
      //   unitPrice: item.unitPrice,
      //   priceType: item.priceType,
      //   vatRate: item.vatRate,
      //   priceWithVat: item.priceWithVat,
      //   priceWithoutVat: item.priceWithoutVat,
      //   totalWithVat: item.totalWithVat,
      //   totalWithoutVat: item.totalWithoutVat,
      //   vatAmount: item.vatAmount
      // });
    // } else {
      // console.error('Položka nebyla nalezena v modelu podle indexu:', index);
    }
  },
  
  // Aktualizace celkových součtů
  updateTotals() {
    console.log("Začátek metody updateTotals");
    
    // Nejprve synchronizujeme model s DOM, aby obsahoval aktuální položky
    InvoiceModel.syncFromDOM();
    
    // Nyní vypočítáme celkové součty
    const totals = InvoiceModel.calculateTotals();
    
    console.log("Celkové součty v updateTotals:", totals);
    
    // Získáme hodnoty pro zobrazení
    const currencyEl = document.getElementById('mena');
    const currency = currencyEl ? currencyEl.value : 'CZK';
    
    // Aktualizace zobrazení celkových součtů - používáme pouze primární elementy
    const bezDphEl = document.querySelector('#bez-dph-display');
    const celkemDphEl = document.querySelector('#celkem-dph-display');
    const celkemEl = document.getElementById('cena_celkem');
    const cenaPredSlevouEl = document.getElementById('cena_pred_slevou');
    const celkovaSlevaPolozkyEl = document.getElementById('celkova_sleva_na_polozky');
    const slevaDisplayEl = document.getElementById('sleva_display');
    const slevaInfoEl = document.getElementById('sleva-info');
    const slevaRadekEl = document.getElementById('sleva-radek');
    
    // Debugovací výpis
    console.log(`DOM Elementy: bezDphEl=${bezDphEl ? bezDphEl.id : "nenalezen"}, celkemDphEl=${celkemDphEl ? celkemDphEl.id : "nenalezen"}`);
    
    // Aktualizace hodnot v UI - použijeme try-catch pro odhalení chyb
    try {
      // Pokud hodnoty nejsou dostupné v totals, použijeme součty z vatBreakdown
      let bezDphHodnota = totals.totalWithoutVat;
      let celkemDphHodnota = totals.totalVat;
      
      // Pokud hodnoty nejsou platné, počítáme náhradní hodnoty
      if (isNaN(bezDphHodnota) || bezDphHodnota === undefined) {
        bezDphHodnota = Object.values(totals.vatBreakdown || {}).reduce((sum, group) => sum + (group.totalWithoutVat || 0), 0);
        console.log("Náhradní výpočet pro bezDphHodnota:", bezDphHodnota);
      }
      
      if (isNaN(celkemDphHodnota) || celkemDphHodnota === undefined) {
        celkemDphHodnota = Object.values(totals.vatBreakdown || {}).reduce((sum, group) => sum + (group.totalVat || 0), 0);
        console.log("Náhradní výpočet pro celkemDphHodnota:", celkemDphHodnota);
      }
      
      if (bezDphEl) {
        bezDphEl.textContent = bezDphHodnota.toFixed(2);
        console.log("Aktualizace bez DPH na:", bezDphHodnota.toFixed(2));
      }
      
      if (celkemDphEl) {
        celkemDphEl.textContent = celkemDphHodnota.toFixed(2);
        console.log("Aktualizace celkem DPH na:", celkemDphHodnota.toFixed(2));
      }
    } catch (error) {
      console.error("Chyba při aktualizaci hodnot DPH:", error);
    }
    
    // Aktualizace zaokrouhlení
    const zaokrouhleniElement = document.getElementById('zaokrouhleni');
    const zaokrouhleniDisplayElement = document.getElementById('zaokrouhleni_display');
    
    if (zaokrouhleniElement) zaokrouhleniElement.value = totals.roundingAmount.toFixed(2);
    if (zaokrouhleniDisplayElement) zaokrouhleniDisplayElement.textContent = totals.roundingAmount.toFixed(2);
    
    // Oprava celkové částky - použijeme součet všech celkových částek s DPH po aplikaci slev
    try {
      // Pro editaci potřebujeme správnou celkovou částku bez zaokrouhlení
      // Celková částka = Suma položek s DPH - Slevy na položky
      // Musíme odečíst slevy, protože už jsou zahrnuty v sumě položek
      const displayTotal = Object.values(totals.vatBreakdown || {}).reduce((sum, group) => sum + group.totalWithVat, 0);
      const finalDisplayTotal = displayTotal - totals.totalSaleAmount;
      
      if (celkemEl) {
        celkemEl.textContent = finalDisplayTotal.toFixed(2);
        console.log("Aktualizace celkem na:", finalDisplayTotal.toFixed(2), 
                    "(výpočet: celkemSDPH", displayTotal.toFixed(2), 
                    "- slevy na položky", totals.totalSaleAmount, ")");
      }
    } catch (error) {
      console.error("Chyba při aktualizaci celkové částky:", error);
    }
    
    // Aktualizace dalších hodnot
    if (cenaPredSlevouEl) cenaPredSlevouEl.textContent = totals.priceBeforeDiscount.toFixed(2);
    if (celkovaSlevaPolozkyEl) celkovaSlevaPolozkyEl.textContent = totals.totalSaleAmount.toFixed(2);
    if (slevaDisplayEl) slevaDisplayEl.textContent = (totals.totalSaleAmount + totals.invoiceDiscount).toFixed(2);
    
    // Zobrazit řádky se slevou, pokud je sleva větší než 0
    if (totals.totalSaleAmount > 0 || totals.invoiceDiscount > 0) {
      if (slevaInfoEl) {
        slevaInfoEl.classList.remove('d-none');
        slevaInfoEl.classList.add('d-block');
      }
      if (slevaRadekEl) {
        slevaRadekEl.classList.remove('d-none');
        slevaRadekEl.classList.add('d-block');
      }
    } else {
      if (slevaInfoEl) {
        slevaInfoEl.classList.remove('d-block');
        slevaInfoEl.classList.add('d-none');
      }
      if (slevaRadekEl) {
        slevaRadekEl.classList.remove('d-block');
        slevaRadekEl.classList.add('d-none');
      }
    }
    
    // Aktualizace skrytých polí pro formulář
    const celkemBezDphHidden = document.getElementById('cena_celkem_bez_dph_hidden');
    const zTohoDphHidden = document.getElementById('z_toho_dph_hidden');
    const celkemHidden = document.getElementById('cena_celkem_hidden');
    const slevaNaFakturuHidden = document.getElementById('sleva_na_fakturu_hidden');
    
    if (celkemBezDphHidden) celkemBezDphHidden.value = totals.totalWithoutVat.toFixed(2);
    if (zTohoDphHidden) zTohoDphHidden.value = totals.totalVat.toFixed(2);
    if (celkemHidden) celkemHidden.value = totals.finalTotal.toFixed(2);
    if (slevaNaFakturuHidden) slevaNaFakturuHidden.value = totals.invoiceDiscount.toFixed(2);
    
    // Vždy aktualizovat sleva_na_fakturu element
    const slevaNaFakturuEl = document.getElementById('sleva_na_fakturu');
    if (slevaNaFakturuEl) slevaNaFakturuEl.textContent = totals.invoiceDiscount.toFixed(2);
  },
  
  // Přeindexování položek v DOM
  reindexItems() {
    console.log("Přeindexování položek faktury - začátek");
    const items = document.querySelectorAll('.polozka-item');
    
    // Kompletně nová implementace přeindexování
    // Nejprve si uložíme všechna položky do pole, abychom mohli pracovat s indexy nezávisle na DOM
    const itemsArray = Array.from(items);
    
    console.log(`Přeindexování: Nalezeno ${itemsArray.length} položek v DOM`);
    
    // Procházíme všechna položky a nastavujeme jim nové indexy
    itemsArray.forEach((item, newIndex) => {
      // Získáme původní ID pro logging
      const originalId = item.id;
      console.log(`Přeindexování položky: ${originalId} -> polozka-${newIndex}`);
      
      // Nastavíme správný index
      // Nastavení ID položky
      item.id = `polozka-${newIndex}`;
      
      // Nastavení data-index atributu pro tlačítka
      const deleteButton = item.querySelector('button[onclick*="removeInvoiceItem"]');
      if (deleteButton) {
        deleteButton.setAttribute('data-index', newIndex.toString());
      }
      
      // Aktualizace data-index atributu pro tlačítka slevy
      const discountButton = item.querySelector('.sleva-polozka-btn');
      if (discountButton) {
        console.log(`Aktualizace data-index pro tlačítko slevy na položce ${originalId} na ${newIndex}`);
        discountButton.setAttribute('data-index', newIndex.toString());
      }
      
      // Aktualizace názvů vstupních polí
      const inputs = item.querySelectorAll('input, select');
      inputs.forEach(input => {
        if (input.name) {
          const newName = input.name.replace(/polozky\[\d+\]/, `polozky[${newIndex}]`);
          if (newName !== input.name) {
            input.name = newName;
          }
        }
      });
    });
    
    console.log(`Přeindexování položek faktury - dokončeno, přeindexováno ${itemsArray.length} položek`);
  },
  
  // Obsluha změny stavu "uhrazeno"
  handlePaidStatusChange(event) {
    const isChecked = event.target.checked;
    const datumPlatyContainer = document.getElementById('datum_platby').closest('.mb-3');
    
    if (isChecked) {
      datumPlatyContainer.classList.remove('visually-hidden');
      // Změna textu a barvy na "Faktura je zaplacená" (zelená)
      const statusElement = document.querySelector('h4.text-success, h4.text-danger');
      if (statusElement) {
        statusElement.textContent = 'Faktura je zaplacená';
        statusElement.classList.remove('text-danger');
        statusElement.classList.add('text-success');
      }
    } else {
      datumPlatyContainer.classList.add('visually-hidden');
      // Změna textu a barvy na "Faktura není zaplacená" (červená)
      const statusElement = document.querySelector('h4.text-success, h4.text-danger');
      if (statusElement) {
        statusElement.textContent = 'Faktura není zaplacená';
        statusElement.classList.remove('text-success');
        statusElement.classList.add('text-danger');
      }
    }
  },
  
  // Aktualizace bankovních údajů
  updateBankDetails(select) {
    if (!select.value) {
      // Clear all fields if no bank is selected
      document.getElementById('nazev_uctu').value = '';
      document.getElementById('bankovni_ucet').value = '';
      document.getElementById('iban').value = '';
      document.getElementById('swift').value = '';
      return;
    }

    const option = select.options[select.selectedIndex];
    
    // Update the form fields with the selected bank's details
    document.getElementById('nazev_uctu').value = option.dataset.nazev;
    document.getElementById('bankovni_ucet').value = option.dataset.ucet + '/' + option.dataset.kod;
    document.getElementById('iban').value = option.dataset.iban;
    document.getElementById('swift').value = option.dataset.swift;
  },
  
  // Validace formuláře před odesláním
  handleFormSubmit(event) {
    // Synchronizace modelu s DOM před odesláním
    InvoiceModel.syncFromDOM();
    
    // Validace dat
    if (InvoiceModel.items.length === 0) {
      this.showToast('Chyba', 'Přidejte alespoň jednu položku na fakturu', 'danger');
      event.preventDefault();
      return false;
    }
    
    // Validace požadovaných polí v položkách
    let valid = true;
    InvoiceModel.items.forEach((item, index) => {
      // Pro slevové položky povolíme zápornou cenu
      if (!item.name || item.quantity <= 0 || (item.unitPrice === 0 || (item.unitPrice < 0 && !item.isSale))) {
        valid = false;
        this.showToast('Chyba', `Položka ${index + 1} má neplatné hodnoty`, 'danger');
      }
    });
    
    if (!valid) {
      event.preventDefault();
      return false;
    }
    
    return true;
  },
  
  // Zobrazení toast notifikace
  showToast(title, message, type = 'success') {
    const toastContainer = document.getElementById('toast-container');
    if (!toastContainer) return;
    
    const toastEl = document.createElement('div');
    toastEl.className = `toast align-items-center text-white bg-${type} border-0`;
    toastEl.setAttribute('role', 'alert');
    toastEl.setAttribute('aria-live', 'assertive');
    toastEl.setAttribute('aria-atomic', 'true');
    
    toastEl.innerHTML = `
      <div class="d-flex">
        <div class="toast-body">
          <strong>${title}</strong>: ${message}
        </div>
        <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
      </div>
    `;
    
    toastContainer.appendChild(toastEl);
    const toast = new bootstrap.Toast(toastEl);
    toast.show();
    
    // Automatické odstranění toastu po zavření
    toastEl.addEventListener('hidden.bs.toast', function() {
      toastEl.remove();
    });
  },
  
  // Nastavení modálních oken
  setupModals() {
    // Modál pro slevu na položku
    this.setupItemDiscountModal();
    
    // Modál pro slevu na fakturu
    this.setupInvoiceDiscountModal();
    
    // Modál pro výběr kontaktu
    this.setupContactSelectModal();
    
    // Modál pro výběr produktu
    this.setupProductSelectModal();
  },
  
  // Nastavení modálu pro slevu na položku
  setupItemDiscountModal() {
    // console.log("Inicializace modálu pro slevu na položku");
    const modal = document.getElementById('polozka-sleva-modal');
    if (!modal) {
      console.error("Modál pro slevu na položku nebyl nalezen");
      return;
    }
    
    // Event listener pro otevření modálu
    modal.addEventListener('show.bs.modal', event => {
      // console.log("Otevření modálu pro slevu na položku", event);
      const button = event.relatedTarget;
      if (!button) {
        console.error("Tlačítko, které otevřelo modál, nebylo nalezeno");
        return;
      }
      
      const polozkaIndex = parseInt(button.getAttribute('data-index'));
      // console.log("Index položky pro slevu:", polozkaIndex);
      if (isNaN(polozkaIndex)) {
        console.error("Index položky nebyl nalezen v atributu data-index");
        return;
      }
      
      // Nastavení indexu položky do skrytého pole
      document.getElementById('sleva-polozka-id').value = polozkaIndex;
      
      // Reset hodnot
      document.getElementById('polozka-sleva-hodnota').value = "0";
      document.getElementById('polozka-sleva-typ').value = "procento";
      
      // Aktualizace informačního textu
      this.updateItemDiscountInfoText();
    });
    
    // Event listener pro změnu typu slevy
    const slevaTypSelect = document.getElementById('polozka-sleva-typ');
    if (slevaTypSelect) {
      // console.log("Přidávám event listener pro změnu typu slevy");
      slevaTypSelect.addEventListener('change', () => {
        // console.log("Změna typu slevy");
        this.updateItemDiscountInfoText();
      });
    } else {
      console.error("Element pro výběr typu slevy nebyl nalezen");
    }
    
    // Event listener pro změnu hodnoty slevy
    const slevaHodnotaInput = document.getElementById('polozka-sleva-hodnota');
    if (slevaHodnotaInput) {
      // console.log("Přidávám event listener pro změnu hodnoty slevy");
      slevaHodnotaInput.addEventListener('input', () => {
        // console.log("Změna hodnoty slevy");
        this.updateItemDiscountInfoText();
      });
    } else {
      console.error("Element pro zadání hodnoty slevy nebyl nalezen");
    }
    
    // Event listener pro tlačítko "Přidat slevu"
    const addDiscountButton = document.getElementById('polozka-sleva-potvrdit');
    if (addDiscountButton) {
      // console.log("Přidávám event listener pro tlačítko Potvrdit slevu");
      addDiscountButton.addEventListener('click', () => {
        // console.log("Kliknutí na tlačítko Potvrdit slevu");
        this.addItemDiscount();
      });
    } else {
      console.error("Tlačítko pro potvrzení slevy nebylo nalezeno");
    }
  },
  
  // Aktualizace informačního textu o slevě na položku
  updateItemDiscountInfoText() {
    // console.log("Aktualizace informačního textu o slevě na položku");
    const polozkaIndex = document.getElementById('sleva-polozka-id').value;
    const slevaTyp = document.getElementById('polozka-sleva-typ').value;
    const slevaHodnota = parseFloat(document.getElementById('polozka-sleva-hodnota').value) || 0;
    
    // console.log("Hodnoty pro informační text:", { polozkaIndex, slevaTyp, slevaHodnota });
    
    // Získání položky z DOM podle indexu
    const rows = document.querySelectorAll('.polozka-item');
    if (polozkaIndex < 0 || polozkaIndex >= rows.length) {
      // console.error("Index položky je mimo rozsah:", polozkaIndex, "počet položek:", rows.length);
      return;
    }
    
    const polozkaRow = rows[polozkaIndex];
    if (!polozkaRow) {
      // console.error("Položka s indexem", polozkaIndex, "nebyla nalezena v DOM");
      return;
    }
    
    // Získání názvu položky
    const nazevInput = polozkaRow.querySelector('input[name$="[nazev]"]');
    if (!nazevInput) {
      // console.error("Input pro název položky nebyl nalezen");
      return;
    }
    const nazev = nazevInput.value;
    
    // Získání položky z modelu podle indexu
    if (polozkaIndex < 0 || polozkaIndex >= InvoiceModel.items.length) {
      // console.error("Index položky je mimo rozsah modelu:", polozkaIndex, "počet položek v modelu:", InvoiceModel.items.length);
      return;
    }
    
    const item = InvoiceModel.items[polozkaIndex];
    if (!item) {
      console.error("Položka s indexem", polozkaIndex, "nebyla nalezena v modelu");
      return;
    }
    
    // Výpočet slevy
    const baseAmount = item.totalWithVat;
    let slevaTexturCastka = 0;
    
    if (slevaTyp === 'procento') {
      // Omezení na max 100%
      const percentage = Math.min(parseFloat(slevaHodnota) || 0, 100);
      slevaTexturCastka = baseAmount * percentage / 100;
      document.getElementById('polozka-sleva-info-text').innerHTML = 
        `Sleva ${percentage}% na položku "${nazev}" činí ${slevaTexturCastka.toFixed(2)} Kč`;
    } else {
      // Omezení na max cenu položky
      let hodnota = slevaHodnota;
      if (hodnota > baseAmount) {
        document.getElementById('polozka-sleva-hodnota').value = baseAmount.toFixed(2);
        hodnota = baseAmount;
      }
      
      document.getElementById('polozka-sleva-info-text').innerHTML = 
        `Sleva ${hodnota.toFixed(2)} Kč na položku "${nazev}"`;
    }
    
    // console.log("Informační text aktualizován");
  },
  
  // Přidání slevy na položku
  addItemDiscount() {
    // console.log("Volání funkce addItemDiscount");
    const polozkaIndex = document.getElementById('sleva-polozka-id').value;
    const slevaTyp = document.getElementById('polozka-sleva-typ').value;
    const slevaHodnota = parseFloat(document.getElementById('polozka-sleva-hodnota').value) || 0;
    
    // console.log("Hodnoty pro slevu:", { polozkaIndex, slevaTyp, slevaHodnota });
    
    // Získání položky z DOM
    const rows = document.querySelectorAll('.polozka-item');
    if (polozkaIndex < 0 || polozkaIndex >= rows.length) {
      // console.error("Index položky je mimo rozsah:", polozkaIndex, "počet položek:", rows.length);
      this.showToast('Chyba', 'Položka pro slevu nebyla nalezena.', 'danger');
      return;
    }
    
    const polozkaRow = rows[polozkaIndex];
    if (!polozkaRow) {
      console.error("Položka s indexem", polozkaIndex, "nebyla nalezena v DOM");
      this.showToast('Chyba', 'Položka pro slevu nebyla nalezena.', 'danger');
      return;
    }
    
    // Získání položky z modelu
    if (polozkaIndex < 0 || polozkaIndex >= InvoiceModel.items.length) {
      console.error("Index položky je mimo rozsah modelu:", polozkaIndex, "počet položek v modelu:", InvoiceModel.items.length);
      this.showToast('Chyba', 'Položka pro slevu nebyla nalezena v modelu.', 'danger');
      return;
    }
    
    const item = InvoiceModel.items[polozkaIndex];
    if (!item) {
      console.error("Položka s indexem", polozkaIndex, "nebyla nalezena v modelu");
      this.showToast('Chyba', 'Položka pro slevu nebyla nalezena v modelu.', 'danger');
      return;
    }
    
    // Výpočet slevy
    const baseAmount = item.totalWithVat;
    const discountAmount = InvoiceModel.calculateDiscount(slevaTyp, slevaHodnota, baseAmount);
    
    // Najdeme a klikneme na tlačítko pro přidání položky
    const addButton = document.querySelector('button[hx-get="/polozky/add-form"]');
    if (addButton) {
      // Simulujeme kliknutí na tlačítko
      addButton.click();
      
      // Počkáme chvíli, aby se DOM aktualizoval
      setTimeout(() => {
        // Najdeme poslední řádek v tabulce
        const rows = document.querySelectorAll('.polozka-item');
        const newRow = rows[rows.length - 1];
        
        if (newRow) {
          // Vyplníme hodnoty slevy
          const nazevInput = newRow.querySelector('input[name$="[nazev]"]');
          const cenaInput = newRow.querySelector('input[name$="[cena_za_jednotku]"]');
          const typCenySelect = newRow.querySelector('select[name$="[typ_ceny]"]');
          const sazbaDphSelect = newRow.querySelector('select[name$="[sazba_dph]"]');
          const itsSaleInput = newRow.querySelector('input[name$="[its_sale]"]');
          
          if (nazevInput) nazevInput.value = `Sleva na ${item.name}`;
          if (cenaInput) cenaInput.value = (-discountAmount).toFixed(2);
          if (typCenySelect) typCenySelect.value = item.priceType;
          if (sazbaDphSelect) sazbaDphSelect.value = item.vatRate;
          if (itsSaleInput) itsSaleInput.value = "true"; // Označíme položku jako slevu
          
          // Skryjeme tlačítko pro slevu na slevovém řádku
          const slevaBtn = newRow.querySelector('.sleva-polozka-btn');
          if (slevaBtn) slevaBtn.style.display = 'none';
          
          // Přeindexujeme položky a aktualizujeme model a UI
          this.reindexItems();
          InvoiceModel.syncFromDOM();
          this.updateTotals();
        }
        
        // Zavřeme modální okno
        const closeButton = document.querySelector('#polozka-sleva-modal [data-bs-dismiss="modal"]');
        if (closeButton) {
          closeButton.click();
        } else {
          const modal = bootstrap.Modal.getInstance(document.getElementById('polozka-sleva-modal'));
          if (modal) {
            modal.hide();
          }
        }
      }, 200);
    } else {
      console.error("Tlačítko pro přidání položky nebylo nalezeno");
      this.showToast('Chyba', 'Nelze přidat slevovou položku.', 'danger');
    }
  },
  
  // Nastavení modálu pro slevu na fakturu
  setupInvoiceDiscountModal() {
    const modal = document.getElementById('sleva-na-fakturu-modal');
    if (!modal) return;
    
    // Event listener pro otevření modálu
    modal.addEventListener('show.bs.modal', () => {
      // Reset hodnot
      document.getElementById('faktura-sleva-hodnota').value = "0";
      document.getElementById('faktura-sleva-typ').value = "procento";
      
      // Aktualizace informačního textu
      this.updateInvoiceDiscountInfoText();
    });
    
    // Event listener pro změnu typu slevy
    const slevaTypSelect = document.getElementById('faktura-sleva-typ');
    if (slevaTypSelect) {
      slevaTypSelect.addEventListener('change', this.updateInvoiceDiscountInfoText.bind(this));
    }
    
    // Event listener pro změnu hodnoty slevy
    const slevaHodnotaInput = document.getElementById('faktura-sleva-hodnota');
    if (slevaHodnotaInput) {
      slevaHodnotaInput.addEventListener('input', this.updateInvoiceDiscountInfoText.bind(this));
    }
    
    // Event listener pro tlačítko "Přidat slevu"
    const addDiscountButton = document.getElementById('faktura-sleva-potvrdit');
    if (addDiscountButton) {
      addDiscountButton.addEventListener('click', this.addInvoiceDiscount.bind(this));
    }
  },
  
  // Aktualizace informačního textu o slevě na fakturu
  updateInvoiceDiscountInfoText() {
    const slevaTyp = document.getElementById('faktura-sleva-typ').value;
    const slevaHodnota = parseFloat(document.getElementById('faktura-sleva-hodnota').value) || 0;
    
    // Získáme celkovou cenu (bez slevových položek)
    const regularItems = InvoiceModel.items.filter(item => !item.isSale);
    const totalWithVat = regularItems.reduce((sum, item) => sum + item.totalWithVat, 0);
    
    // Výpočet slevy
    let slevaTexturCastka = 0;
    if (slevaTyp === 'procento') {
      // Omezení na max 100%
      const percentage = Math.min(parseFloat(slevaHodnota) || 0, 100);
      slevaTexturCastka = totalWithVat * percentage / 100;
      document.getElementById('faktura-sleva-info-text').innerHTML = 
        `Sleva ${percentage}% na fakturu činí ${slevaTexturCastka.toFixed(2)} Kč`;
    } else {
      // Omezení na max cenu faktury
      let hodnota = slevaHodnota;
      if (hodnota > totalWithVat) {
        document.getElementById('faktura-sleva-hodnota').value = totalWithVat.toFixed(2);
        hodnota = totalWithVat;
      }
      
      document.getElementById('faktura-sleva-info-text').innerHTML = 
        `Sleva ${hodnota.toFixed(2)} Kč na fakturu`;
    }
  },
  
  // Přidání slevy na fakturu
  addInvoiceDiscount() {
    const slevaTyp = document.getElementById('faktura-sleva-typ').value;
    const slevaHodnota = parseFloat(document.getElementById('faktura-sleva-hodnota').value) || 0;
    
    // Získáme celkovou cenu (bez slevových položek)
    const regularItems = InvoiceModel.items.filter(item => !item.isSale);
    const totalWithVat = regularItems.reduce((sum, item) => sum + item.totalWithVat, 0);
    
    // Výpočet slevy
    const discountAmount = InvoiceModel.calculateDiscount(slevaTyp, slevaHodnota, totalWithVat);
    
    // Nastavení slevy v modelu
    InvoiceModel.setInvoiceDiscount(discountAmount);
    
    // Aktualizace skrytého input pole pro slevu na fakturu (pro formulář)
    const slevaNaFakturuHidden = document.getElementById('sleva_na_fakturu_hidden');
    if (slevaNaFakturuHidden) {
      slevaNaFakturuHidden.value = discountAmount.toFixed(2);
    }
    
    // Aktualizace zobrazení slevy
    const slevaEl = document.getElementById('sleva_na_fakturu');
    if (slevaEl) {
      slevaEl.textContent = discountAmount.toFixed(2);
      slevaEl.setAttribute('data-value', discountAmount.toFixed(2));
    }
    
    // Aktualizace celkových cen
    this.updateTotals();
    
    // Zavření modálního okna
    const closeButton = document.querySelector('#sleva-na-fakturu-modal [data-bs-dismiss="modal"]');
    if (closeButton) {
      closeButton.click();
    } else {
      const modal = bootstrap.Modal.getInstance(document.getElementById('sleva-na-fakturu-modal'));
      if (modal) {
        modal.hide();
      }
    }
    
    // Zobrazit řádky se slevou, pokud je sleva větší než 0
    if (discountAmount > 0) {
      const slevaInfoEl = document.getElementById('sleva-info');
      const slevaRadekEl = document.getElementById('sleva-radek');
      
      if (slevaInfoEl) {
        slevaInfoEl.classList.remove('d-none');
        slevaInfoEl.classList.add('d-block');
      }
      if (slevaRadekEl) {
        slevaRadekEl.classList.remove('d-none');
        slevaRadekEl.classList.add('d-block');
      }
    }
  },
  
  // Nastavení modálu pro výběr kontaktu
  setupContactSelectModal() {
    // Funkce pro otevření modálního okna pro výběr kontaktu
    window.openContactSelectModal = async function() {
      try {
        // Načíst obsah modálního okna
        const response = await fetch('/kontakty/select-modal');
        const html = await response.text();
        
        // Naplnit kontejner obsahem
        document.getElementById('contactModalContainer').innerHTML = html;
        htmx.process(document.getElementById('contactModalContainer'));
        
        // Otevřít modální okno
        const modal = new bootstrap.Modal(document.getElementById('contactSelectModal'));
        modal.show();
      } catch (error) {
        console.error('Chyba při načítání modálního okna:', error);
      }
    };
    
    // Funkce pro výběr kontaktu
    window.selectContact = function(nazev, ulice, mesto, psc, zeme, ico, dic, email, telefon) {
      document.getElementById('odberatel_nazev').value = nazev;
      document.getElementById('odberatel_ulice').value = ulice;
      document.getElementById('odberatel_mesto').value = mesto;
      document.getElementById('odberatel_psc').value = psc;
      
      // Nastavení země v selectu - důležité použít jak .value, tak .selectedIndex pro spolehlivost
      const zemeSelect = document.getElementById('odberatel_zeme');
      
      // Nejprve zkusit přímo nastavit value
      zemeSelect.value = zeme;
      
      // Pokud to nefunguje, najít manuálně správnou option
      if (zemeSelect.selectedIndex === -1) {
        for (let i = 0; i < zemeSelect.options.length; i++) {
          if (zemeSelect.options[i].value === zeme) {
            zemeSelect.selectedIndex = i;
            break;
          }
        }
      }
      
      document.getElementById('odberatel_ico').value = ico;
      document.getElementById('odberatel_dic').value = dic || '';
      document.getElementById('odberatel_email').value = email || '';
      document.getElementById('odberatel_telefon').value = telefon || '';
      
      // Spustit funkci pro změnu země po aktualizaci hodnoty
      if (typeof handleCountryChange === 'function' && zemeSelect) {
        handleCountryChange(zemeSelect);
      }
    };
  },
  
  // Nastavení modálu pro výběr produktu
  setupProductSelectModal() {
    // Funkce pro otevření modálního okna pro výběr produktu
    window.openProduktSelectModal = async function() {
      try {
        // Načíst obsah modálního okna
        const response = await fetch('/polozky/add-from-selectableprodukt');
        const html = await response.text();
        
        // Naplnit kontejner obsahem
        document.getElementById('modalContainer').innerHTML = html;
        htmx.process(document.getElementById('modalContainer'));
        
        // Otevřít modální okno
        const modal = new bootstrap.Modal(document.getElementById('produktSelectModal'));
        modal.show();
      } catch (error) {
        console.error('Chyba při načítání modálního okna:', error);
      }
    };
  },
};

// Globální funkce pro mazání položek
function removeInvoiceItem(index) {
  console.log(`Požadavek na odstranění položky s indexem: ${index}`);
  
  // Nejprve aktualizujeme indexy všech položek pro zajištění konzistence
  InvoiceUI.reindexItems();
  
  // Najít položku v DOM přímo podle data-index atributu, který je spolehlivější než ID
  const allItems = document.querySelectorAll('.polozka-item');
  
  // Pro jistotu zkontrolujeme konzistenci DOM
  if (index >= allItems.length) {
    console.error(`Index položky ${index} je mimo rozsah (celkem položek: ${allItems.length})`);
    alert('Chyba při mazání položky: neplatný index. Zkuste stránku obnovit.');
    return;
  }
  
  // Pokud máme konzistentní indexy, měli bychom moci přímo použít index
  const itemToRemove = allItems[index];
  
  if (!itemToRemove) {
    console.error(`Položka s indexem ${index} nebyla nalezena v DOM`);
    alert('Chyba při mazání položky: položka nebyla nalezena. Zkuste stránku obnovit.');
    return;
  }
  
  console.log(`Nalezena položka k odstranění: ${itemToRemove.id}, aktuální index: ${index}`);
  
  // Potvrzení od uživatele
  if (!confirm('Opravdu chcete smazat tuto položku?')) {
    return;
  }
  
  // Odstranit položku z DOM
  itemToRemove.remove();
  
  // Synchronizace modelu s DOM
  InvoiceModel.syncFromDOM();
  
  // Přeindexování položek a aktualizace UI
  InvoiceUI.reindexItems();
  InvoiceUI.updateTotals();
}

// Původní implementace mazání položek (pro zálohu)
function _OLD_removeInvoiceItem(index) {
  let itemToRemove = null;
  
  // Projdeme všechna položky a najdeme tu, která má správný data-index atribut
  const allItems = document.querySelectorAll('.polozka-item');
  for (const item of allItems) {
    const deleteButton = item.querySelector('button[onclick*="removeInvoiceItem"]');
    if (deleteButton && parseInt(deleteButton.getAttribute('data-index'), 10) === index) {
      itemToRemove = item;
      break;
    }
  }
  
  if (!itemToRemove) {
    console.error('Položka s indexem', index, 'nebyla nalezena v DOM');
    return;
  }
  
  // Potvrzení od uživatele
  if (!confirm('Opravdu chcete smazat tuto položku?')) {
    return;
  }
  
  // Odstranit položku z DOM
  itemToRemove.remove();
  
  // Synchronizace modelu s DOM
  InvoiceModel.syncFromDOM();
  
  // Přeindexování položek
  InvoiceUI.reindexItems();
  
  // Aktualizace UI
  InvoiceUI.updateTotals();
  
  // console.log('Položka byla odstraněna a ceny byly přepočítány');
}

// Globální funkce pro aktualizaci slevy na fakturu
function updateInvoiceDiscount(amount) {
  // Převod na číslo a zaokrouhlení na 2 desetinná místa
  const discountAmount = parseFloat(parseFloat(amount).toFixed(2));
  
  // Aktualizace modelu
  InvoiceModel.settings.invoiceDiscount = discountAmount;
  
  // Aktualizace zobrazení
  const slevaNaFakturuEl = document.getElementById('sleva_na_fakturu');
  if (slevaNaFakturuEl) slevaNaFakturuEl.textContent = discountAmount.toFixed(2);
  
  // Aktualizace skrytého pole pro formulář
  const slevaNaFakturuHidden = document.getElementById('sleva_na_fakturu_hidden');
  if (slevaNaFakturuHidden) slevaNaFakturuHidden.value = discountAmount.toFixed(2);
  
  // Přepočet celkových součtů
  InvoiceUI.updateTotals();
  
  // Zobrazit řádky se slevou, pokud je sleva větší než 0
  if (discountAmount > 0) {
    const slevaInfoEl = document.getElementById('sleva-info');
    const slevaRadekEl = document.getElementById('sleva-radek');
    
    if (slevaInfoEl) {
      slevaInfoEl.classList.remove('d-none');
      slevaInfoEl.classList.add('d-block');
    }
    if (slevaRadekEl) {
      slevaRadekEl.classList.remove('d-none');
      slevaRadekEl.classList.add('d-block');
    }
  }
  
  // console.log("Sleva na fakturu aktualizována:", discountAmount);
}

// ===== INICIALIZACE =====
document.addEventListener('DOMContentLoaded', function() {
  // console.log("DOMContentLoaded - inicializace Invoice modelu a UI");
  
  // Inicializace modelu
  InvoiceModel.initialize();
  
  // Okamžitě aktualizujeme zobrazení celkových součtů
  InvoiceUI.updateTotals();
  
  // Nastavení event listenerů pro položky faktury
  InvoiceUI.initialize();
  
  // Inicializace bankovních údajů
  const bankSelect = document.getElementById('banka_id');
  if (bankSelect && bankSelect.value) {
    InvoiceUI.updateBankDetails(bankSelect);
  }
  
  // Globální event listener pro HTMX události
  document.body.addEventListener('htmx:afterRequest', function(event) {
    // Kontrola, zda se jedná o smazání položky
    if (event.detail.requestConfig.method === 'DELETE' && event.detail.requestConfig.path.startsWith('/polozky/')) {
      // console.log('HTMX afterRequest - smazání položky detekováno');
      
      // Počkáme chvíli, aby se DOM aktualizoval
      setTimeout(function() {
        // Synchronizace modelu s DOM
        InvoiceModel.syncFromDOM();
        
        // Přeindexování položek
        InvoiceUI.reindexItems();
        
        // Aktualizace UI
        InvoiceUI.updateTotals();
        
        // console.log('Ceny byly přepočítány po smazání položky (globální handler)');
      }, 500);
    }
  });
});