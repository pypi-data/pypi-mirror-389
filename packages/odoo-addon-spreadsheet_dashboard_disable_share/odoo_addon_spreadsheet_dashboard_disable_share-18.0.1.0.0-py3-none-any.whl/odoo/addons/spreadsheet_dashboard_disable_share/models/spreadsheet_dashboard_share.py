from werkzeug.exceptions import Forbidden

from odoo import _, models


class SpreadsheetDashboardShare(models.Model):
    _name = "spreadsheet.dashboard.share"
    _inherit = "spreadsheet.dashboard.share"

    def _check_dashboard_access(self, access_token):
        self.ensure_one()
        raise Forbidden(_("Sharing a dashboard is not allowed."))
