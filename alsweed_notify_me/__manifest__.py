{
    'name': 'Notify Me When Available',
    'version': '18.0.1.0.0',
    'summary': 'Personal stock availability reminders',
    'category': 'Inventory/Inventory',
    'author': 'Al Sweed Trading Company',
    'license': 'LGPL-3',
    'depends': ['stock', 'mail', 'sales_team'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/availability_alert_views.xml',
        'data/ir_cron_data.xml',
    ],
    'installable': True,
    'application': True,
}
