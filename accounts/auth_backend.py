from django.contrib.auth.backends import BaseBackend
from django.contrib.auth import get_user_model


class CedulaAuthBackend(BaseBackend):
    def authenticate(self, request, cedula=None, password=None, **kwargs):
        if cedula is None or password is None:
            return None
        UserModel = get_user_model()
        try:
            user = UserModel.objects.get(cedula=cedula)
        except UserModel.DoesNotExist:
            # Corre el hasher igual que si el usuario existiera, para que el
            # tiempo de respuesta no delate qué cédulas están registradas
            # (mismo mitigación que usa el ModelBackend por defecto de Django).
            UserModel().set_password(password)
            return None
        if user.check_password(password) and user.is_active:
            return user
        return None

    def get_user(self, user_id):
        UserModel = get_user_model()
        try:
            return UserModel.objects.get(pk=user_id)
        except UserModel.DoesNotExist:
            return None
