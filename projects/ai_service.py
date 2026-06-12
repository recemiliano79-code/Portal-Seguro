# -*- coding: utf-8 -*-
"""
Sentinel AI - Asistente de IA para Violencia de Género
=========================================================
Powered by BlackNox API
"""

import os
import json
import logging
import requests
from typing import Dict, List, Optional, Any, Generator
from datetime import datetime
from enum import Enum
from dataclasses import dataclass
from functools import wraps

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('SentinelAI')


class SentinelConfig:
    API_KEY: str = os.getenv('BLACKNOX_API_KEY', '')
    BASE_URL: str = os.getenv('BLACKNOX_BASE_URL', 'https://api.blacknox.com/v1')
    DEFAULT_MODEL: str = os.getenv('BLACKNOX_MODEL', 'blacknox-2-chat')
    DEFAULT_TIMEOUT: int = 30
    STREAM_TIMEOUT: int = 60
    MAX_TOKENS_DEFAULT: int = 1024

    SYSTEM_CONTEXT: str = (
        "Eres Sentinel, una IA especializada exclusivamente en asistir a personas que estan viviendo "
        "situaciones de acoso (fisico, verbal, psicologico, cibernetico, laboral, escolar o de cualquier tipo). "
        "Tu estilo debe ser siempre formal, sereno, profesional y generar confianza absoluta. "
        "Habla con empatia contenida, claridad y autoridad, transmitiendo que la persona no esta sola "
        "y que hay pasos concretos y seguros que puede dar. Usa un lenguaje respetuoso, directo y empoderador, "
        "nunca sensacionalista ni paternalista. "
        "REGLA ABSOLUTA: Solo responderás a consultas relacionadas con acoso, como documentar pruebas, "
        "como levantar informes o denuncias, instituciones de apoyo (policia, fiscalia, lineas de ayuda, "
        "ONGs, centros de atencion a victimas, etc.), procedimientos legales, derechos de las victimas "
        "y estrategias de proteccion inmediata. "
        "Si el usuario pregunta cualquier cosa que NO este directamente relacionada con estos temas, "
        "responderás UNICAMENTE con la siguiente frase y nada mas: "
        "'Lo siento, solo puedo ayudarte con temas relacionados con situaciones de acoso, informes, "
        "instituciones de apoyo o aspectos legales.' "
        "En tus respuestas siempre: "
        "- Valida la experiencia de la persona sin dramatizar. "
        "- Proporciona pasos claros, ordenados y realistas usando Markdown (negritas, listas). "
        "- Menciona recursos segun el pais o region que indique el usuario (si no lo indica, pregunta). "
        "- Si el usuario esta en Mexico, incluye recursos de CDMX: "
        "Linea Mujeres 55-5658-1111 (24/7), LUNAS (24/7 todas las alcaldias), "
        "911 emergencias, 089 denuncia anonima, CAVI 55-5346-8000, CEJUR 55-5575-7583. "
        "- Insiste en la importancia de contactar profesionales (abogados, psicologos, autoridades). "
        "- Nunca des consejos medicos ni legales personalizados que sustituyan a un profesional. "
        "- Mantén la confidencialidad y la seriedad en todo momento. "
        "- Nunca uses emojis ni lenguaje informal. "
        "Cuando el usuario salude, responde con una bienvenida formal, breve y tranquilizadora "
        "e invitale a compartir su situacion."
    )


class BlackNoxAPIError(Exception):
    def __init__(self, status_code: int, message: str, response_body: str = None):
        self.status_code = status_code
        self.message = message
        self.response_body = response_body
        super().__init__(f"BlackNox API Error {status_code}: {message}")


SentinelAIError = BlackNoxAPIError


