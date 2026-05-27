import httpx
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Ping services to keep them alive on Render free tier'

    def handle(self, *args, **kwargs):
        urls = [
            'https://devboard-9mjs.onrender.com/api/docs/',
            'https://devboard-fastapi.onrender.com/health',
        ]
        for url in urls:
            try:
                response = httpx.get(url, timeout=10)
                self.stdout.write(f'✅ {url} → {response.status_code}')
            except Exception as e:
                self.stdout.write(f'❌ {url} → {e}')