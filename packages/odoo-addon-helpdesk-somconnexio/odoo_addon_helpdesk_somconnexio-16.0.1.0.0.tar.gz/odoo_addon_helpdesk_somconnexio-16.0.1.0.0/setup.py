import setuptools

setuptools.setup(
    setup_requires=['setuptools-odoo'],
    odoo_addon={
        "depends_override": {
           "helpdesk_mgmt_rating": "odoo-addon-helpdesk-mgmt-rating==16.0.1.0.1",  # noqa E501
           "helpdesk_ticket_mail_message": "odoo-addon-helpdesk-ticket-mail-message==16.0.1.0.9.9",  # noqa E501
        }
    },
)