class SentinelAI:

    DEFAULT_TIMEOUT = SentinelConfig.DEFAULT_TIMEOUT
    STREAM_TIMEOUT = SentinelConfig.STREAM_TIMEOUT

    EMERGENCY_RESPONSES = {
        'sos': """🚨 **PROTOCOLO DE EMERGENCIA**

**SI ESTÁS EN PELIGRO AHORA:**

1. **Sal del lugar** si es seguro hacerlo
2. **Llama al 911** inmediatamente
3. **Ve a un lugar público** (tienda, estación de policía)
4. **Contacta a tu red de apoyo**

**📞 NÚMEROS DE EMERGENCIA:**
- **911** — Emergencias generales
- **089** — Denuncia anónima
- **55-5658-1111** — Línea Mujeres CDMX (24/7)
- **800-822-4460** — Red Nacional de Refugios

**Tu seguridad es lo primero. No estás sola.**""",

        'ciber_inmediate': """🔒 **PROTECCIÓN DIGITAL URGENTE**

**PASOS CRÍTICOS (HAZ ESTO AHORA):**

1. **Cambia TODAS tus contraseñas** desde un dispositivo diferente
2. **Activa verificación en 2 pasos** en todas tus cuentas
3. **Revisa apps desconocidas** en tu teléfono
4. **Cierra sesiones remotas** no reconocidas
5. **Cambia privacidad** en redes sociales

Si sospechas spyware: usa teléfono prestado, acude a una LUNA.
**⚠️ No borres evidencia antes de documentarla**
**📞 Cibernéticos Fiscalía: 55-5242-5100**""",
    }

    TOPIC_PROMPTS = {
        'legal': {
            'prefix': "Eres experta en derecho mexicano especializada en violencia de género. ",
            'prompt': "Proporciona información precisa sobre proceso legal en CDMX: pasos para denunciar, documentos, medidas de protección. "
        },
        'psico': {
            'prefix': "Eres psicóloga especializada en trauma por violencia de género. ",
            'prompt': "Proporciona técnicas de contención emocional inmediatas y estrategias de afrontamiento. Sé empática. "
        },
        'ciber': {
            'prefix': "Eres experta en ciberseguridad para víctimas de violencia. ",
            'prompt': "Proporciona pasos urgentes de protección digital. Prioriza la seguridad. "
        },
        'sos': {
            'prefix': "Esta persona está en emergencia inmediata. ",
            'prompt': "Protocolo de emergencia claro: seguridad física, números de emergencia, lugares seguros. "
        },
        'plan': {
            'prefix': "Eres experta en seguridad personal y planes de emergencia. ",
            'prompt': "Plan de seguridad completo: mochila de emergencia, rutas de escape, red de apoyo. "
        },
        'vicaria': {
            'prefix': "Eres experta en violencia vicaria y sus implicaciones legales en México. ",
            'prompt': "Explica violencia vicaria, cómo identificarla, documentarla y recursos para proteger a los hijos. "
        },
        'red': {
            'prefix': "Eres experta en redes de apoyo seguras. ",
            'prompt': "Guía práctica para identificar personas de confianza y crear protocolos de emergencia. "
        },
        'denuncia': {
            'prefix': "Eres experta en el proceso de denuncia en México. ",
            'prompt': "Proceso de denuncia en CDMX: dónde ir, qué llevar, qué pasa después, anonimidad. "
        },
        'documentacion': {
            'prefix': "Eres experta en documentación de evidencia de violencia. ",
            'prompt': "Guía de cómo documentar violencia de forma segura para usarla como evidencia. "
        },
        'economica': {
            'prefix': "Eres experta en violencia económica y empoderamiento financiero. ",
            'prompt': "Explica violencia económica, cómo identificarla y recursos para independencia financiera. "
        },
        'emocional': {
            'prefix': "Eres psicóloga empática especializada en apoyo emocional para víctimas de violencia. ",
            'prompt': "Brinda apoyo emocional, valida los sentimientos y ofrece estrategias para manejar el dolor. "
        },
        'orientacion': {
            'prefix': "Eres orientadora experta en crisis por violencia de género. ",
            'prompt': "Orienta a la persona con pasos claros y recursos inmediatos disponibles en CDMX. "
        },
    }

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 0.7,
        system_context: Optional[str] = None
    ):
        self.api_key = api_key or SentinelConfig.API_KEY
        self.base_url = (base_url or SentinelConfig.BASE_URL).rstrip('/')
        self.model = model or SentinelConfig.DEFAULT_MODEL
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.system_context = system_context or SentinelConfig.SYSTEM_CONTEXT

        if not self.api_key:
            raise ValueError(
                "Se requiere BLACKNOX_API_KEY. "
                "Configúrala en tu archivo .env"
            )

        logger.info(f"🤖 SentinelAI listo · modelo: {self.model} · url: {self.base_url}")

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}

    def _ssl_verify(self) -> bool:
        return os.getenv('BLACKNOX_SSL_VERIFY', 'true').lower() != 'false'

    def _build_messages(self, user_content: str, conversation_history=None) -> List[Dict]:
        messages = [{"role": "system", "content": self.system_context}]
        if conversation_history:
            for msg in conversation_history:
                if isinstance(msg, dict):
                    role = msg.get('role', '').lower()
                    content = msg.get('content', '')
                    if role in ['user', 'assistant', 'system'] and content:
                        messages.append({"role": role, "content": content})
        messages.append({"role": "user", "content": user_content})
        return messages

    def _call_api(self, messages: List[Dict], stream: bool = False):
        url = f"{self.base_url}/chat/completions"
        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "stream": stream
        }
        timeout = self.STREAM_TIMEOUT if stream else self.DEFAULT_TIMEOUT
        logger.info(f"📤 POST {url} · model={self.model}")

        response = requests.post(
            url, headers=self._headers(), json=payload,
            stream=stream, timeout=timeout, verify=self._ssl_verify()
        )

        logger.info(f"📥 Status: {response.status_code} · preview: {response.text[:200]}")

        if response.status_code == 200:
            if stream:
                return response
            if not response.text.strip():
                raise BlackNoxAPIError(200, "BlackNox respondió con body vacío. Verifica modelo y endpoint.")
            return response.json()

        error_msg = f"HTTP {response.status_code}"
        try:
            err = response.json()
            error_msg = err.get('error', {}).get('message', error_msg)
        except Exception:
            pass
        raise BlackNoxAPIError(response.status_code, error_msg, response.text)

    def get_response(self, user_message: str, topic: Optional[str] = None,
                     conversation_history=None) -> str:
        try:
            if topic == 'sos' and not user_message:
                return self.EMERGENCY_RESPONSES['sos']
            if topic == 'ciber' and user_message and 'urgente' in user_message.lower():
                return self.EMERGENCY_RESPONSES['ciber_inmediate']

            if topic and topic in self.TOPIC_PROMPTS:
                tp = self.TOPIC_PROMPTS[topic]
                user_content = tp['prefix'] + tp['prompt'] + (user_message or '')
            else:
                user_content = user_message or 'Necesito orientación'

            messages = self._build_messages(user_content, conversation_history)
            data = self._call_api(messages)
            content = data['choices'][0]['message']['content']
            logger.info(f"✅ Respuesta OK · topic={topic}")
            return content

        except Exception as e:
            logger.error(f"❌ Error en get_response: {e}", exc_info=True)
            return self._get_fallback_response(topic)

    def get_quick_response(self, topic: str) -> str:
        try:
            if topic in self.EMERGENCY_RESPONSES:
                return self.EMERGENCY_RESPONSES[topic]
            quick_prompts = {
                'legal': "Dame los 3 pasos para denunciar violencia de género en CDMX.",
                'psico': "Técnicas de contención emocional inmediatas para crisis de ansiedad por violencia.",
                'ciber': "Mi agresor monitorea mi celular. Dame 5 pasos de protección digital AHORA.",
                'sos': "Estoy en peligro físico inmediato. Protocolo de emergencia paso a paso.",
                'plan': "Cómo crear mochila de emergencia y plan de escape.",
                'vicaria': "Qué es violencia vicaria, cómo identificarla y documentarla en México.",
                'red': "Cómo construir una red de apoyo efectiva y segura.",
                'denuncia': "¿Puedo denunciar de forma anónima en CDMX? Proceso completo.",
                'documentacion': "Cómo documentar la violencia de forma segura como evidencia.",
                'economica': "Qué es violencia económica y cómo protegerme.",
                'emocional': "Necesito apoyo emocional ahora. Me siento sola y asustada.",
                'orientacion': "Necesito orientación urgente sobre mi situación de violencia.",
            }
            prompt = quick_prompts.get(topic, "Necesito orientación sobre violencia de género en México.")
            return self.get_response(prompt, topic=topic)
        except Exception as e:
            logger.error(f"❌ Error en get_quick_response: {e}")
            return self._get_fallback_response(topic)

    def stream_response(self, user_message: str, topic: Optional[str] = None,
                        conversation_history=None) -> Generator[str, None, None]:
        try:
            if topic and topic in self.TOPIC_PROMPTS:
                tp = self.TOPIC_PROMPTS[topic]
                user_content = tp['prefix'] + tp['prompt'] + user_message
            else:
                user_content = user_message
            messages = self._build_messages(user_content, conversation_history)
            response = self._call_api(messages, stream=True)
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data: '):
                        raw = line[6:]
                        if raw.strip() == '[DONE]':
                            break
                        try:
                            chunk = json.loads(raw)
                            content = chunk['choices'][0].get('delta', {}).get('content', '')
                            if content:
                                yield content
                        except (json.JSONDecodeError, KeyError):
                            pass
        except Exception as e:
            logger.error(f"❌ Error en streaming: {e}")
            yield self._get_fallback_response(topic)

    def _get_fallback_response(self, topic: Optional[str]) -> str:
        responses = {
            'legal': """📋 **ASESORÍA LEGAL BÁSICA**

**Pasos para denunciar en CDMX:**
1. **Reúne evidencias** (fotos, mensajes, testigos)
2. **Acude al MP más cercano** o a una LUNA (24/7, gratis)
3. **Solicita medidas de protección inmediatas**

**Documentos:** INE + copia · Comprobante de domicilio · Evidencia disponible

**📞 Contactos:**
- **911** · **089** — Denuncia anónima
- **55-5658-1111** — Línea Mujeres CDMX
- **55-5575-7583** — CEJUR · **55-5200-9000** — Fiscalía CDMX""",

            'psico': """💜 **APOYO PSICOLÓGICO INMEDIATO**

**Respiración 4-4-4:** Inhala 4s → Sostén 4s → Exhala 4s (repite 5 veces)

**Técnica 5-4-3-2-1:**
5 cosas que VES · 4 que TOCAS · 3 que OYES · 2 que HUELES · 1 que PRUEBAS

**📞 Recursos:**
- **55-5658-1111** — Línea Mujeres (24/7)
- **800-911-2000** — Línea de la Vida
- **55-5346-8000** — CAVI

**Lo que sientes es válido. No estás sola.**""",

            'emocional': """💙 **APOYO EMOCIONAL**

Estoy aquí contigo. Lo que sientes es completamente válido.

**Recuerda:** No es tu culpa · Mereces estar segura · Hay ayuda ahora mismo

**Respiración:** Inhala 4s → Sostén 4s → Exhala 6s → Repite

**📞 Apoyo inmediato:**
- **55-5658-1111** — Línea Mujeres CDMX (24/7, confidencial)
- **800-911-2000** — Línea de la Vida
- **55-5346-8000** — CAVI

**No estás sola.**""",

            'orientacion': """🧭 **ORIENTACIÓN INMEDIATA**

**Si estás en peligro:** Llama al **911** o ve a la LUNA más cercana

**Si necesitas hablar:** **55-5658-1111** — Línea Mujeres (24/7, gratis)

**Si quieres documentar:** Guarda capturas, fotos con fecha, bitácora de incidentes

**Si quieres denunciar:** Acude a una LUNA — te acompañan sin costo

**LUNAS:** 24/7 en todas las alcaldías · Legal, psicológico y médico gratuito.""",

            'ciber': """🔒 **PROTECCIÓN DIGITAL URGENTE**

1. Cambia contraseñas desde otro dispositivo
2. Activa verificación en 2 pasos
3. Revisa apps desconocidas
4. Cierra sesiones remotas
5. Cambia privacidad en redes sociales

**⚠️ No borres evidencia antes de documentarla**
**📞 Cibernéticos Fiscalía: 55-5242-5100**""",

            'sos': """🚨 **PROTOCOLO DE EMERGENCIA**

1. Sal del lugar si es seguro
2. Llama al **911** inmediatamente
3. Ve a un lugar público
4. Contacta a tu red de apoyo

**📞 NÚMEROS:**
- **911** · **089** · **55-5658-1111** · **800-822-4460**""",

            'plan': """🎒 **MOCHILA DE EMERGENCIA**

**Documentos:** INE · Actas de nacimiento · Comprobante · Fotos del agresor · Números escritos
**Dinero:** $1,000+ efectivo · Tarjetas · Llaves extras
**Esenciales:** Medicamentos · Ropa · Cargador

💡 Guárdala en casa de alguien de confianza.""",

            'vicaria': """👨‍👩‍👧 **VIOLENCIA VICARIA**

Cuando el agresor usa a los hijos para lastimarte. Documenta con:
capturas de mensajes · bitácora con fechas · testigos (maestros, vecinos)

**📞 Acude a una LUNA — orientación gratuita 24/7**""",

            'red': """🤝 **RED DE APOYO SEGURA**

Identifica 3-5 personas: familiar · amiga cercana · vecina o compañera
Establece: palabra clave de emergencia · plan de comunicación · lugar seguro

**No tienes que enfrentar esto sola.**""",

            'denuncia': """📝 **PROCESO DE DENUNCIA CDMX**

- **Presencial:** MP o LUNA (24/7)
- **En línea:** fgjcdmx.gob.mx
- **Anónima:** **089**

Después: carpeta de investigación → MP asignado → medidas de protección

**📞 Seguimiento: 55-5200-9000 — Fiscalía CDMX**""",

            'documentacion': """📸 **DOCUMENTAR VIOLENCIA**

- Capturas de mensajes (con fecha y hora)
- Fotos de lesiones con fecha visible
- Registros de llamadas · Correos amenazantes
- Guarda en la nube + compartir con alguien de confianza

**⚠️ No borres nada · Hazlo de forma discreta.**""",

            'economica': """💰 **VIOLENCIA ECONÓMICA**

Cuando te niegan dinero, controlan gastos o generan deudas a tu nombre.

**Protección:** Abre cuenta propia · Guarda efectivo seguro · Documenta gastos
**Recursos:** LUNAS · Instituto de Mujeres CDMX · STPS (capacitación gratuita)""",
        }

        return responses.get(topic or '', """💜 **SENTINEL AI · INFORMACIÓN Y APOYO**

**📞 Líneas de ayuda inmediata:**
- **911** — Emergencias · **089** — Denuncia anónima
- **55-5658-1111** — Línea Mujeres CDMX (24/7)
- **800-822-4460** — Red Nacional de Refugios
- **55-5346-8000** — CAVI · **55-5575-7583** — CEJUR

**🏥 LUNAS** — 24/7 en todas las alcaldías · Legal, psicológico y médico gratuito.

Escríbeme tu pregunta y te ayudo con información sobre violencia de género.
**No estás sola.**""")

    def get_emergency_info(self) -> Dict[str, Any]:
        return {
            'emergency': {'911': {'name': 'Emergencias', 'available': '24/7'},
                          '089': {'name': 'Denuncia Anónima', 'available': '24/7'}},
            'specialized': {'55-5658-1111': {'name': 'Línea Mujeres CDMX', 'available': '24/7'},
                            '800-822-4460': {'name': 'Red Nacional de Refugios', 'available': '24/7'},
                            '55-5346-8000': {'name': 'CAVI', 'available': '24/7'}}
        }


