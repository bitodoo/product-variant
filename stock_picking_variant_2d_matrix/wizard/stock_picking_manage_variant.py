# Copyright 2016-2018 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import odoo.addons.decimal_precision as dp
from odoo import api, models, fields


class StockPickinManageVariant(models.TransientModel):
    _name = 'stock.picking.manage.variant'

    product_tmpl_id = fields.Many2one(
        comodel_name='product.template', string="Template", required=True)
    variant_line_ids = fields.Many2many(
        comodel_name='stock.picking.variant.line', string="Variant Lines")

    def _get_product_variant(self, value_x, value_y):
        """Filter the corresponding product for provided values."""
        self.ensure_one()
        values = value_x
        if value_y:
            values += value_y
        return self.product_tmpl_id.product_variant_ids.filtered(
            lambda x: not (values - x.attribute_value_ids)
        )[:1]

    @api.onchange('product_tmpl_id')
    def _onchange_product_tmpl_id(self):
        self.variant_line_ids = [(6, 0, [])]
        template = self.product_tmpl_id
        context = self.env.context
        record = self.env[context['active_model']].browse(
            context['active_id'])
        if context['active_model'] == 'stock.move.line':
            stock_picking = record.picking_id
        else:
            stock_picking = record
        attr_lines = template.attribute_line_ids.filtered(
            lambda x: x.attribute_id.create_variant
        )
        num_attrs = len(attr_lines)
        if not template or not num_attrs or num_attrs > 2:
            return
        line_x = attr_lines[0]
        line_y = False if num_attrs == 1 else attr_lines[1]
        lines = []
        for value_x in line_x.value_ids:
            for value_y in line_y and line_y.value_ids or [False]:
                product = self._get_product_variant(value_x, value_y)
                if not product:
                    continue
                move_stock_line = stock_picking.move_line_ids.filtered(
                    lambda x: x.product_id == product
                )[:1]
                lines.append((0, 0, {
                    'value_x': value_x,
                    'value_y': value_y,
                    'qty_done': move_stock_line.qty_done,
                }))
        self.variant_line_ids = lines

    @api.multi
    def button_transfer_to_order(self):
        context = self.env.context
        record = self.env[context['active_model']].browse(context['active_id'])
        if context['active_model'] == 'stock.move.line':
            stock_picking = record.picking_id
        else:
            stock_picking = record
        StockMoveLine = self.env['stock.move.line']
        lines2unlink = StockMoveLine
        for line in self.variant_line_ids:
            product = self._get_product_variant(line.value_x, line.value_y)
            move_line = stock_picking.move_line_ids.filtered(
                lambda x: x.product_id == product
            )
            if move_line:
                if not line.qty_done:
                    # Done this way because there's a side effect removing here
                    lines2unlink |= move_line
                else:
                    move_line.qty_done = line.qty_done
            elif line.qty_done:
                vals = StockMoveLine.default_get(StockMoveLine._fields.keys())
                vals.update({
                    'product_id': product.id,
                    'product_uom': product.uom_id,
                    'qty_done': line.qty_done,
                    'picking_id': record.id,
                    'location_id': record.location_id.id,
                    'location_dest_id': record.location_dest_id.id,
                })
                move_line = StockMoveLine.new(vals)
                move_line.onchange_product_id()
                move_line_vals = move_line._convert_to_write(
                    move_line._cache)
                stock_picking.move_line_ids.browse().create(move_line_vals)
        lines2unlink.unlink()


class StockPinkingManageVariantLine(models.TransientModel):
    _name = 'stock.picking.variant.line'

    value_x = fields.Many2one(comodel_name='product.attribute.value')
    value_y = fields.Many2one(comodel_name='product.attribute.value')
    qty_done = fields.Float(
        string="Quantity", digits=dp.get_precision('Product UoS'))
