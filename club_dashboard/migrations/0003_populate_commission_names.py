# Data migration to populate new commission name fields

from django.db import migrations


def populate_commission_names(apps, schema_editor):
    Commission = apps.get_model('club_dashboard', 'Commission')
    
    for commission in Commission.objects.all():
        if commission.name and not commission.name_ar and not commission.name_en:
            commission.name_ar = commission.name
            commission.name_en = commission.name
            commission.save()


def reverse_populate_commission_names(apps, schema_editor):
    # Reverse migration - no action needed as we're just copying data
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('club_dashboard', '0002_add_commission_names'),
    ]

    operations = [
        migrations.RunPython(populate_commission_names, reverse_populate_commission_names),
    ]