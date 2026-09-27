from typing import Any

from django.db import transaction
from django.contrib.auth import get_user_model
from auditoria.services import record_audit_event
from .models import CompraTienda, ProductoTienda


class PurchaseError(ValueError):
    """Error de negocio al comprar un artículo."""


@transaction.atomic
def comprar_producto(usuario: Any, producto: ProductoTienda) -> CompraTienda:
    """Compra un producto y aplica su efecto cosmético al perfil."""
    if not usuario.is_authenticated:
        raise PurchaseError('Debes iniciar sesión para comprar.')
    usuario = get_user_model().objects.select_for_update().get(pk=usuario.pk)
    producto = ProductoTienda.objects.select_for_update().get(pk=producto.pk)
    if not producto.activo:
        raise PurchaseError('Este artículo ya no está disponible.')
    if CompraTienda.objects.filter(usuario=usuario, producto=producto).exists():
        raise PurchaseError('Ya tienes este artículo en tu inventario.')
    if usuario.saldo_fichas < producto.precio:
        raise PurchaseError('No tienes fichas suficientes.')
    saldo_anterior = usuario.saldo_fichas
    usuario.saldo_fichas -= producto.precio
    if producto.categoria == 'titulo' and producto.valor:
        usuario.titulo_equipado = producto.valor
    elif producto.categoria == 'fondo' and producto.valor:
        usuario.fondo_perfil = producto.valor
    elif producto.categoria == 'estado' and producto.valor:
        usuario.estado_equipado = producto.valor
    usuario.save(update_fields=['saldo_fichas', 'titulo_equipado', 'fondo_perfil', 'estado_equipado'])
    compra = CompraTienda.objects.create(usuario=usuario, producto=producto)
    record_audit_event(
        'balance_change',
        actor=usuario,
        target=usuario,
        metadata={
            'before': saldo_anterior,
            'after': usuario.saldo_fichas,
            'source': 'store_purchase',
            'purchase_id': compra.pk,
        },
    )
    return compra
