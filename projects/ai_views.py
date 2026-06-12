from django.http import JsonResponse, StreamingHttpResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import cache_page, never_cache
from django.views.decorators.gzip import gzip_page
from django.utils.decorators import method_decorator
from django.views import View
from django.utils import timezone
import json
import os
import logging
from typing import Optional

try:
    from projects.ai_service import (
        sentinel_ai,
        get_emergency_contacts,
        get_institutional_resources,
        get_legal_information,
        get_cibersecurity_tips,
        SentinelAIError,
    )
    AI_IMPORT_OK = True
except ImportError as e:
    logging.error(f"Error importando servicio de IA: {e}")
    sentinel_ai = None
    SentinelAIError = Exception
    AI_IMPORT_OK = False

logger = logging.getLogger('sentinel_ai_views')


def is_blacknox_configured() -> bool:
    return bool(os.getenv('BLACKNOX_API_KEY'))


def validate_json_request(request, required_fields: list = None) -> tuple:
    try:
        if not request.body:
            return False, None, "Request body vacío"
        data = json.loads(request.body)
        if required_fields:
            missing_fields = [f for f in required_fields if f not in data]
            if missing_fields:
                return False, None, f"Campos faltantes: {', '.join(missing_fields)}"
        return True, data, None
    except json.JSONDecodeError:
        return False, None, "JSON inválido"
    except Exception as e:
        return False, None, f"Error procesando request: {str(e)}"


def ok(data, status=200) -> JsonResponse:
    """Respuesta exitosa — SIEMPRE HTTP 200 para que el JS no rompa."""
    return JsonResponse({
        'success': True,
        'timestamp': timezone.now().isoformat(),
        'data': data
    }, status=status)


# ─── Respuestas de respaldo ───────────────────────────────────────────────────

