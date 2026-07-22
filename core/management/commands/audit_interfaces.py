from collections import Counter
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.test import Client
from django.urls import Resolver404, get_resolver, resolve, reverse


class _IdCollector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.links = []

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if attributes.get("id"):
            self.ids.append(attributes["id"])
        if tag == "a" and attributes.get("href"):
            self.links.append(attributes["href"])


class Command(BaseCommand):
    help = "Audita las interfaces GET sin parámetros y no modifica datos de negocio."

    excluded_names = {"logout"}
    excluded_fragments = ("/admin/", "exportar", "descargar", "eliminar")
    accepted_statuses = {200, 301, 302, 403}
    suspicious_text = ("Ã", "Â", "â€", "�")

    def add_arguments(self, parser):
        parser.add_argument(
            "--user",
            help="Cédula o identificador del usuario con el que se realizará la auditoría.",
        )

    def _get_user(self, identifier):
        users = get_user_model().objects
        if identifier:
            lookup_field = get_user_model().USERNAME_FIELD
            try:
                return users.get(**{lookup_field: identifier})
            except get_user_model().DoesNotExist as exc:
                raise CommandError(f"No existe el usuario {identifier!r}.") from exc
        user = users.filter(is_superuser=True, is_active=True).first()
        if not user:
            raise CommandError("No existe un superusuario activo para ejecutar la auditoría.")
        return user

    def _routes(self):
        root = get_resolver()
        routes = set()
        for namespace, (_, resolver) in root.namespace_dict.items():
            if namespace == "admin":
                continue
            for name in resolver.reverse_dict.keys():
                if (
                    not isinstance(name, str)
                    or name in self.excluded_names
                    or name.startswith("api_")
                ):
                    continue
                full_name = f"{namespace}:{name}"
                try:
                    url = reverse(full_name)
                except Exception:
                    # La ruta necesita parámetros y se audita desde sus listados.
                    continue
                if any(fragment in url.lower() for fragment in self.excluded_fragments):
                    continue
                routes.add((full_name, url))
        return sorted(routes)

    def handle(self, *args, **options):
        client = Client(raise_request_exception=False)
        client.force_login(self._get_user(options.get("user")))
        errors = []
        warnings = []
        pending = list(self._routes())
        queued_names = {name for name, _ in pending}
        reviewed = 0

        try:
            while pending:
                name, url = pending.pop(0)
                reviewed += 1
                response = client.get(url, follow=False)
                if response.status_code not in self.accepted_statuses:
                    errors.append(f"{name} ({url}): HTTP {response.status_code}")
                    continue
                content_type = response.get("Content-Type", "")
                if response.status_code != 200 or "text/html" not in content_type:
                    continue
                html = response.content.decode(response.charset or "utf-8", errors="replace")
                found = [token for token in self.suspicious_text if token in html]
                if found:
                    warnings.append(f"{name} ({url}): posible texto mal codificado {found}")
                parser = _IdCollector()
                parser.feed(html)
                repeated = sorted(key for key, count in Counter(parser.ids).items() if count > 1)
                if repeated:
                    errors.append(f"{name} ({url}): id HTML repetido {repeated}")
                for href in parser.links:
                    parts = urlsplit(href)
                    if parts.scheme or parts.netloc or href.startswith(("#", "mailto:", "tel:")):
                        continue
                    linked_url = urljoin(url, parts.path or url)
                    if any(fragment in linked_url.lower() for fragment in self.excluded_fragments):
                        continue
                    try:
                        match = resolve(linked_url)
                    except Resolver404:
                        continue
                    linked_name = match.view_name or ""
                    short_name = linked_name.rsplit(":", 1)[-1]
                    if not linked_name or short_name in self.excluded_names or short_name.startswith("api_"):
                        continue
                    if linked_name in queued_names:
                        continue
                    queued_names.add(linked_name)
                    pending.append((linked_name, linked_url))
        finally:
            client.logout()

        for warning in warnings:
            self.stdout.write(self.style.WARNING(f"ADVERTENCIA: {warning}"))
        for error in errors:
            self.stdout.write(self.style.ERROR(f"ERROR: {error}"))

        summary = (
            f"Interfaces revisadas: {reviewed}; "
            f"errores: {len(errors)}; advertencias: {len(warnings)}."
        )
        if errors:
            raise CommandError(summary)
        self.stdout.write(self.style.SUCCESS(summary))
