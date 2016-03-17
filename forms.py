from django import forms

class BasePayflowCallbackForm(forms.Form):
    """ Callback form used to validate the payflow response parameters."""
    PNREF = forms.CharField(required=True) 
    RESULT = forms.CharField(required=True)
