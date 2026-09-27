from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TransactionTestCase
from django.urls import reverse
from asgiref.sync import async_to_sync
from channels.testing.websocket import WebsocketCommunicator
from channels.routing import URLRouter

from equipos.models import Equipo
from .consumers import MatchStateConsumer
from .routing import websocket_urlpatterns

from usuarios.models import Notificacion

from .models import (
    EventoRating,
    Inscripcion,
    Partida,
    RecompensaPartida,
    Torneo,
    Videojuego,
)
from .forms import ResultadoPartidaForm
from .services import generar_bracket, pagar_inscripcion, procesar_inscripcion, procesar_resultado


class CompetenciaEstabilidadTests(TransactionTestCase):
    def setUp(self):
        self.usuario = get_user_model().objects.create_user(
            username='capitan',
            password='password-segura',
        )
        self.rival = get_user_model().objects.create_user(
            username='rival',
            password='password-segura',
        )
        self.videojuego = Videojuego.objects.create(
            nombre='Arena Test',
            genero='Competitivo',
        )

    def _crear_equipo(self, indice: int, capitan=None) -> Equipo:
        return Equipo.objects.create(
            capitan=capitan or self.usuario,
            nombre=f'Crew {indice}',
            modo='1v1',
        )

    def _crear_torneo(self, estado: str) -> Torneo:
        return Torneo.objects.create(
            juego=self.videojuego,
            nombre='Copa de Estabilidad',
            modalidad='1v1',
            cupo_maximo=16,
            estado=estado,
        )

    def test_generar_bracket_admite_cantidad_no_potencia_de_dos(self):
        torneo = self._crear_torneo(Torneo.ESTADO_CERRADO)

        for indice in range(6):
            Inscripcion.objects.create(
                torneo=torneo,
                equipo=self._crear_equipo(indice),
                estado_pago=Inscripcion.ESTADO_PAGADO,
            )

        generar_bracket(torneo)
        self.assertEqual(Partida.objects.filter(torneo=torneo).count(), 7)

    def test_procesar_resultado_no_duplica_recompensas(self):
        torneo = self._crear_torneo(Torneo.ESTADO_EN_CURSO)
        equipo_local = self._crear_equipo(1)
        equipo_visitante = self._crear_equipo(2, self.rival)
        partida = Partida.objects.create(
            torneo=torneo,
            equipo_local=equipo_local,
            equipo_visitante=equipo_visitante,
            ronda='1',
            numero_partida=1,
        )

        procesar_resultado(partida, equipo_local)
        self.usuario.refresh_from_db()

        self.assertEqual(self.usuario.victorias, 1)
        self.assertEqual(self.usuario.puntos_xp, 100)
        self.assertEqual(
            RecompensaPartida.objects.filter(partida=partida).count(),
            2,
        )

    def test_generar_bracket_admite_seis_equipos_con_byes(self):
        torneo = self._crear_torneo(Torneo.ESTADO_CERRADO)
        for indice in range(6):
            Inscripcion.objects.create(
                torneo=torneo,
                equipo=self._crear_equipo(10 + indice),
                estado_pago=Inscripcion.ESTADO_PAGADO,
            )

        partidas = generar_bracket(torneo)

        self.assertEqual(len(partidas), 4)
        self.assertEqual(
            Partida.objects.filter(torneo=torneo, ronda='1', es_bye=True).count(),
            2,
        )
        self.assertEqual(
            Partida.objects.filter(torneo=torneo, ronda='2').count(),
            2,
        )
        self.assertEqual(torneo.refresh_from_db(), None)
        self.assertEqual(torneo.estado, Torneo.ESTADO_EN_CURSO)

    def test_resultado_actualiza_rating_y_historial(self):
        torneo = self._crear_torneo(Torneo.ESTADO_EN_CURSO)
        local = self._crear_equipo(20)
        visitante = self._crear_equipo(21, self.rival)
        partida = Partida.objects.create(
            torneo=torneo,
            equipo_local=local,
            equipo_visitante=visitante,
            ronda='1',
            numero_partida=1,
        )

        procesar_resultado(partida, local)

        self.usuario.refresh_from_db()
        self.rival.refresh_from_db()
        self.assertGreater(self.usuario.rating_competitivo, 1000)
        self.assertLess(self.rival.rating_competitivo, 1000)
        self.assertEqual(EventoRating.objects.filter(partida=partida).count(), 2)

    def test_pago_debita_fichas_y_es_idempotente(self):
        torneo = self._crear_torneo(Torneo.ESTADO_ABIERTO)
        torneo.cuota = 25
        torneo.save(update_fields=['cuota'])
        self.usuario.saldo_fichas = 40
        self.usuario.save(update_fields=['saldo_fichas'])
        inscripcion = procesar_inscripcion(torneo, self._crear_equipo(30))

        pagada = pagar_inscripcion(inscripcion, self.usuario)
        self.usuario.refresh_from_db()
        self.assertEqual(pagada.estado_pago, Inscripcion.ESTADO_PAGADO)
        self.assertEqual(self.usuario.saldo_fichas, 15)
        pagar_inscripcion(inscripcion, self.usuario)
        self.usuario.refresh_from_db()
        self.assertEqual(self.usuario.saldo_fichas, 15)

    def test_inscripcion_reserva_cupo_y_evita_duplicados(self):
        torneo = self._crear_torneo(Torneo.ESTADO_ABIERTO)
        torneo.cupo_maximo = 1
        torneo.cuota = 10
        torneo.save(update_fields=['cupo_maximo', 'cuota'])
        equipo = self._crear_equipo(31)
        procesar_inscripcion(torneo, equipo)
        with self.assertRaisesMessage(ValueError, 'ya está inscrito'):
            procesar_inscripcion(torneo, equipo)
        otro = self._crear_equipo(32)
        with self.assertRaisesMessage(ValueError, 'no admite nuevas inscripciones'):
            procesar_inscripcion(torneo, otro)

    def test_evidencia_solo_es_descargable_por_capitanes(self):
        torneo = self._crear_torneo(Torneo.ESTADO_EN_CURSO)
        local = self._crear_equipo(40)
        visitante = self._crear_equipo(41, self.rival)
        partida = Partida.objects.create(
            torneo=torneo,
            equipo_local=local,
            equipo_visitante=visitante,
            evidencia_victoria=SimpleUploadedFile(
                'resultado.png',
                (
                    b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR'
                    b'\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06'
                    b'\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00'
                    b'\x0dIDAT\x08\xd7c\xf8\xcf\xc0\xf0\x1f\x00'
                    b'\x05\x00\x01\xff\x89\x99=\x1d\x00\x00\x00\x00IEND\xaeB`\x82'
                ),
                content_type='image/png',
            ),
        )
        url = reverse('descargar_evidencia', kwargs={'partida_id': partida.pk})

        self.client.force_login(self.rival)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['X-Content-Type-Options'], 'nosniff')
        self.assertIn('attachment', response['Content-Disposition'])

        outsider = get_user_model().objects.create_user(
            username='outsider',
            password='password-segura',
        )
        self.client.force_login(outsider)
        self.assertEqual(self.client.get(url).status_code, 403)

    def test_evidencia_rechaza_contenido_que_no_es_imagen(self):
        torneo = self._crear_torneo(Torneo.ESTADO_EN_CURSO)
        partida = Partida.objects.create(
            torneo=torneo,
            equipo_local=self._crear_equipo(42),
            equipo_visitante=self._crear_equipo(43, self.rival),
        )
        form = ResultadoPartidaForm(
            data={'ganador': str(partida.equipo_local_id)},
            files={
                'captura_evidencia': SimpleUploadedFile(
                    'payload.png',
                    b'not-an-image',
                    content_type='image/png',
                ),
            },
            partida=partida,
        )
        self.assertFalse(form.is_valid())
        self.assertIn('captura_evidencia', form.errors)

    def test_websocket_estado_solo_acepta_capitanes(self):
        torneo = self._crear_torneo(Torneo.ESTADO_EN_CURSO)
        local = self._crear_equipo(40)
        visitante = self._crear_equipo(41, self.rival)
        partida = Partida.objects.create(
            torneo=torneo,
            equipo_local=local,
            equipo_visitante=visitante,
            ronda='1',
            numero_partida=1,
        )

        outsider = get_user_model().objects.create_user(
            username='outsider',
            password='password-segura',
        )

        async def exercise_connections():
            communicator = WebsocketCommunicator(
                URLRouter(websocket_urlpatterns),
                f'/ws/torneos/partidas/{partida.pk}/',
            )
            communicator.scope['user'] = self.usuario
            connected, _ = await communicator.connect()
            self.assertTrue(connected)
            snapshot = await communicator.receive_json_from()
            self.assertEqual(snapshot['type'], 'match.snapshot')
            self.assertEqual(snapshot['match']['id'], partida.pk)
            await communicator.disconnect()

            denied = WebsocketCommunicator(
                URLRouter(websocket_urlpatterns),
                f'/ws/torneos/partidas/{partida.pk}/',
            )
            denied.scope['user'] = outsider
            connected, _ = await denied.connect()
            self.assertFalse(connected)

        async_to_sync(exercise_connections)()
