# Copyright 2016-2018 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    # This field is for avoiding conflicts with other modules adding the same
    # field. This field name for sure won't conflict
    product_tmpl_id_order_variant_mgmt = fields.Many2one(
        comodel_name="product.template", related="product_id.product_tmpl_id",
        readonly=True)
    product_attribute_value_ids = fields.Many2many(
        comodel_name='product.attribute.value',
        related="product_id.attribute_value_ids",
        readonly=True)
