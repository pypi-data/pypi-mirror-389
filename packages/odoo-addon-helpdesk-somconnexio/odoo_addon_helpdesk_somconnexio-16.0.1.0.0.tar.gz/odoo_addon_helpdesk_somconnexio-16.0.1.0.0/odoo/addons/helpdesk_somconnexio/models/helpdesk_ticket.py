from odoo import models, fields


class HelpdeskTicket(models.Model):
    _inherit = "helpdesk.ticket"

    primary_tag_ids = fields.Many2many(
        comodel_name="helpdesk.ticket.primary.tag",
        string="Primary Tags",
        help="Primary tags for the helpdesk ticket.",
    )
    secondary_tag_ids = fields.Many2many(
        comodel_name="helpdesk.ticket.secondary.tag",
        string="Secondary Tags",
        help="Secondary tags for the helpdesk ticket.",
    )
