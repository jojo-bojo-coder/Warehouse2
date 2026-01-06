# Migration to make the name field optional

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('club_dashboard', '0003_populate_commission_names'),
    ]

    operations = [
        migrations.AlterField(
            model_name='commission',
            name='name',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='اسم العمولة'),
        ),
    ]