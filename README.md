## Settings 

django_payflow accepts a python dictionary for all settings 

The minimum settings needed are shown below:

```
DJANGO_PAYFLOW = {
    'PARTNER': 'partner', #This will most likely be 'PayPal'
    'MERCHANT_LOGIN': 'merchant',
    'USER': 'user', # This will most likely be the same as the MERCHANT_LOGIN setting
    'PASSWORD': 'password',
    'TEST_MODE': True,
}
```
