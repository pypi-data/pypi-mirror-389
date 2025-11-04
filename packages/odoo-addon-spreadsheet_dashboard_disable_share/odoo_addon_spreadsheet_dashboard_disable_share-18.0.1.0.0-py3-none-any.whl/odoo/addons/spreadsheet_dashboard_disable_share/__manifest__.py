# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Spreadsheet Dashboard Disable Share",
    "summary": """
        Disable the share feature of dashboards.
    """,
    "author": "Mint System GmbH",
    "website": "https://github.com/Mint-system/",
    "category": "Repository",
    "version": "18.0.1.0.0",
    "license": "AGPL-3",
    "depends": ["spreadsheet_dashboard"],
    "installable": True,
    "application": False,
    "auto_install": False,
    "images": ["images/screen.png"],
    "assets": {
        "web.assets_backend": [
            "spreadsheet_dashboard_disable_share/static/src/components/dashboard_action.xml",
        ],
    },
}
