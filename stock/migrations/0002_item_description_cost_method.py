from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("stock", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="item",
            name="description",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="item",
            name="cost_method",
            field=models.CharField(
                choices=[("standard", "Standard Cost")],
                default="standard",
                help_text="Current AsianCam costing uses the item Cost Price as the standard cost.",
                max_length=20,
            ),
        ),
    ]
