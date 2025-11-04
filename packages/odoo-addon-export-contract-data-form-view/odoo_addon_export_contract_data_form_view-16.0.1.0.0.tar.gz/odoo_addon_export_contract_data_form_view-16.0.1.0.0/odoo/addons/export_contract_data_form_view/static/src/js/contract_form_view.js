/** @odoo-module **/

import { registry } from "@web/core/registry";
import { formView } from "@web/views/form/form_view";
import { ContractFormController } from "./contract_form_controller";

export const contractFormView = {
    ...formView,
    Controller: ContractFormController,
};

registry.category("views").add("contract_form", contractFormView);
