# Copyright 2025-SomItCoop SCCL(<https://gitlab.com/somitcoop>)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
{
    "name": "Odoo helpdesk Som Connexió Customizations",
    "version": "16.0.1.0.0",
    "summary": "Odoo Helpdesk customizations for Som Connexió",
    "author": "Som It Cooperatiu SCCL, Som Connexió SCCL",
    "website": "https://coopdevs.org",
    "license": "AGPL-3",
    "category": "Cooperative management",
    "depends": [
        "helpdesk_mgmt_rating",
        "helpdesk_ticket_mail_message",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/helpdesk_ticket_view.xml",
        "views/helpdesk_ticket_menu.xml",
        "wizards/mail_compose_message_view.xml",
    ],
    "external_dependencies": {},
    "application": False,
    "installable": True,
}