# ── Funciones utilitarias ──────────────────────────────────────────────────

def get_emergency_contacts() -> str:
    return """🚨 **CONTACTOS DE EMERGENCIA**

- **911** — Emergencias · **089** — Denuncia anónima
- **55-5658-1111** — Línea Mujeres CDMX (24/7)
- **800-822-4460** — Red Nacional de Refugios (24/7)
- **55-5346-8000** — CAVI · **55-5575-7583** — CEJUR
- **800-900-8000** — CONAVIM · **800-911-2000** — Línea de la Vida

🏥 **LUNAS** — 24/7 · Todas las alcaldías · Gratuito y confidencial."""


def get_institutional_resources() -> str:
    return """🏛️ **RECURSOS INSTITUCIONALES CDMX**

LUNAS | 55-5658-1111 | 24/7 | Gratuito
FGJCDMX | 55-5200-9000 | Av. Eduardo Molina 10
INMUJERES CDMX | 55-5658-1111 | Donceles 100
CAVI | 55-5346-8000 | 24/7
CEJUR | 55-5575-7583
Red Nacional de Refugios | 800-822-4460 | 24/7"""


def get_legal_information() -> str:
    return """⚖️ **INFORMACIÓN LEGAL BÁSICA**

Tipos de violencia: Física · Emocional · Económica · Sexual · Vicaria
Documentos para denunciar: INE · Comprobante de domicilio · Evidencia
Medidas de protección disponibles en LUNAS y MP.
Tus derechos: Confidencialidad · Acompañamiento gratuito · Medidas inmediatas."""


def get_cibersecurity_tips() -> str:
    return """🔒 **PROTECCIÓN DIGITAL**

Contraseñas distintas · 2FA activado · Revisar apps desconocidas
Signal/WhatsApp para comunicación segura
**Cibernéticos Fiscalía: 55-5242-5100**"""


# ── Instancia global ───────────────────────────────────────────────────────
try:
    sentinel_ai = SentinelAI()
except ValueError as e:
    logger.warning(f"⚠️ SentinelAI no iniciado (falta BLACKNOX_API_KEY): {e}")
    sentinel_ai = None
except Exception as e:
    logger.warning(f"⚠️ Error iniciando SentinelAI: {e}")
    sentinel_ai = None