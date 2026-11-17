from odoo import _, api, fields, models
from odoo.exceptions import AccessError, ValidationError
from odoo.tools import float_compare


class AvailabilityAlert(models.Model):
    _name = 'alsweed.availability.alert'
    _description = 'Stock Availability Reminder'
    _inherit = ['mail.activity.mixin']
    _rec_name = 'product_id'
    _order = 'create_date desc, id desc'
    _check_company_auto = True

    product_id = fields.Many2one(
        'product.product', required=True, check_company=True,
        domain=[('is_storable', '=', True)],
    )
    warehouse_id = fields.Many2one(
        'stock.warehouse', required=True, check_company=True,
    )
    quantity = fields.Float(string='Requested Quantity', default=1, required=True)
    uom_id = fields.Many2one(related='product_id.uom_id', string='Unit of Measure')
    user_id = fields.Many2one(
        'res.users', string='Requested By', required=True,
        default=lambda self: self.env.user, readonly=True,
    )
    company_id = fields.Many2one(
        'res.company', required=True, default=lambda self: self.env.company,
    )
    state = fields.Selection(
        [('waiting', 'Waiting'), ('notified', 'Notified'), ('cancelled', 'Cancelled')],
        default='waiting', required=True, readonly=True, copy=False,
    )
    last_checked_at = fields.Datetime(default=fields.Datetime.now, readonly=True, index=True)

    @api.model_create_multi
    def create(self, vals_list):
        values = []
        for vals in vals_list:
            vals = dict(vals, user_id=self.env.uid, state='waiting')
            company_id = vals.get('company_id', self.env.company.id)
            if company_id not in self.env.companies.ids:
                raise AccessError(_('Select one of your active companies.'))
            values.append(vals)
        return super().create(values)

    def write(self, vals):
        protected = {'product_id', 'warehouse_id', 'quantity', 'user_id', 'company_id', 'state', 'last_checked_at'}
        if protected.intersection(vals):
            raise AccessError(_('Cancel this reminder and create a new one to change it.'))
        return super().write(vals)

    @api.constrains('product_id', 'quantity', 'warehouse_id', 'company_id')
    def _check_request(self):
        for alert in self:
            if not alert.product_id.is_storable:
                raise ValidationError(_('Select a product that tracks inventory.'))
            if float_compare(alert.quantity, 0, precision_rounding=alert.product_id.uom_id.rounding) <= 0:
                raise ValidationError(_('Requested quantity must be greater than zero.'))
            if alert.warehouse_id.company_id != alert.company_id:
                raise ValidationError(_('The warehouse must belong to the selected company.'))

    def action_cancel(self):
        self.check_access_rights('write')
        self.check_access_rule('write')
        waiting = self.filtered(lambda alert: alert.state == 'waiting')
        return super(AvailabilityAlert, waiting).write({'state': 'cancelled'})

    def action_check_now(self):
        self._check_availability()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Notify Me'),
                'message': _('Availability checked. Open your activities for any new reminders.'),
                'type': 'info',
                'next': {'type': 'ir.actions.client', 'tag': 'reload'},
            },
        }

    def _check_availability(self):
        self.check_access_rights('write')
        self.check_access_rule('write')
        if not self:
            return
        # Lock only these reminders to avoid duplicate activities during concurrent checks.
        self.flush_recordset(['state'])
        self.env.cr.execute(
            "SELECT id FROM alsweed_availability_alert "
            "WHERE id IN %s AND state = 'waiting' FOR UPDATE SKIP LOCKED",
            [tuple(self.ids)],
        )
        alerts = self.browse([row[0] for row in self.env.cr.fetchall()])
        alerts.invalidate_recordset(['state'])
        for alert in alerts:
            super(AvailabilityAlert, alert).write({'last_checked_at': fields.Datetime.now()})
            if not alert.user_id.active or not alert.user_id.has_group('sales_team.group_sale_salesman'):
                continue
            if alert.company_id not in alert.user_id.company_ids:
                continue
            product = alert.product_id.with_company(alert.company_id).with_context(
                allowed_company_ids=[alert.company_id.id], warehouse=alert.warehouse_id.id,
            )
            if float_compare(product.free_qty, alert.quantity, precision_rounding=product.uom_id.rounding) < 0:
                continue
            alert.activity_schedule(
                'mail.mail_activity_data_todo',
                user_id=alert.user_id.id,
                summary=_('Product available'),
                note=_('The requested quantity is available in the selected warehouse. Stock is not reserved.'),
            )
            super(AvailabilityAlert, alert).write({'state': 'notified'})

    @api.model
    def _cron_check_availability(self):
        alerts = self.search([('state', '=', 'waiting')], order='last_checked_at, id', limit=200)
        alerts._check_availability()