def _fallback(topic: Optional[str] = None) -> str:
    if sentinel_ai is not None:
        try:
            return sentinel_ai._get_fallback_response(topic)
        except Exception:
            pass

    HARDCODED = {
        'sos': (
            "Entiendo que puede estar en una situacion de riesgo. Su seguridad es la prioridad absoluta.\n\n"
            "**Pasos inmediatos:**\n"
            "1. Si hay peligro fisico, salga del lugar si es seguro hacerlo\n"
            "2. Llame al 911 de inmediato\n"
            "3. Dirijase a un lugar publico o a la LUNA mas cercana (atencion 24/7)\n"
            "4. Contacte a una persona de confianza\n\n"
            "**Numeros de emergencia CDMX:**\n"
            "- 911 — Emergencias\n"
            "- 089 — Denuncia anonima\n"
            "- 55-5658-1111 — Linea Mujeres CDMX (24/7, gratuita)\n"
            "- 800-822-4460 — Red Nacional de Refugios\n\n"
            "No esta sola. Hay personas capacitadas listas para ayudarle ahora mismo."
        ),
        'legal': (
            "Tiene derecho a recibir orientacion legal y a denunciar lo que esta viviendo.\n\n"
            "**Pasos para denunciar en CDMX:**\n"
            "1. Reuna evidencias disponibles (mensajes, fotos, testigos, fechas)\n"
            "2. Acuda al Ministerio Publico mas cercano o a una LUNA (atencion 24/7)\n"
            "3. Solicite medidas de proteccion de forma inmediata\n"
            "4. Pida asesoria juridica gratuita en el CEJUR\n\n"
            "**Documentos utiles:** identificacion oficial, comprobante de domicilio, "
            "cualquier evidencia disponible.\n\n"
            "**Contactos:**\n"
            "- 55-5658-1111 — Linea Mujeres CDMX\n"
            "- 55-5575-7583 — CEJUR (asesoria juridica gratuita)\n"
            "- 55-5346-8000 — CAVI\n\n"
            "Le recomiendo contactar a un profesional legal para orientacion personalizada."
        ),
        'psico': (
            "Lo que esta viviendo es dificil, y sus sentimientos son completamente validos. "
            "Pedir ayuda es un acto de valentia.\n\n"
            "**Tecnica de respiracion para momentos de crisis (4-4-4):**\n"
            "Inhale 4 segundos — Sostenga 4 segundos — Exhale 4 segundos. Repita 5 veces.\n\n"
            "**Tecnica de anclaje 5-4-3-2-1:**\n"
            "- 5 cosas que puede VER\n"
            "- 4 cosas que puede TOCAR\n"
            "- 3 cosas que puede OIR\n"
            "- 2 cosas que puede OLER\n"
            "- 1 cosa que puede PROBAR\n\n"
            "**Recursos de apoyo emocional:**\n"
            "- 55-5658-1111 — Linea Mujeres CDMX (24/7, gratuita)\n"
            "- 800-911-2000 — Linea de la Vida\n"
            "- 55-5346-8000 — CAVI (atencion psicologica especializada)\n\n"
            "Le recomiendo buscar acompanamiento con un psicologo especializado en trauma."
        ),
        'ciber': (
            "La seguridad digital es parte de su proteccion integral. "
            "Le recomiendo actuar con calma pero sin demora.\n\n"
            "**Pasos prioritarios:**\n"
            "1. Cambie todas sus contrasenas desde un dispositivo seguro y distinto\n"
            "2. Active la verificacion en dos pasos en todas sus cuentas\n"
            "3. Revise las aplicaciones instaladas en su telefono\n"
            "4. Cierre sesiones remotas no reconocidas\n"
            "5. Ajuste la privacidad en sus redes sociales\n\n"
            "**Importante:** No elimine evidencia digital antes de documentarla con capturas de pantalla.\n\n"
            "- Fiscalia CDMX (ciberneticos): 55-5242-5100"
        ),
        'plan': (
            "Contar con un plan de seguridad es una decision inteligente y preventiva.\n\n"
            "**Mochila de emergencia — tenga lista:**\n"
            "- Documentos: identificacion, actas de nacimiento, comprobante de domicilio\n"
            "- Evidencia: capturas de mensajes, fotos relevantes\n"
            "- Recursos economicos: efectivo y tarjetas bancarias\n"
            "- Articulos basicos: medicamentos, cargador, ropa esencial\n\n"
            "**Red de apoyo:**\n"
            "- Identifique 2 o 3 personas de confianza\n"
            "- Acuerde una palabra clave de emergencia con ellas\n"
            "- Considere compartir su ubicacion en tiempo real si es necesario\n\n"
            "Guarde la mochila en un lugar seguro, idealmente en casa de alguien de confianza."
        ),
        'emocional': (
            "Estoy aqui para escucharle. Lo que comparta es completamente confidencial.\n\n"
            "Lo que esta viviendo es dificil, y es completamente normal sentir miedo, "
            "confusion o agotamiento. Sus sentimientos son validos.\n\n"
            "**Recuerde:**\n"
            "- Lo que le ocurre no es su culpa\n"
            "- Merece estar segura y en paz\n"
            "- Pedir ayuda es una muestra de fortaleza\n\n"
            "**Apoyo disponible ahora:**\n"
            "- 55-5658-1111 — Linea Mujeres CDMX (24/7, gratuita)\n"
            "- 800-911-2000 — Linea de la Vida\n\n"
            "Cuando este lista, puede contarme mas sobre su situacion y le oriento paso a paso."
        ),
        'orientacion': (
            "Estoy aqui para orientarle. Por favor describa brevemente su situacion "
            "y le proporcionare una guia concreta.\n\n"
            "**Si hay peligro inmediato:**\n"
            "1. Salga del lugar si es seguro\n"
            "2. Llame al 911\n"
            "3. Acuda a la LUNA mas cercana (atencion 24/7, gratuita)\n\n"
            "**Si la situacion no es urgente:**\n"
            "1. Documente todo lo ocurrido (fechas, mensajes, testigos)\n"
            "2. Hable con una persona de confianza\n"
            "3. Contacte la Linea Mujeres: 55-5658-1111 para orientacion profesional\n"
            "4. Considere asesoria legal en el CEJUR: 55-5575-7583\n\n"
            "Indiqueme su situacion y le ayudo con informacion mas especifica."
        ),
    }

    return HARDCODED.get(topic, (
        "Bienvenida a Sentinel. Todo lo que comparta es estrictamente confidencial.\n\n"
        "Estoy aqui para orientarle con informacion clara sobre situaciones de acoso, "
        "derechos, instituciones de apoyo y estrategias de proteccion.\n\n"
        "**Recursos disponibles en CDMX:**\n"
        "- 911 — Emergencias\n"
        "- 55-5658-1111 — Linea Mujeres CDMX (24/7, gratuita)\n"
        "- 089 — Denuncia anonima\n"
        "- 800-822-4460 — Red Nacional de Refugios\n"
        "- 55-5346-8000 — CAVI\n\n"
        "Las LUNAS ofrecen atencion gratuita las 24 horas en todas las alcaldias de CDMX, "
        "incluyendo apoyo legal, psicologico y medico.\n\n"
        "Puede comenzar cuando lo considere oportuno."
    ))


