{
    "name": "Export Contract Data Form View",
    "version": "16.0.1.0.0",
    "summary": "Allows the export data action from a contract form view.",
    "author": "Coopdevs Treball SCCL, Som Connexió SCCL",
    "website": "https://coopdevs.org",
    "license": "AGPL-3",
    "category": "Accounting",
    "depends": ["contract"],
    "data": [
        "views/contract_views.xml",
    ],
    "demo": [],
    "assets": {
        "web.assets_backend": [
            "export_contract_data_form_view/static/src/js/contract_form_controller.js",
            "export_contract_data_form_view/static/src/js/contract_form_view.js",
        ],
    },
    "external_dependencies": {},
    "application": False,
    "installable": True,
}
