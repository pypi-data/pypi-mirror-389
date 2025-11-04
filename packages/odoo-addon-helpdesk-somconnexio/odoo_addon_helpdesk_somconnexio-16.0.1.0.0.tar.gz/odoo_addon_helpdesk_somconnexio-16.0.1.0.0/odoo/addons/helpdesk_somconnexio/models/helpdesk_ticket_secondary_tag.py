from odoo import models


class HelpdeskTicketSecondaryTag(models.Model):
    _name = "helpdesk.ticket.secondary.tag"
    _inherit = "helpdesk.ticket.tag"
    _description = "Helpdesk Ticket Secondary Tag"
    _order = "name"
