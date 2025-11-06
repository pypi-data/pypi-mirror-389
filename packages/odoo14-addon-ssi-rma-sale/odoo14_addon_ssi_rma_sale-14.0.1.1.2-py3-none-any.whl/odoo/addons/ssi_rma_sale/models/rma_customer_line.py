# Copyright 2023 OpenSynergy Indonesia
# Copyright 2023 PT. Simetri Sinergi Indonesia
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class RMACustomerLine(models.Model):
    _name = "rma_customer_line"
    _inherit = [
        "rma_line_mixin",
        "rma_customer_line",
    ]

    sale_line_id = fields.Many2one(
        related="source_stock_move_id.sale_line_id",
        store=False,
    )

    def _get_receipt_procurement_data(self):
        _super = super(RMACustomerLine, self)
        result = _super._get_receipt_procurement_data()
        sale_line_id = self.sale_line_id and self.sale_line_id.id or False
        to_refund = sale_line_id and True or False
        result.update(
            {
                "sale_line_id": sale_line_id,
                "to_refund": to_refund,
            }
        )
        return result

    def _get_delivery_procurement_data(self):
        _super = super(RMACustomerLine, self)
        result = _super._get_delivery_procurement_data()
        sale_line_id = self.sale_line_id and self.sale_line_id.id or False
        source_stock_move_id = (
            self.source_stock_move_id and self.source_stock_move_id.id or False
        )
        to_refund = sale_line_id and True or False
        result.update(
            {
                "sale_line_id": sale_line_id,
                "origin_returned_move_id": source_stock_move_id,
                "to_refund": to_refund,
            }
        )
        return result

    def _prepare_refund_line(self, move):
        _super = super(RMACustomerLine, self)
        result = _super._prepare_refund_line(move)
        sale_line_id = self.sale_line_id
        if sale_line_id:
            result.update(
                {
                    "price_unit": sale_line_id.price_unit,
                    "tax_ids": [(6, 0, sale_line_id.tax_id.ids)],
                }
            )
        return result
