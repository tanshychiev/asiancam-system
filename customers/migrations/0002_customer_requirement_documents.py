import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('accounting', '0004_bulkimportlog_accountcustomer_accountitem'),
        ('customers', '0001_initial'),
        ('stock', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]
    operations = [
        migrations.CreateModel(
            name='SalesInvoice',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('document_type', models.CharField(choices=[('invoice','Invoice'),('sale_receipt','Sale Receipt')], default='invoice', max_length=30)),
                ('invoice_date', models.DateField(default=django.utils.timezone.localdate)),
                ('due_date', models.DateField(blank=True, null=True)),
                ('number', models.CharField(blank=True, max_length=80)), ('po_number', models.CharField(blank=True, max_length=80)),
                ('currency', models.CharField(default='USD', max_length=20)), ('exchange_rate', models.DecimalField(decimal_places=4, default=1, max_digits=14)),
                ('memo', models.TextField(blank=True)), ('subtotal', models.DecimalField(decimal_places=2, default=0, max_digits=14)),
                ('tax_total', models.DecimalField(decimal_places=2, default=0, max_digits=14)), ('discount_total', models.DecimalField(decimal_places=2, default=0, max_digits=14)),
                ('total_amount', models.DecimalField(decimal_places=2, default=0, max_digits=14)),
                ('status', models.CharField(choices=[('draft','Draft'),('posted','Posted'),('void','Void')], default='posted', max_length=20)),
                ('created_at', models.DateTimeField(auto_now_add=True)), ('updated_at', models.DateTimeField(auto_now=True)),
                ('accounts_receivable_account', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='sales_invoices_ar', to='accounting.chartofaccount')),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sales_invoices', to='core.company')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='sales_invoices', to='customers.customer')),
                ('deposit_account', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='sale_receipt_deposits', to='accounting.chartofaccount')),
                ('journal_entry', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='sales_invoice', to='accounting.journalentry')),
                ('salesperson', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='customers.salesperson')),
            ], options={'ordering':['-invoice_date','-id']}),
        migrations.CreateModel(
            name='CustomerReceipt', fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')), ('receipt_date', models.DateField(default=django.utils.timezone.localdate)),
                ('number', models.CharField(blank=True, max_length=80)), ('payment_method', models.CharField(blank=True, default='Cash', max_length=80)), ('currency', models.CharField(default='USD', max_length=20)),
                ('memo', models.TextField(blank=True)), ('total_amount', models.DecimalField(decimal_places=2, default=0, max_digits=14)), ('status', models.CharField(choices=[('draft','Draft'),('posted','Posted'),('void','Void')], default='posted', max_length=20)), ('created_at', models.DateTimeField(auto_now_add=True)),
                ('company', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='customer_receipts', to='core.company')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='receipts', to='customers.customer')),
                ('deposit_account', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='customer_receipt_deposits', to='accounting.chartofaccount')),
                ('journal_entry', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='customer_receipt', to='accounting.journalentry')),
            ], options={'ordering':['-receipt_date','-id']}),
        migrations.CreateModel(
            name='SalesInvoiceLine', fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')), ('description', models.CharField(blank=True, max_length=255)),
                ('qty', models.DecimalField(decimal_places=2, default=1, max_digits=14)), ('unit_name', models.CharField(blank=True, max_length=50)), ('unit_price', models.DecimalField(decimal_places=2, default=0, max_digits=14)),
                ('line_amount', models.DecimalField(decimal_places=2, default=0, max_digits=14)), ('discount_amount', models.DecimalField(decimal_places=2, default=0, max_digits=14)), ('tax_amount', models.DecimalField(decimal_places=2, default=0, max_digits=14)),
                ('invoice', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='lines', to='customers.salesinvoice')),
                ('item', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='sales_invoice_lines', to='stock.item')),
                ('revenue_account', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='sales_invoice_revenue_lines', to='accounting.chartofaccount')),
            ], options={'ordering':['id']}),
        migrations.CreateModel(
            name='CustomerReceiptAllocation', fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')), ('discount', models.DecimalField(decimal_places=2, default=0, max_digits=14)), ('amount', models.DecimalField(decimal_places=2, default=0, max_digits=14)), ('memo', models.CharField(blank=True, max_length=255)),
                ('invoice', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='receipt_allocations', to='customers.salesinvoice')), ('receipt', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='allocations', to='customers.customerreceipt')),
            ]),
        migrations.CreateModel(
            name='CustomerReceiptOtherCharge', fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')), ('memo', models.CharField(max_length=255)), ('amount', models.DecimalField(decimal_places=2, default=0, max_digits=14)),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='customer_receipt_other_charges', to='accounting.chartofaccount')), ('receipt', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='other_charges', to='customers.customerreceipt')),
            ]),
    ]
