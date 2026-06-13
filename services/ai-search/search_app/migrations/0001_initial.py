from django.db import migrations, models
import uuid


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='ProductIndex',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('product_id', models.UUIDField(db_index=True, unique=True)),
                ('name', models.CharField(db_index=True, max_length=255)),
                ('name_normalized', models.CharField(db_index=True, max_length=255)),
                ('description', models.TextField(blank=True)),
                ('category', models.CharField(blank=True, db_index=True, max_length=255)),
                ('brand', models.CharField(blank=True, db_index=True, max_length=255)),
                ('price', models.DecimalField(decimal_places=0, max_digits=12)),
                ('keywords', models.TextField(blank=True)),
                ('search_vector', models.TextField(blank=True)),
                ('popularity_score', models.FloatField(default=0)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'product_index',
            },
        ),
        migrations.CreateModel(
            name='SearchHistory',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('query', models.CharField(db_index=True, max_length=255)),
                ('query_normalized', models.CharField(db_index=True, max_length=255)),
                ('search_count', models.IntegerField(default=1)),
                ('result_count', models.IntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'search_history',
                'ordering': ['-search_count'],
            },
        ),
        migrations.CreateModel(
            name='Synonym',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('word', models.CharField(db_index=True, max_length=100)),
                ('synonyms', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'synonyms',
            },
        ),
        migrations.AddIndex(
            model_name='productindex',
            index=models.Index(fields=['name_normalized'], name='product_ind_name_no_1be7a6_idx'),
        ),
        migrations.AddIndex(
            model_name='productindex',
            index=models.Index(fields=['category'], name='product_ind_categor_c0aff6_idx'),
        ),
        migrations.AddIndex(
            model_name='productindex',
            index=models.Index(fields=['brand'], name='product_ind_brand_dbb789_idx'),
        ),
        migrations.AddIndex(
            model_name='productindex',
            index=models.Index(fields=['-popularity_score'], name='product_ind_popular_2b0054_idx'),
        ),
    ]