# ─── Filtro de tema ───────────────────────────────────────────────────────────

_TEMAS_PERMITIDOS = [
    'acoso','hostigamiento','violencia','agresion','agresión','abuso',
    'violacion','violación','amenaza','amenazas','golpe','golpea','maltrato',
    'feminicidio','stalking','persigue','tocamiento','manoseo','acosador','agresor',
    'denuncia','denunciar','derechos','ley','legal','ministerio','fiscalia','fiscalía',
    'amparo','orden de proteccion','abogada','abogado','juicio','delito','crimen',
    'miedo','asustada','asustado','trauma','ansiedad','depresion','depresión',
    'ayuda','socorro','auxilio','peligro','emergencia','escape','huir','refugio',
    'culpa','culpable','vergüenza','verguenza','lloro','llorando','dolor',
    'sufrimiento','apoyo','escuchar','me siento','sola','solo',
    'fotos intimas','extorsion','extorsión','hackeo','hackear','contraseña',
    'espia','rastreo','revenge porn','sexting','ciberacoso',
    'evidencia','prueba','documentar','captura','screenshot','testigo','reporte',
    'luna','cavi','cejur','inmujeres','albergue','linea mujeres','conavim',
    'que hago','qué hago','como','cómo','donde','dónde',
    'puedo','debo','tengo que','estoy','siento','me paso','me hizo',
    'me dijo','me toco','me amenazo','plan','mochila','red de apoyo',
    'bullying','bully','acoso escolar','acoso laboral','acoso sexual',
    'orientacion','orientación','apoyo emocional',
]

_RESPUESTA_FUERA_DE_TEMA = (
    "Lo siento, solo puedo ayudarte con temas relacionados con situaciones de acoso, "
    "informes, instituciones de apoyo o aspectos legales."
)


def _es_tema_permitido(mensaje: str) -> bool:
    msg = mensaje.lower().strip()
    # Saludos y mensajes cortos siempre se permiten
    if len(msg) <= 25:
        return True
    return any(kw in msg for kw in _TEMAS_PERMITIDOS)


# ─── Endpoints ────────────────────────────────────────────────────────────────

