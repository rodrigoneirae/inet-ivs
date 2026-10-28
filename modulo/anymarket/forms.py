from datetime import date

from django import forms


class FiltrosPedidosForm(forms.Form):
    desde = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    hasta = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    busqueda = forms.CharField(required=False, max_length=100, strip=True)
    canal = forms.CharField(required=False, max_length=100, strip=True)
    estado = forms.CharField(required=False, max_length=64, strip=True)

    def clean(self) -> dict:
        datos = super().clean()
        if datos.get('desde') and datos.get('hasta') and datos['desde'] > datos['hasta']:
            self.add_error('hasta', 'La fecha final debe ser igual o posterior a la fecha inicial.')
        if datos.get('hasta') == date.max:
            self.add_error('hasta', 'La fecha final no es válida.')
        return datos
