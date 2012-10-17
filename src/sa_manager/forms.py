from django.forms import Form, CharField, PasswordInput, ValidationError

class ChangePasswordForm (Form):
    new_password = CharField(widget=PasswordInput)
    confirm_password = CharField(widget=PasswordInput)
    
    def clean(self):
        cleaned_data = super(ChangePasswordForm, self).clean()
        p1 = cleaned_data.get("new_password")
        p2 = cleaned_data.get("confirm_password")

        if p1 != p2:
            raise ValidationError("Passwords do not match")

        return cleaned_data
