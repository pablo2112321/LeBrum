from django.contrib.auth import get_user_model
from django.test import TestCase

from equipos.models import Equipo

from .models import Inscripcion, Partida, RecompensaPartida, Torneo, Videojuego
from .services import generar_bracket, procesar_resultado


class CompetenciaEstabilidadTests(TestCase):
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

    def test_generar_bracket_rechaza_cantidad_no_potencia_de_dos(self):
        torneo = self._crear_torneo(Torneo.ESTADO_CERRADO)

        for indice in range(6):
            Inscripcion.objects.create(
                torneo=torneo,
                equipo=self._crear_equipo(indice),
                estado_pago=Inscripcion.ESTADO_PAGADO,
            )

        with self.assertRaises(ValueError):
            generar_bracket(torneo)

        self.assertEqual(Partida.objects.filter(torneo=torneo).count(), 0)

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

        with self.assertRaises(ValueError):
            procesar_resultado(partida, equipo_local)

        self.usuario.refresh_from_db()
        self.assertEqual(self.usuario.victorias, 1)
        self.assertEqual(self.usuario.puntos_xp, 100)
        self.assertEqual(
            RecompensaPartida.objects.filter(partida=partida).count(),
            2,
        )
