from django import forms

from modulo.inventario.models import Asignacion


class BodegaForm(forms.Form):
    codigo = forms.CharField(max_length=30)
    nombre = forms.CharField(max_length=120)


class ZonaForm(forms.Form):
    bodega = forms.UUIDField()
    codigo = forms.CharField(max_length=30)
    nombre = forms.CharField(max_length=120)


class UbicacionForm(forms.Form):
    zona = forms.UUIDField()
    codigo = forms.CharField(max_length=40)


class InventarioForm(forms.Form):
    bodega = forms.CharField(max_length=30)
    nombre = forms.CharField(max_length=120)


class AsignacionForm(forms.Form):
    usuario = forms.CharField(max_length=150, required=False)
    dispositivo = forms.UUIDField(required=False)
    zona = forms.CharField(max_length=30, required=False)
    tipo = forms.ChoiceField(choices=Asignacion.Tipo.choices)

    def clean(self) -> dict[str, object]:
        data = super().clean()
        if bool(data.get('usuario')) == bool(data.get('dispositivo')):
            raise forms.ValidationError('Indica un usuario o un capturador.')
        return data


class TurnoForm(forms.Form):
    """Reconfiguración de la zona y el tipo de conteo de un turno."""

    zona = forms.CharField(max_length=30)
    tipo = forms.ChoiceField(choices=Asignacion.Tipo.choices, required=False)


class ConteoForm(forms.Form):
    evento = forms.UUIDField()
    zona = forms.CharField(max_length=30, required=False)
    ubicacion = forms.CharField(max_length=40, required=False)
    producto = forms.CharField(max_length=30)
    cantidad = forms.DecimalField(max_digits=15, decimal_places=3, min_value=0.001)


class PaginaForm(forms.Form):
    pagina = forms.IntegerField(min_value=1, required=False)
    tamano = forms.IntegerField(min_value=1, max_value=500, required=False)
