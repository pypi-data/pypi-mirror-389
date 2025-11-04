/** @odoo-module **/
import { FormController } from '@web/views/form/form_controller';
import { _t } from "@web/core/l10n/translation";
import { useService } from "@web/core/utils/hooks";
import { download } from "@web/core/network/download";
import { ExportDataDialog } from "@web/views/view_dialogs/export_data_dialog";

export class ContractFormController extends FormController {

    setup() {
        super.setup();
        this.dialogService = useService("dialog");
        this.rpc = useService("rpc");
    }

    /**
     * Add Export action to contract.contract form view
     * @returns {Array} menu items
     */
    getActionMenuItems() {
        const menuItems = super.getActionMenuItems();
        if (this.props.resModel === 'contract.contract') {
            if (!menuItems.other) {
                menuItems.other = [];
            }
            menuItems.other.push({
                key: "export",
                description: this.env._t("Export"),
                callback: () => this.onExportData(),
            });
        }
        return menuItems;
    }

    /**
     * Get default fields to export based on form view fields
     */
    get defaultExportList() {
        const fieldNames = ['phone_number', 'code', 'emails', 'date_start', 'date_end'];

        return fieldNames
            .map(fieldName => this.props.fields[fieldName])
            .filter(field => field && field.exportable !== false);
    }

    /**
     * Download export file
     */
    async downloadExport(fields, import_compat, format) {
        const ids = [this.model.root.resId];

        const exportedFields = fields.map((field) => ({
            name: field.name || field.id,
            label: field.label || field.string,
            store: field.store,
            type: field.field_type || field.type,
        }));

        if (import_compat) {
            exportedFields.unshift({ name: "id", label: this.env._t("External ID") });
        }

        await download({
            data: {
                data: JSON.stringify({
                    import_compat,
                    context: this.props.context,
                    domain: [],
                    fields: exportedFields,
                    groupby: [],
                    ids,
                    model: this.model.root.resModel,
                }),
            },
            url: `/web/export/${format}`,
        });
    }

    /**
     * Get fields available for export
     */
    async getExportedFields(model, import_compat, parentParams) {
        return await this.rpc("/web/export/get_fields", {
            ...parentParams,
            model,
            import_compat,
        });
    }

    /**
     * Opens the Export Dialog
     */
    async onExportData() {
        if (!this.model.root.resId) {
            this.env.services.notification.add(
                this.env._t("Please save the record before exporting."),
                { type: "warning" }
            );
            return;
        }

        const dialogProps = {
            context: this.props.context,
            defaultExportList: this.defaultExportList,
            download: this.downloadExport.bind(this),
            getExportedFields: this.getExportedFields.bind(this),
            root: this.model.root,
        };
        this.dialogService.add(ExportDataDialog, dialogProps);
    }
}
