from django import forms

from retour_client.constantes import RetourClientConstantes
from retour_client.models import ReponseBug
from retour_client.adapters import is_user_admin


class ReponseBugForm(forms.ModelForm):
    class Meta:
        model = ReponseBug
        fields = ["reponse", "repondant", "temps_passe", "piece_jointe"]

    reponse = forms.CharField(
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 6}),
        required=True,
    )

    def __init__(self, *args, **kwargs):
        # récupère l’utilisateur sans casser l’API Django/admin
        current_user = kwargs.pop("current_user", None)
        super().__init__(*args, **kwargs)

        # valeur initiale selon le rôle
        if current_user and not getattr(current_user, "is_anonymous", False) and is_user_admin(current_user):
            self.fields["repondant"].initial = RetourClientConstantes.REVOLUCY
        else:
            self.fields["repondant"].initial = RetourClientConstantes.CLIENT

    def clean_reponse(self):
        reponse = self.cleaned_data.get("reponse", "")
        return reponse.replace("\n", "<br>")
