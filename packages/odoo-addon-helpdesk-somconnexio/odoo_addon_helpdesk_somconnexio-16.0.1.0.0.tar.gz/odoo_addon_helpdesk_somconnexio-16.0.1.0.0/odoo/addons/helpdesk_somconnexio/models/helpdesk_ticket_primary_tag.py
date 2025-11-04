from odoo import models


class HelpdeskTicketPrimaryTag(models.Model):
    _name = "helpdesk.ticket.primary.tag"
    _inherit = "helpdesk.ticket.tag"
    _description = "Helpdesk Ticket Primary Tag"
    _order = "name"
