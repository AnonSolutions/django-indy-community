# Generated by Django 2.1.7 on 2019-04-13 01:25

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('indy_community', '0006_auto_20190413_0001'),
    ]

    operations = [
        migrations.AlterField(
            model_name='agentconnection',
            name='partner_name',
            field=models.CharField(max_length=60),
        ),
        migrations.AlterField(
            model_name='agentconversation',
            name='connection',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='indy_community.AgentConnection'),
        ),
    ]