@method_decorator(csrf_exempt, name='dispatch')
@method_decorator(gzip_page, name='dispatch')
class AIChatEndpoint(View):
    """
    Endpoint principal del chat Sentinel.
    SIEMPRE devuelve HTTP 200 para que el JS nunca muestre 'Error de conexión'.
    """

    @method_decorator(never_cache)
    def post(self, request):
        data = None
        try:
            success, data, error = validate_json_request(request, required_fields=['message'])
            if not success:
                return ok({'response': _fallback(None), 'source': 'fallback', 'topic': None})

            user_message = data.get('message', '').strip()
            topic = data.get('topic') or None
            history = data.get('history', [])
            stream = data.get('stream', False)

            ai_unavailable = (sentinel_ai is None) or (not is_blacknox_configured())

            # Mensaje vacío
            if not user_message:
                return ok({'response': _fallback(topic), 'source': 'fallback', 'topic': topic})

            # Filtro de tema
            if not _es_tema_permitido(user_message):
                return ok({'response': _RESPUESTA_FUERA_DE_TEMA, 'source': 'filter', 'topic': topic})

            # IA no disponible → respaldo enriquecido
            if ai_unavailable:
                logger.warning("BlackNox no configurado, usando respaldo para topic=%s", topic)
                return ok({'response': _fallback(topic), 'source': 'fallback', 'topic': topic})

            # Streaming
            if stream:
                return self._handle_streaming(user_message, topic, history)

            # Respuesta normal con BlackNox
            try:
                ai_response = sentinel_ai.get_response(user_message, topic, history)
                return ok({'response': ai_response, 'source': 'blacknox', 'topic': topic})
            except Exception as e:
                logger.error("Error en sentinel_ai.get_response: %s", e)
                return ok({'response': _fallback(topic), 'source': 'fallback', 'topic': topic})

        except Exception as e:
            logger.error("Error inesperado en AIChatEndpoint: %s", e, exc_info=True)
            topic = data.get('topic') if data else None
            return ok({'response': _fallback(topic), 'source': 'fallback', 'topic': topic})

    def _handle_streaming(self, user_message, topic, history):
        try:
            def event_stream():
                try:
                    yield f"data: {json.dumps({'type': 'start', 'topic': topic})}\n\n"
                    for chunk in sentinel_ai.stream_response(user_message, topic, history):
                        yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"
                    yield f"data: {json.dumps({'type': 'end'})}\n\n"
                except Exception as e:
                    logger.error("Error en streaming: %s", e)
                    yield f"data: {json.dumps({'type': 'chunk', 'content': _fallback(topic)})}\n\n"
                    yield f"data: {json.dumps({'type': 'end'})}\n\n"

            response = StreamingHttpResponse(event_stream(), content_type='text/event-stream')
            response['Cache-Control'] = 'no-cache'
            response['X-Accel-Buffering'] = 'no'
            return response
        except Exception as e:
            logger.error("Error configurando streaming: %s", e)
            return ok({'response': _fallback(topic), 'source': 'fallback', 'topic': topic})


@method_decorator(csrf_exempt, name='dispatch')
class AIQuickResponseEndpoint(View):
    @method_decorator(never_cache)
    def get(self, request, topic: str):
        try:
            if sentinel_ai is None or not is_blacknox_configured():
                return ok({'response': _fallback(topic), 'source': 'fallback', 'topic': topic})
            ai_response = sentinel_ai.get_quick_response(topic)
            return ok({'response': ai_response, 'source': 'blacknox', 'topic': topic})
        except Exception as e:
            logger.error("Error en AIQuickResponseEndpoint: %s", e)
            return ok({'response': _fallback(topic), 'source': 'fallback', 'topic': topic})

    @method_decorator(never_cache)
    def post(self, request, topic: str):
        return self.get(request, topic)


@method_decorator(csrf_exempt, name='dispatch')
class EmergencyInfoEndpoint(View):
    @method_decorator(cache_page(300))
    def get(self, request):
        try:
            info_type = request.GET.get('type', 'all')
            if sentinel_ai:
                data = sentinel_ai.get_emergency_info()
            else:
                data = _fallback('sos')
            return ok({'response': data, 'type': info_type})
        except Exception as e:
            logger.error("Error en EmergencyInfoEndpoint: %s", e)
            return ok({'response': _fallback('sos'), 'type': 'contacts'})


@method_decorator(csrf_exempt, name='dispatch')
class HealthCheckEndpoint(View):
    def get(self, request):
        is_configured = is_blacknox_configured()
        ai_available = sentinel_ai is not None
        return JsonResponse({
            'status': 'healthy' if (is_configured and ai_available) else 'degraded',
            'service': 'sentinel_ai',
            'blacknox_configured': is_configured,
            'ai_instance_available': ai_available,
            'fallback_active': not (is_configured and ai_available),
            'timestamp': timezone.now().isoformat()
        }, status=200)


# ─── Wrappers para urls.py ────────────────────────────────────────────────────

@require_http_methods(["POST"])
@csrf_exempt
@never_cache
def ai_chat_endpoint(request):
    return AIChatEndpoint().post(request)


@require_http_methods(["GET", "POST"])
@csrf_exempt
@never_cache
def ai_quick_response_endpoint(request, topic):
    view = AIQuickResponseEndpoint()
    return view.get(request, topic) if request.method == 'GET' else view.post(request, topic)


@require_http_methods(["GET"])
@cache_page(300)
def get_emergency_info(request, **kwargs):
    return EmergencyInfoEndpoint().get(request)


@require_http_methods(["GET"])
def health_check(request):
    return HealthCheckEndpoint().get(request)