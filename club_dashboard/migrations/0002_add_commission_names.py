# Generated manually for adding commission names

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('club_dashboard', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='commission',
            name='name_ar',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='الاسم العربي'),
        ),
        migrations.AddField(
            model_name='commission',
            name='name_en',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='English Name'),
        ),
    ]