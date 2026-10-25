"""Extracción asistida. Nunca acepta mercadería; el usuario valida el borrador."""
import base64
import io
import json
import os
import urllib.request
from app.models.validation import day, text

def extract(payload):
    kind=payload.get('type')
    if kind not in ['invoice','delivery_note','certificate']:raise ValueError('Tipo documental inválido')
    if payload.get('pdf_base64'):
        try:
            from pypdf import PdfReader
        except ImportError:
            raise ValueError('Para PDF instala requirements-pdf.txt')
        try:
            raw=base64.b64decode(payload['pdf_base64'],validate=True)
            reader=PdfReader(io.BytesIO(raw))
            if len(reader.pages)>30:raise ValueError('Máximo 30 páginas')
            content='\n'.join(f'[página {i+1}] {page.extract_text() or ""}' for i,page in enumerate(reader.pages))
        except Exception as e:
            raise ValueError('PDF inválido, cifrado o no legible: '+str(e))
    else:content=payload.get('text','')
    if not isinstance(content,str) or not 1<=len(content.strip())<=50000:raise ValueError('Texto vacío o mayor a 50000 caracteres. PDF escaneado requiere OCR externo.')
    if os.environ.get('AI_MODE')!='ollama':raise ValueError('La extracción requiere AI_MODE=ollama; también puedes cargar documentos estructurados en JSON.')
    prompt=(__import__('pathlib').Path(__file__).resolve().parents[2]/'prompts/extraction.txt').read_text()
    request=urllib.request.Request(os.environ.get('OLLAMA_URL','http://127.0.0.1:11434')+'/api/chat',
        data=json.dumps({'model':os.environ.get('OLLAMA_MODEL','qwen2.5:7b'),'stream':False,'format':'json',
          'options':{'temperature':0},'messages':[{'role':'system','content':prompt},
          {'role':'user','content':json.dumps({'type':kind,'document_text':content})}]}).encode(),headers={'Content-Type':'application/json'})
    try:
        with urllib.request.urlopen(request,timeout=30) as response:raw=response.read(262145)
        if len(raw)>262144:raise ValueError('Salida demasiado grande')
        value=json.loads(json.loads(raw)['message']['content'])
        doc={'id':text(value.get('id'),'id'),'type':kind}
        if kind=='certificate':
            doc.update(sku=text(value.get('sku'),'sku'),lot=text(value.get('lot'),'lot'),expiry=day(value.get('expiry')).isoformat())
        evidence=value.get('evidence')
        if not isinstance(evidence,str) or not evidence.strip() or evidence not in content:raise ValueError('Evidencia textual no encontrada')
        return {'document':doc,'evidence':evidence,'review_required':True,'prompt_version':'extraction-v1'}
    except (OSError,ValueError,KeyError,TypeError) as e:
        raise ValueError('No se pudo extraer con evidencia válida: '+str(e))
