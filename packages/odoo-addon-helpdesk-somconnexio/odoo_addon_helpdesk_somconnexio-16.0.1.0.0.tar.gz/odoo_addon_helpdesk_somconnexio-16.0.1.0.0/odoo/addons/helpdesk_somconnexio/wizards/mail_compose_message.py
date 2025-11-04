from datetime import timedelta
from odoo import models, fields
from odoo.tools.translate import _
from odoo.exceptions import UserError


DELAY_SEND_MINUTES = 5


class MailComposeMessage(models.TransientModel):
    _inherit = "mail.compose.message"

    def save_note(self):
        self.ensure_one()

        if self.model != "helpdesk.ticket":
            raise UserError(_("This action is only available for helpdesk tickets."))

        self.create(
            {
                "composition_mode": "comment",
                "model": self.model,
                "res_id": self.res_id,
                "body": self.body,
            }
        )._action_send_mail()

        return {"type": "ir.actions.act_window_close"}

    def get_mail_values(self, res_ids):
        """
        Override to set a default scheduled date if none is provided.
        Som Connexio requirement: if no scheduled date is set,
        delay sending the email by a few minutes.
        """
        results = super(MailComposeMessage, self).get_mail_values(res_ids)

        if self.model == "helpdesk.ticket" and not self.scheduled_date:
            for res_id in results.keys():
                delay_send = fields.Datetime.now() + timedelta(
                    minutes=DELAY_SEND_MINUTES
                )
                if not results[res_id].get("scheduled_date"):
                    results[res_id]["scheduled_date"] = delay_send

        return results
