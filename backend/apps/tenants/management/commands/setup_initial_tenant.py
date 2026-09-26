from django.core.management.base import BaseCommand
from django_tenants.utils import get_tenant_model, get_tenant_domain_model
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = "Sets up the initial public tenant, domain mapping, and superuser for cloud deployment."

    def handle(self, *args, **options):
        Client = get_tenant_model()
        Domain = get_tenant_domain_model()
        User = get_user_model()

        # 1. Ensure public tenant exists
        public_tenant = Client.objects.filter(schema_name="public").first()
        if not public_tenant:
            public_tenant = Client(
                schema_name="public",
                name="Edubest Platform",
                school_code="PUBLIC",
            )
            public_tenant.auto_create_schema = False
            public_tenant.save()
            self.stdout.write(self.style.SUCCESS("Successfully created public tenant."))
        else:
            self.stdout.write("Public tenant already exists.")

        # 2. Add domains for public tenant (Render domain, localhost, etc.)
        domains = [
            "edubest-api-pl2v.onrender.com",
            "localhost",
            "127.0.0.1",
        ]
        for idx, d in enumerate(domains):
            if not Domain.objects.filter(domain=d).exists():
                Domain.objects.create(
                    domain=d,
                    tenant=public_tenant,
                    is_primary=(idx == 0),
                )
                self.stdout.write(self.style.SUCCESS(f"Registered domain '{d}' for public tenant."))

        # 3. Create initial Live SuperAdmin account
        admin_email = "admin@edubest.gh"
        if not User.objects.filter(email=admin_email).exists():
            User.objects.create_superuser(
                email=admin_email,
                password="Password123!",
                first_name="Edubest",
                last_name="SuperAdmin",
                role="platform_admin",
            )
            self.stdout.write(self.style.SUCCESS(f"Created live superadmin: {admin_email} / Password123!"))
        else:
            self.stdout.write(f"Superadmin {admin_email} already exists.")
