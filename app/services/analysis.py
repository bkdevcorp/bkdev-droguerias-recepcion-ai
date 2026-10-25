from app.models.validation import day, rows, text, number

def analyze(payload):
    today = day(payload.get('as_of'))
    orders = {}
    for r in rows(payload.get('order')):
        sku = text(r.get('sku'),'sku')
        if sku in orders: raise ValueError('SKU duplicado en orden')
        orders[sku] = number(r.get('quantity'),'quantity',True)
    findings = []
    def add(code,message,source,severity='alta'):
        findings.append(dict(id=f'F{len(findings)+1}',code=code,message=message,source=source,severity=severity))
    received, seen, lots = {}, set(), {}
    receipt = rows(payload.get('receipt'))
    for index,r in enumerate(receipt,1):
        sku = text(r.get('sku'),'sku'); lot = text(r.get('lot'),'lot')
        qty = number(r.get('quantity'),'quantity',True)
        expiry = day(r.get('expiry'))
        source = f'receipt[{index}] / {sku} / lote {lot}'
        if (sku,lot) in seen: raise ValueError('Lote duplicado para el mismo SKU; consolidar antes de analizar')
        seen.add((sku,lot)); lots[(sku,lot)] = (expiry,source)
        received[sku] = received.get(sku,0)+qty
        if sku not in orders: add('UNEXPECTED_SKU',f'{sku}: producto fuera de la orden.',source)
        if expiry <= today: add('EXPIRED',f'{sku}/{lot}: vencido o vence en la fecha de revisión.',source,'critica')
        elif (expiry-today).days < 180: add('SHORT_SHELF_LIFE',f'{sku}/{lot}: vida útil menor al umbral de demo de 180 días.',source,'media')
    for sku,qty in orders.items():
        actual = received.get(sku,0)
        if actual != qty: add('QUANTITY_MISMATCH',f'{sku}: orden {qty}, recibido {actual}.',f'order/{sku} + receipt')
    docs = payload.get('documents')
    if not isinstance(docs,list) or len(docs)>2000: raise ValueError('documents debe ser una lista de hasta 2000 documentos')
    kinds=set(); certified=set()
    for index,doc in enumerate(docs,1):
        if not isinstance(doc,dict): raise ValueError('Documento inválido')
        kind=text(doc.get('type'),'type'); docid=text(doc.get('id'),'id'); kinds.add(kind)
        if kind=='certificate':
            sku=text(doc.get('sku'),'sku'); lot=text(doc.get('lot'),'lot'); expiry=day(doc.get('expiry'))
            key=(sku,lot)
            if key in certified: raise ValueError('Certificado duplicado para SKU y lote')
            certified.add(key)
            if key not in lots: add('ORPHAN_CERTIFICATE',f'{docid}: certificado sin lote recibido.',f'documents[{index}]/{docid}')
            elif lots[key][0] != expiry: add('EXPIRY_CONFLICT',f'{docid}: vencimiento distinto al declarado en recepción.',f'documents[{index}]/{docid} + {lots[key][1]}')
    for required in ['invoice','delivery_note']:
        if required not in kinds: add('MISSING_DOCUMENT',f'Falta documento: {required}.','documents')
    for key,(_,source) in lots.items():
        if key not in certified: add('MISSING_CERTIFICATE',f'Falta certificado para {key[0]}/{key[1]}.',source+' + documents')
    return {'title':'Revisión de recepción','as_of':today.isoformat(),
            'metrics':{'lineas':len(receipt),'observaciones':len(findings),'criticas':sum(f['severity']=='critica' for f in findings)},
            'findings':findings,'items':[], 'decision':'Requiere revisión del responsable'}
