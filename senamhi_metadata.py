import requests
from bs4 import BeautifulSoup
import json
import re

# ══════════════════════════════════════════════════════════════════════════════
# Scrapper de metadata (regiones, tipos, estaciones)
# ══════════════════════════════════════════════════════════════════════════════

class SenamhiMetadata:
    URL_PRINCIPAL = 'https://www.senamhi.gob.pe/main.php?dp=amazonas&p=estaciones'
    URL_MAPA      = 'https://www.senamhi.gob.pe/mapas/mapa-estaciones-2/?dp={dp}'

    @staticmethod
    def obtener_regiones():
        print("[META] Obteniendo regiones...")
        response = requests.get(SenamhiMetadata.URL_PRINCIPAL)
        soup     = BeautifulSoup(response.text, 'html.parser')
        dropdown = soup.find('div', {'class': 'dropdown-menu'})
        links    = dropdown.find_all('a', class_='dropdown-item')

        regiones = []
        for link in links:
            href = link.get('href', '')
            if 'dp=' in href:
                dp     = href.split('dp=')[1].split('&')[0]
                nombre = link.get_text(strip=True)
                regiones.append({'nombre': nombre, 'dp': dp})

        print(f"  {len(regiones)} regiones encontradas")
        return regiones

    @staticmethod
    def obtener_tipos_estacion():
        print("[META] Obteniendo tipos de estación...")
        response = requests.get(SenamhiMetadata.URL_PRINCIPAL)
        soup     = BeautifulSoup(response.text, 'html.parser')

        clases = [
            'ico-leyenda-mapa-convencional-m',
            'ico-leyenda-mapa-automatica-m',
            'ico-leyenda-mapa-convencional-h',
            'ico-leyenda-mapa-automatica-h',
        ]
        tipos = []
        for clase in clases:
            div = soup.find('div', class_=clase)
            if div:
                tipos.append(div.get_text(strip=True))

        print(f"  {len(tipos)} tipos encontrados")
        return tipos

    @staticmethod
    def obtener_estaciones(dp):
        print(f"[META] Obteniendo estaciones de '{dp}'...")
        url      = SenamhiMetadata.URL_MAPA.format(dp=dp)
        response = requests.get(url)
        soup     = BeautifulSoup(response.text, 'html.parser')

        script_target = None
        for script in soup.find_all('script', type='text/javascript'):
            if script.string and 'PruebaTest' in script.string:
                script_target = script.string
                break

        if not script_target:
            print(f"  [!] No se encontró PruebaTest para {dp}")
            return []

        match = re.search(
            r'var PruebaTest\s*=\s*(\[.*?\])\s*;', script_target, re.DOTALL
        )
        if not match:
            print(f"  [!] No se pudo extraer el JSON para {dp}")
            return []

        estaciones = json.loads(match.group(1))
        normalizadas = [
            SenamhiMetadata._normalizar(e) for e in estaciones
        ]
        print(f"  {len(normalizadas)} estaciones encontradas")
        return normalizadas

    @staticmethod
    def _normalizar_tipo(estacion):
        ico    = estacion.get('ico', '')
        estado = estacion.get('estado', '')

        tipo_base = {'M': 'Meteorológica', 'H': 'Hidrológica'}.get(ico, 'Desconocida')
        subtipo   = 'Automática' if estado == 'AUTOMATICA' else 'Convencional'
        return f'Estación {tipo_base} {subtipo}'

    @staticmethod
    def _normalizar(estacion):
        return {
            'nombre':     estacion['nom'],
            'codigo':     estacion['cod'],
            'codigo_old': estacion.get('cod_old'),
            'categoria':  estacion['cate'],
            'tipo':       SenamhiMetadata._normalizar_tipo(estacion),
            'ico':        estacion.get('ico', 'M'),
            'latitud':    estacion['lat'],
            'longitud':   estacion['lon'],
            'estado':     estacion['estado'],
        }