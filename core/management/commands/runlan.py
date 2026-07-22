import socket

from django.conf import settings
from django.contrib.staticfiles.management.commands.runserver import Command as RunserverCommand


class Command(RunserverCommand):
    help = 'Ejecuta el servidor en la red local y muestra las direcciones disponibles.'
    default_addr = '0.0.0.0'

    def handle(self, *args, **options):
        # runlan es exclusivamente un servidor de desarrollo. Debe entregar los
        # recursos estáticos aunque una variable global fuerce DEBUG=False.
        options['use_static_handler'] = True
        options['insecure_serving'] = True
        settings.ALLOWED_HOSTS = ['*']

        port = self.default_port
        addrport = options.get('addrport')
        if addrport and ':' in addrport:
            port = addrport.rsplit(':', 1)[-1]
        elif addrport and addrport.isdigit():
            port = addrport

        addresses = self._local_ipv4_addresses()
        self.stdout.write(self.style.SUCCESS('Servidor disponible en:'))
        self.stdout.write(f'  Este equipo: http://127.0.0.1:{port}/')
        for index, address in enumerate(addresses):
            label = 'Red local (recomendada)' if index == 0 else 'Otra interfaz'
            self.stdout.write(f'  {label}: http://{address}:{port}/')
        self.stdout.write('Los otros equipos deben estar conectados a la misma red.')
        super().handle(*args, **options)

    @staticmethod
    def _local_ipv4_addresses():
        addresses = set()
        preferred = None
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as connection:
                connection.connect(('8.8.8.8', 80))
                preferred = connection.getsockname()[0]
                if preferred and not preferred.startswith('127.'):
                    addresses.add(preferred)
        except OSError:
            pass
        try:
            for address in socket.gethostbyname_ex(socket.gethostname())[2]:
                if address and not address.startswith('127.'):
                    addresses.add(address)
        except socket.gaierror:
            pass
        return sorted(addresses, key=lambda address: (address != preferred, address))
