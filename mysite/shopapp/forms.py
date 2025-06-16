from django.contrib.auth.models import Group
from django import forms
from django.forms import ClearableFileInput

from .models import Product


class GroupForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ['name']


class MultipleClearableFileInput(ClearableFileInput):
    allow_multiple_selected = True

    def value_from_datadict(self, data, files, name):
        if not self.allow_multiple_selected:
            return super().value_from_datadict(data, files, name)
        else:
            return files.getlist(name)


class ProductForm(forms.ModelForm):
    images = forms.ImageField(
        required=False,
        widget=MultipleClearableFileInput(attrs={'multiple': True}),
        label='Product Images',
    )
    class Meta:
        model = Product
        fields = "name", "price", "description", "discount", "preview"

class CSVImportForm(forms.Form):
    csv_file = forms.FileField()


